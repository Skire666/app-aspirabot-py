"""epi_stats — Measure code quality with Ruff-style output.

Rules:
  - EPI025: Functions with >25 effective lines (code only, no blanks/comments/docstring)
  - SCR250: Functions with high complexity/effective-lines score
  - EPI301: Files must end with '# EOF'
  - EPI302: Files must have import section marker before imports

Config is read from `furripe-config.json` in the current directory.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final, Protocol, TypedDict, cast

import mccabe  # You'll need: pip install mccabe

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #


TOOL_NAME: Final[str] = "furripe"
TOOL_VERSION: Final[str] = "1.0"

CONFIG_FILE: Final[Path] = Path("furripe-config.json")
FILE_ENCODING: Final[str] = "utf-8"

EXIT_CONFIG_INVALID: Final[int] = 2
EXIT_PATH_MISSING: Final[int] = 3

FIXABLE_RULES: Final[frozenset[str]] = frozenset({"EPI301", "EPI302"})

C_THRESHOLD_LINES: Final[int] = 26
C_MAX_SCORE: Final[int] = 250
C_MIN_COMPLEXITY: Final[int] = 6
C_MIN_LINES: Final[int] = 14


class RuleConfig(TypedDict, total=False):
    """Configuration for a single rule."""

    enabled: bool
    threshold_lines: int
    max_score: int
    min_complexity: int
    min_lines: int


class RulesConfig(TypedDict, total=False):
    """Mapping of rule codes to their configuration."""

    EPI025: RuleConfig
    SCR250: RuleConfig
    EPI301: RuleConfig
    EPI302: RuleConfig


class Config(TypedDict):
    """User configuration loaded from the JSON config file."""

    path: str
    rules: RulesConfig
    exclude_dirs: list[str]
    output_format: str


class Error(TypedDict):
    """A single error finding."""

    code: str
    message: str
    filename: str
    line: int
    column: int
    name: str | None


class RuleStatistics(TypedDict):
    """Statistics entry for a rule code."""

    code: str
    count: int
    name: str


class StatisticsPayload(TypedDict):
    """Statistics payload emitted in JSON mode."""

    tool: str
    version: str
    total_errors: int
    statistics: list[RuleStatistics]


# Default configuration
DEFAULT_CONFIG: Final[Config] = {
    "path": "./__src__/",
    "rules": {
        "EPI025": {"enabled": True, "threshold_lines": C_THRESHOLD_LINES},
        "SCR250": {
            "enabled": True,
            "max_score": C_MAX_SCORE,
            "min_complexity": C_MIN_COMPLEXITY,
            "min_lines": C_MIN_LINES,
        },
        "EPI301": {"enabled": True},
        "EPI302": {"enabled": True},
    },
    "exclude_dirs": ["__pycache__", ".venv", ".git", "node_modules", "tests"],
    "output_format": "text",  # text or json
}


class InvalidConfigJsonError(SystemExit):
    """Raised when the config file is not valid JSON."""

    def __init__(self, config_path: Path, exc: json.JSONDecodeError) -> None:
        """Initialize the error with a formatted message."""
        super().__init__(f"Error: {config_path} is not valid JSON ({exc}).")


class MissingConfigPathError(SystemExit):
    """Raised when the config file is missing the required path key."""

    def __init__(self, config_path: Path) -> None:
        """Initialize the error with a formatted message."""
        super().__init__(f"Error: key 'path' is required in {config_path}.")


class RootPathMissingError(SystemExit):
    """Raised when the configured root path does not exist."""

    def __init__(self, root: Path) -> None:
        """Initialize the error with a formatted message."""
        super().__init__(f"Error: path '{root}' does not exist.")


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def _write_default_config() -> None:
    """Write the default configuration file to disk."""
    CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding=FILE_ENCODING)


def _read_config_payload() -> object:
    """Read the raw config payload, creating defaults if needed."""
    if not CONFIG_FILE.exists():
        _write_default_config()

    try:
        return json.loads(CONFIG_FILE.read_text(encoding=FILE_ENCODING))
    except json.JSONDecodeError as exc:
        raise InvalidConfigJsonError(CONFIG_FILE, exc) from exc


def _validate_config_payload(raw: object) -> dict[str, object]:
    """Validate the raw payload and ensure required keys."""
    if not isinstance(raw, dict):
        raise MissingConfigPathError(CONFIG_FILE)
    if "path" not in raw or not raw["path"]:
        raise MissingConfigPathError(CONFIG_FILE)
    return cast(dict[str, object], raw)


def _apply_config_defaults(raw: dict[str, object]) -> Config:
    """Apply default values to the config payload."""
    config = cast(Config, raw)
    if "rules" not in config:
        config["rules"] = DEFAULT_CONFIG["rules"]
    if "exclude_dirs" not in config:
        config["exclude_dirs"] = DEFAULT_CONFIG["exclude_dirs"]
    if "output_format" not in config:
        config["output_format"] = DEFAULT_CONFIG["output_format"]
    return config


def load_config() -> Config:
    """Load the JSON config, creating a default file if missing."""
    raw = _read_config_payload()
    validated = _validate_config_payload(raw)
    return _apply_config_defaults(validated)


def parse_cli() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="EPI code quality checker (Ruff-style).")
    parser.add_argument("--statistics", action="store_true", help="Show statistics summary per rule.")
    parser.add_argument("--fix", action="store_true", help="Fix EPI301/EPI302 where possible.")
    parser.add_argument("--output-format", choices=["text", "json"], help="Output format (overrides config file).")
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# AST analysis helpers
# --------------------------------------------------------------------------- #
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
FunctionCheck = Callable[[FunctionNode], Error | None]


class _McCabeGraph(Protocol):
    """Protocol for McCabe path graphs."""

    def complexity(self) -> int:
        """Return the cyclomatic complexity for the graph."""
        ...


class _ComplexityVisitor(Protocol):
    """Structural typing for the McCabe visitor."""

    graphs: dict[str, _McCabeGraph]

    def preorder(self, tree: ast.AST, visitor: _ComplexityVisitor) -> None:
        """Walk the AST and collect graphs."""
        ...


def _make_mccabe_visitor() -> _ComplexityVisitor:
    """Create a McCabe visitor without relying on typed stubs."""
    return cast(_ComplexityVisitor, cast(Any, mccabe).PathGraphingAstVisitor())


def _is_docstring(node: ast.stmt) -> bool:
    """Return True if `node` is a bare string expression (a docstring)."""
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def effective_lines(func: FunctionNode, source_lines: list[str]) -> int:
    """Return the count of real code lines in `func` (no blanks, comments, docstring)."""
    body: list[ast.stmt] = func.body
    if body and _is_docstring(body[0]):
        body = body[1:]
    if not body:
        return 0

    line_numbers: set[int] = set()
    for stmt in body:
        start: int = stmt.lineno
        end: int = getattr(stmt, "end_lineno", start) or start
        line_numbers.update(range(start, end + 1))

    count: int = 0
    for lineno in line_numbers:
        line: str = source_lines[lineno - 1].strip()
        if not line or line.startswith("#"):
            continue
        count += 1
    return count


def calculate_complexity(func: FunctionNode) -> int:
    """Calculate McCabe cyclomatic complexity for a function."""
    visitor = _make_mccabe_visitor()
    visitor.preorder(func, visitor)
    graph = next(iter(visitor.graphs.values()), None)
    if graph is None:
        return 0
    return int(graph.complexity())


def get_function_source_lines(source_lines: list[str], func: FunctionNode) -> list[str]:
    """Extract the source lines of a function."""
    start_line = func.lineno - 1
    end_line = getattr(func, "end_lineno", func.lineno) or func.lineno
    return source_lines[start_line:end_line]


# --------------------------------------------------------------------------- #
# Rule implementations
# --------------------------------------------------------------------------- #
def check_epi025(
    func: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str], filename: str, threshold: int
) -> Error | None:
    """EPI025: Function with > threshold effective lines."""
    eff_lines = effective_lines(func, source_lines)
    if eff_lines > threshold:
        return {
            "code": "EPI025",
            "message": f"Function has {eff_lines} effective lines (max: {threshold})",
            "filename": filename,
            "line": func.lineno,
            "column": func.col_offset + 1,
            "name": func.name,
        }

    return None


def check_scr250(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
    filename: str,
    max_score: int,
    min_complexity: int,
    min_lines: int,
) -> Error | None:
    """SCR250: High complexity/effective-lines score."""
    eff_lines = effective_lines(func, source_lines)
    complexity = calculate_complexity(func)

    if eff_lines >= min_lines and complexity >= min_complexity:
        score: int = complexity * eff_lines
        if score > max_score:
            str_fm = f"Score complexity too high (mccabe * lines) : {complexity} * {eff_lines} = {score} > {max_score}"
            return {
                "code": "SCR250",
                "message": str_fm,
                "filename": filename,
                "line": func.lineno,
                "column": func.col_offset + 1,
                "name": func.name,
            }
    return None


def check_epi301(source: str, filename: str) -> Error | None:
    """EPI301: File must end with '# EOF'."""
    lines = source.splitlines()
    if not lines:
        return None

    last_line = lines[-1].strip()
    if last_line != "# EOF":
        return {
            "code": "EPI301",
            "message": "File must end with '# EOF'",
            "filename": filename,
            "line": len(lines),
            "column": 1,
            "name": None,
        }
    return None


IMPORT_MARKER_LINES: Final[tuple[str, str, str]] = (
    "# -----------------------------------------------------------------------------",
    "# Imports",
    "# -----------------------------------------------------------------------------",
)


def _import_marker_text() -> str:
    """Return the import section marker as a single string."""
    return "\n".join(IMPORT_MARKER_LINES)


def _find_first_real_import_line(source: str) -> int | None:
    """Return the 0-based index of the first module-level import, using AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return node.lineno - 1
    return None


def _has_import_marker(lines: list[str], first_import_line: int) -> bool:
    """Return True if the import marker is already present before the first import."""
    return _import_marker_text() in "\n".join(lines[:first_import_line])


def check_epi302(source: str, filename: str) -> Error | None:
    """EPI302: File must have import section marker before imports."""
    lines = source.splitlines()
    first_import_line = _find_first_real_import_line(source)

    if first_import_line is None:
        return None  # No imports found, skip check

    if not _has_import_marker(lines, first_import_line):
        return {
            "code": "EPI302",
            "message": "Missing import section marker before imports",
            "filename": filename,
            "line": first_import_line + 1,
            "column": 1,
            "name": None,
        }
    return None


# --------------------------------------------------------------------------- #
# Rule configuration helpers
# --------------------------------------------------------------------------- #
_DEFAULT_RULE: Final[RuleConfig] = {"enabled": True}


def _get_rule(rules: RulesConfig, key: str) -> RuleConfig:
    """Return the rule config for a key, or a safe default."""
    rule = rules.get(key)
    return rule if rule is not None else _DEFAULT_RULE


def _rule_enabled(rules: RulesConfig, key: str) -> bool:
    """Return True if the rule is enabled or missing."""
    rule = _get_rule(rules, key)
    return bool(rule.get("enabled", True))


def _get_rule_int(rule: RuleConfig, key: str, default: int) -> int:
    """Return an integer rule value with a safe fallback."""
    value = rule.get(key, default)
    return value if isinstance(value, int) else default


def _get_rule_float(rule: RuleConfig, key: str, default: float) -> float:
    """Return a float rule value with a safe fallback."""
    value = rule.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    return default


# --------------------------------------------------------------------------- #
# File analysis
# --------------------------------------------------------------------------- #
def _parse_source(path: Path) -> tuple[str, list[str], ast.Module] | None:
    """Load and parse a Python file, returning None on failure."""
    try:
        source = path.read_text(encoding=FILE_ENCODING)
        tree = ast.parse(source, filename=str(path))
    except UnicodeDecodeError, OSError, SyntaxError:
        return None
    return source, source.splitlines(), tree


def _apply_fix_epi301(lines: list[str]) -> list[str]:
    """Ensure the file ends with the EPI301 marker."""
    if not lines:
        return lines
    trimmed = list(lines)
    while trimmed and not trimmed[-1].strip():
        trimmed.pop()
    if not trimmed:
        return lines
    if trimmed[-1] != "# EOF":
        trimmed.append("")
        trimmed.append("")
        trimmed.append("# EOF")
    return trimmed


def _apply_fix_epi302(lines: list[str]) -> list[str]:
    """Ensure the import marker exists before the first import."""
    first_import_line = _find_first_real_import_line("\n".join(lines))
    if first_import_line is None:
        return lines
    if _has_import_marker(lines, first_import_line):
        return lines

    before = lines[:first_import_line]
    after = lines[first_import_line:]

    if before and before[-1].strip():
        before = [*before, ""]
    if after and after[0].strip():
        after = ["", *after]

    return [*before, *IMPORT_MARKER_LINES, *after]


def _fix_file(path: Path, rules: RulesConfig) -> bool:
    """Apply EPI301/EPI302 fixes when possible; return True if changed."""
    try:
        source = path.read_text(encoding=FILE_ENCODING)
    except OSError, UnicodeDecodeError:
        return False

    lines = source.splitlines()
    updated = lines
    if _rule_enabled(rules, "EPI302"):
        updated = _apply_fix_epi302(updated)
    if _rule_enabled(rules, "EPI301"):
        updated = _apply_fix_epi301(updated)
    if updated == lines:
        return False
    path.write_text("\n".join(updated) + "\n", encoding=FILE_ENCODING)
    return True


def _apply_fixes(files: list[Path], config: Config) -> int:
    """Apply auto-fixes and return the number of modified files."""
    rules = config["rules"]
    modified = 0
    for path in files:
        if _fix_file(path, rules):
            modified += 1
    return modified


def _collect_file_errors(source: str, filename: str, rules: RulesConfig) -> list[Error]:
    """Collect file-level rule violations."""
    errors: list[Error] = []
    if _rule_enabled(rules, "EPI301"):
        error = check_epi301(source, filename)
        if error is not None:
            errors.append(error)
    if _rule_enabled(rules, "EPI302"):
        error = check_epi302(source, filename)
        if error is not None:
            errors.append(error)
    return errors


def _build_function_checks(rules: RulesConfig, source_lines: list[str], filename: str) -> list[FunctionCheck]:
    """Build the list of function-level checks to run."""
    checks: list[FunctionCheck] = []

    if _rule_enabled(rules, "EPI025"):
        rule_025 = _get_rule(rules, "EPI025")
        threshold = _get_rule_int(rule_025, "threshold_lines", C_THRESHOLD_LINES)

        def _check_025(func: FunctionNode) -> Error | None:
            return check_epi025(func, source_lines, filename, threshold)

        checks.append(_check_025)

    if _rule_enabled(rules, "SCR250"):
        rule_250 = _get_rule(rules, "SCR250")
        max_score = _get_rule_int(rule_250, "max_score", C_MAX_SCORE)
        min_complexity = _get_rule_int(rule_250, "min_complexity", C_MIN_COMPLEXITY)
        min_lines = _get_rule_int(rule_250, "min_lines", C_MIN_LINES)

        def _check_250(func: FunctionNode) -> Error | None:
            return check_scr250(func, source_lines, filename, max_score, min_complexity, min_lines)

        checks.append(_check_250)

    return checks


def _collect_function_errors(
    tree: ast.Module, source_lines: list[str], filename: str, rules: RulesConfig
) -> list[Error]:
    """Collect function-level rule violations."""
    checks = _build_function_checks(rules, source_lines, filename)
    if not checks:
        return []

    errors: list[Error] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for check in checks:
            error = check(node)
            if error is not None:
                errors.append(error)
    return errors


def analyze_file(path: Path, config: Config) -> list[Error]:
    """Parse `path` and return all rule violations."""
    parsed = _parse_source(path)
    if parsed is None:
        return []

    source, source_lines, tree = parsed
    rules = config["rules"]
    errors = _collect_file_errors(source, str(path), rules)
    errors.extend(_collect_function_errors(tree, source_lines, str(path), rules))
    return errors


def iter_python_files(root: Path, exclude_dirs: list[str]) -> list[Path]:
    """List all `.py` files under `root`, skipping any path crossing an excluded dir."""
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    excluded: set[str] = set(exclude_dirs)
    return [p for p in root.rglob("*.py") if not (excluded & set(p.parts)) and p.suffix == ".py"]


# --------------------------------------------------------------------------- #
# Output formatting (Ruff-style)
# --------------------------------------------------------------------------- #
def ruff_style_message(error: Error, source_lines: list[str] | None = None) -> str:
    """Format error in Ruff's style."""
    # error[C901]: `function_name` is too complex (9 > 7)
    return f"error[{error['code']}]: {error['message']}"


def _group_errors_by_file(errors: list[Error]) -> dict[str, list[Error]]:
    """Group errors by filename for multi-line formatting."""
    errors_by_file: dict[str, list[Error]] = {}
    for error in errors:
        errors_by_file.setdefault(error["filename"], []).append(error)
    return errors_by_file


def _build_context_lines(error: Error, source_lines: list[str], num_width: int) -> list[str]:
    """Build source context lines for a single error."""
    if not source_lines or error["line"] > len(source_lines):
        return []

    start_line = max(0, error["line"] - 3)
    end_line = min(error["line"] + 2, len(source_lines))
    context_lines: list[str] = []
    sep = f"{' ' * (num_width + 1)}|"

    for line_num in range(start_line, end_line):
        display_num = line_num + 1
        line_content = source_lines[line_num].rstrip()
        if display_num == error["line"]:
            context_lines.append(f"{display_num:{num_width}} | {line_content}")
            col_offset = error["column"] - 1
            span = len(error["name"]) if error["name"] else 1
            context_lines.append(f"{sep} {' ' * col_offset}{'^' * span}")
        else:
            context_lines.append(f"{display_num:{num_width}} | {line_content}")

    return context_lines


def _format_error_block(error: Error, source_lines: list[str]) -> list[str]:
    """Format a single error block with optional source context."""
    end_line = min(error["line"] + 2, len(source_lines)) if source_lines else error["line"]
    num_width = len(str(end_line))
    sep = f"{' ' * (num_width + 1)}|"

    lines = [
        f"error[{error['code']}]: {error['message']}",
        f"{' ' * num_width}--> {error['filename']}:{error['line']}:{error['column']}",
        sep,
    ]

    context_lines = _build_context_lines(error, source_lines, num_width)
    if context_lines:
        lines.extend(context_lines)
        lines.append(sep)

    help_msg = get_rule_help(error["code"])
    if help_msg:
        lines.append(f"help: {help_msg}")

    return lines


def _format_file_errors(filename: str, file_errors: list[Error], source_cache: dict[str, list[str]]) -> list[str]:
    """Format the errors for a single file."""
    output_lines: list[str] = []
    source_lines = source_cache.get(filename, [])

    for error in file_errors:
        output_lines.extend(_format_error_block(error, source_lines))
        output_lines.append("")

    return output_lines


def _format_summary(errors: list[Error]) -> list[str]:
    """Return the trailing summary lines."""
    if not errors:
        return []
    fixable_count = sum(1 for e in errors if e["code"] in FIXABLE_RULES)
    lines = [f"Found {len(errors)} error(s)."]
    if fixable_count:
        lines.append(f"[*] {fixable_count} fixable with the `--fix` option.")
    else:
        lines.append("No fixes available.")
    return lines


def format_ruff_output(errors: list[Error], source_cache: dict[str, list[str]]) -> str:
    """Format errors in Ruff's multi-line style with context."""
    if not errors:
        return "All checks passed!"

    output_lines: list[str] = []
    errors_by_file = _group_errors_by_file(errors)

    for filename, file_errors in errors_by_file.items():
        output_lines.extend(_format_file_errors(filename, file_errors, source_cache))

    output_lines.extend(_format_summary(errors))
    return "\n".join(output_lines)


def emit_findings_text(errors: list[Error], source_cache: dict[str, list[str]]) -> None:
    """Print errors in Ruff-style format."""
    output = format_ruff_output(errors, source_cache)
    if output:
        print(output)


def emit_findings_json(errors: list[Error]) -> None:
    """Print errors as JSON."""
    json.dump(errors, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# --------------------------------------------------------------------------- #
# Statistics mode (like ruff --statistics)
# --------------------------------------------------------------------------- #
def emit_statistics_text(errors: list[Error]) -> None:
    """Print statistics summary per rule (like ruff --statistics)."""
    from collections import Counter

    rule_counts = Counter(error["code"] for error in errors)
    sorted_rules = sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))

    if not sorted_rules:
        print("All checks passed!")
        return

    max_code_width = max(len(code) for code, _ in sorted_rules)
    max_count_width = max(len(str(count)) for _, count in sorted_rules)
    show_markers = any(code in FIXABLE_RULES for code, _ in sorted_rules)

    for code, count in sorted_rules:
        rule_name = get_rule_name(code)
        if show_markers:
            marker = "[*]" if code in FIXABLE_RULES else "[ ]"
            print(f"{count:>{max_count_width}}      {code:<{max_code_width + 1}}{marker}  {rule_name}")
        else:
            print(f"{count:>{max_count_width}}      {code:<{max_code_width + 1}}{rule_name}")

    total = len(errors)
    noun = "error" if total == 1 else "errors"
    print(f"Found {total} {noun}.")

    fixable_count = sum(1 for e in errors if e["code"] in FIXABLE_RULES)
    if fixable_count:
        print(f"[*] {fixable_count} fixable with the `--fix` option.")
    else:
        print("No fixes available")


def emit_statistics_json(errors: list[Error]) -> None:
    """Print statistics as JSON."""
    from collections import Counter

    rule_counts = Counter(error["code"] for error in errors)

    statistics: list[RuleStatistics] = [
        {"code": code, "count": count, "name": get_rule_name(code)}
        for code, count in sorted(rule_counts.items(), key=lambda x: (-x[1], x[0]))
    ]

    payload: StatisticsPayload = {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "total_errors": len(errors),
        "statistics": statistics,
    }

    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def get_rule_name(code: str) -> str:
    """Get the human-readable name for a rule code."""
    rule_names = {
        "EPI025": "function-too-long",
        "SCR250": "high-cyclomatic-complexity",
        "EPI301": "missing-eof-marker",
        "EPI302": "missing-import-marker",
    }
    return rule_names.get(code, "unknown-rule")


def get_rule_help(code: str) -> str:
    """Get the help message for a rule code."""
    rule_help = {
        "EPI025": "Consider splitting this function into smaller, focused functions",
        "SCR250": "Consider simplifying the logic or extracting helper functions to reduce branching",
        "EPI301": "Add `# EOF` at the end of the file",
        "EPI302": "Add the import section marker before the first import statement",
    }
    return rule_help.get(code, "")


def _resolve_output_format(args: argparse.Namespace, config: Config) -> str:
    """Return the output format, honoring CLI overrides."""
    return args.output_format or config["output_format"]


def _cache_source_lines(path: Path, source_cache: dict[str, list[str]]) -> None:
    """Cache source lines for context rendering."""
    with contextlib.suppress(OSError, UnicodeDecodeError):
        source_cache[str(path)] = path.read_text(encoding=FILE_ENCODING).splitlines()


def _collect_errors(files: list[Path], config: Config) -> tuple[list[Error], dict[str, list[str]]]:
    """Analyze files and return errors with their source cache."""
    all_errors: list[Error] = []
    source_cache: dict[str, list[str]] = {}

    for path in files:
        errors = analyze_file(path, config)
        if errors:
            all_errors.extend(errors)
            _cache_source_lines(path, source_cache)

    return all_errors, source_cache


def _emit_output(
    args: argparse.Namespace, output_format: str, errors: list[Error], source_cache: dict[str, list[str]]
) -> None:
    """Emit results based on statistics flag and output format."""
    if args.statistics:
        if output_format == "json":
            emit_statistics_json(errors)
        else:
            emit_statistics_text(errors)
        return

    if output_format == "json":
        emit_findings_json(errors)
    else:
        emit_findings_text(errors, source_cache)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    """Entry point: load config, scan files, dispatch output mode."""
    config: Config = load_config()
    args: argparse.Namespace = parse_cli()

    # Override output format if provided via CLI
    output_format = _resolve_output_format(args, config)

    root: Path = Path(config["path"])
    if not root.exists():
        raise RootPathMissingError(root)

    files: list[Path] = iter_python_files(root, config["exclude_dirs"])
    if args.fix:
        _apply_fixes(files, config)
    all_errors, source_cache = _collect_errors(files, config)
    _emit_output(args, output_format, all_errors, source_cache)

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
