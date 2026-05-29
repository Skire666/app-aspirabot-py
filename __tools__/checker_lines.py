"""loc_stats — Measure effective lines of code per function, Ruff-style.

Two modes:
  - Normal mode      : list each function above the threshold,
                       one finding per line (`path:line:col: CODE message`).
  - --statistics mode: aggregate (summary + bucket distribution).

Config is read from `loc_stats.json` in the current directory.
A default file is created on first run.
"""

from __future__ import annotations

import argparse
import ast
import json
import statistics
import sys
from pathlib import Path
from typing import Final, Literal, NotRequired, TypedDict, cast

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
TOOL_NAME: Final[str] = "loc_stats"
TOOL_VERSION: Final[str] = "1.0"
RULE_CODE: Final[str] = "LOC001"
RULE_NAME: Final[str] = "function-too-long"

CONFIG_FILE: Final[Path] = Path("loc_stats.json")
FILE_ENCODING: Final[str] = "utf-8"

OUTPUT_TEXT: Final[str] = "text"
OUTPUT_JSON: Final[str] = "json"
OUTPUT_FORMATS: Final[tuple[str, ...]] = (OUTPUT_TEXT, OUTPUT_JSON)

KIND_FUNCTION: Final[str] = "function"
KIND_ASYNC_FUNCTION: Final[str] = "async_function"

MIN_SAMPLES_FOR_P90: Final[int] = 10
P90_DECILE_INDEX: Final[int] = 10

EXIT_CONFIG_INVALID: Final[int] = 2
EXIT_PATH_MISSING: Final[int] = 3

DEFAULT_CONFIG: Final[dict] = {
    "path": "./__src__/",
    "buckets": [20, 25, 30],
    "ranking_threshold": 25,
    "output_format": OUTPUT_TEXT,
    "exclude_dirs": ["__pycache__", ".venv", ".git", "node_modules"],
}

OutputFormat = Literal["text", "json"]
FunctionKind = Literal["function", "async_function"]


# --------------------------------------------------------------------------- #
# Typed structures
# --------------------------------------------------------------------------- #
class Config(TypedDict):
    """User configuration loaded from the JSON config file."""

    path: str
    buckets: list[int]
    ranking_threshold: int
    output_format: OutputFormat
    exclude_dirs: list[str]


class Finding(TypedDict):
    """A single function measurement."""

    path: str
    line: int
    column: int
    name: str
    lines: int
    kind: FunctionKind


class Bucket(TypedDict):
    """One range of the function-size distribution."""

    range: str
    min: int
    max: int | None
    count: int
    percentage: float


class Summary(TypedDict):
    """Aggregate statistics over all analyzed functions."""

    total_functions: int
    mean: float
    median: float
    max: int
    min: int
    p90: NotRequired[int]


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def load_config() -> Config:
    """Load the JSON config, creating a default file if missing."""
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding=FILE_ENCODING)
        print(f"Config file created: {CONFIG_FILE}", file=sys.stderr)

    try:
        raw = json.loads(CONFIG_FILE.read_text(encoding=FILE_ENCODING))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: {CONFIG_FILE} is not valid JSON ({exc}).") from exc

    if not raw.get("path"):
        raise SystemExit(f"Error: key 'path' is required in {CONFIG_FILE}.")
    if raw.get("output_format", OUTPUT_TEXT) not in OUTPUT_FORMATS:
        raise SystemExit(f"Error: 'output_format' must be one of {OUTPUT_FORMATS}.")
    return cast(Config, raw)


def parse_cli(config: Config) -> argparse.Namespace:
    """Parse command-line arguments, using the config as defaults."""
    parser = argparse.ArgumentParser(description="Measure Python function sizes (Ruff-style).")
    parser.add_argument(
        "--statistics", action="store_true", help="Show aggregated distribution instead of per-function findings."
    )
    parser.add_argument(
        "--output-format",
        choices=OUTPUT_FORMATS,
        default=config.get("output_format", OUTPUT_TEXT),
        help="Output format (defaults to value in config file).",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# AST analysis
# --------------------------------------------------------------------------- #
def _is_docstring(node: ast.stmt) -> bool:
    """Return True if `node` is a bare string expression (a docstring)."""
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def effective_lines(func: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str]) -> int:
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


def analyze_file(path: Path) -> list[Finding]:
    """Parse `path` and return one Finding per function/method (recursively)."""
    try:
        source: str = path.read_text(encoding=FILE_ENCODING)
        tree: ast.Module = ast.parse(source, filename=str(path))
    except UnicodeDecodeError, OSError, SyntaxError:
        return []

    source_lines: list[str] = source.splitlines()
    results: list[Finding] = []

    def walk(node: ast.AST, prefix: str) -> None:
        """Recursively collect findings, qualifying names by class/function prefix."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname: str = f"{prefix}{child.name}"
                kind: FunctionKind = KIND_ASYNC_FUNCTION if isinstance(child, ast.AsyncFunctionDef) else KIND_FUNCTION
                results.append(
                    Finding(
                        path=str(path),
                        line=child.lineno,
                        column=child.col_offset + 1,
                        name=qualname,
                        lines=effective_lines(child, source_lines),
                        kind=kind,
                    )
                )
                walk(child, f"{qualname}.")
            elif isinstance(child, ast.ClassDef):
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)

    walk(tree, "")
    return results


def iter_python_files(root: Path, exclude_dirs: list[str]) -> list[Path]:
    """List all `.py` files under `root`, skipping any path crossing an excluded dir."""
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    excluded: set[str] = set(exclude_dirs)
    return [p for p in root.rglob("*.py") if not (excluded & set(p.parts))]


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def build_summary(counts: list[int]) -> Summary:
    """Compute mean / median / min / max (and P90 when enough samples)."""
    summary: Summary = {
        "total_functions": len(counts),
        "mean": round(statistics.mean(counts), 2),
        "median": round(statistics.median(counts), 2),
        "max": max(counts),
        "min": min(counts),
    }
    if len(counts) >= MIN_SAMPLES_FOR_P90:
        summary["p90"] = round(statistics.quantiles(counts, n=P90_DECILE_INDEX)[-1])
    return summary


def build_distribution(counts: list[int], buckets: list[int]) -> list[Bucket]:
    """Bucket `counts` into the given thresholds plus one trailing open-ended range."""
    total: int = len(counts)
    dist: list[Bucket] = []
    previous: int = 0
    for threshold in sorted(buckets):
        n: int = sum(1 for c in counts if previous < c <= threshold)
        dist.append(
            Bucket(
                range=f"{previous + 1}-{threshold}",
                min=previous + 1,
                max=threshold,
                count=n,
                percentage=round(100 * n / total, 2),
            )
        )
        previous = threshold
    n = sum(1 for c in counts if c > previous)
    dist.append(
        Bucket(range=f">={previous + 1}", min=previous + 1, max=None, count=n, percentage=round(100 * n / total, 2))
    )
    return dist


# --------------------------------------------------------------------------- #
# Output: normal mode (per-function findings)
# --------------------------------------------------------------------------- #
def emit_findings_text(findings: list[Finding], threshold: int, total: int) -> None:
    """Print one finding per line in `path:line:col: CODE message` format."""
    for f in findings:
        location: str = f"{f['path']}:{f['line']}:{f['column']}"
        msg: str = f"Function `{f['name']}` has {f['lines']} effective lines (threshold: {threshold})"
        print(f"{location}: {RULE_CODE} {msg}")

    n: int = len(findings)
    if n == 0:
        print(f"All checks passed! ({total} functions analyzed)")
    else:
        suffix: str = "s" if n != 1 else ""
        print(f"Found {n} function{suffix} exceeding {threshold} lines (out of {total} analyzed).")


def emit_findings_json(findings: list[Finding], threshold: int) -> None:
    """Print findings as a flat JSON array, mirroring `ruff check --output-format json`."""
    payload: list[dict] = [
        {
            "code": RULE_CODE,
            "name": RULE_NAME,
            "message": f"Function `{f['name']}` has {f['lines']} effective lines",
            "filename": f["path"],
            "location": {"row": f["line"], "column": f["column"]},
            "name_qualified": f["name"],
            "lines": f["lines"],
            "threshold": threshold,
            "kind": f["kind"],
        }
        for f in findings
    ]
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# --------------------------------------------------------------------------- #
# Output: --statistics mode (aggregate)
# --------------------------------------------------------------------------- #
def emit_statistics_text(summary: Summary, distribution: list[Bucket]) -> None:
    """Print the aggregated summary and bucket distribution as human-readable text."""
    print(f"\nFunctions analyzed : {summary['total_functions']}")
    print(f"Mean   : {summary['mean']} lines")
    print(f"Median : {summary['median']} lines")
    if "p90" in summary:
        print(f"P90    : {summary['p90']} lines")
    print(f"Max    : {summary['max']} lines\n")

    print("Distribution :")
    for b in distribution:
        label: str = f"≥ {b['min']:<3}" if b["max"] is None else f"{b['min']:>3}–{b['max']:<3}"
        print(f"  {label} lines : {b['count']:>5} ({b['percentage']:5.1f} %)")


def emit_statistics_json(summary: Summary, distribution: list[Bucket], config: Config) -> None:
    """Print the aggregated stats as a single JSON object including config metadata."""
    payload: dict = {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "config": {
            "path": config["path"],
            "buckets": config["buckets"],
            "ranking_threshold": config.get("ranking_threshold", 0),
        },
        "summary": summary,
        "distribution": distribution,
    }
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    """Entry point: load config, scan files, dispatch output mode."""
    config: Config = load_config()
    args: argparse.Namespace = parse_cli(config)

    root: Path = Path(config["path"])
    if not root.exists():
        raise SystemExit(f"Error: path '{root}' does not exist.")

    files: list[Path] = iter_python_files(root, config.get("exclude_dirs", []))
    all_functions: list[Finding] = []
    for path in files:
        all_functions.extend(analyze_file(path))

    if not all_functions:
        print("No functions found.", file=sys.stderr)
        return 0

    counts: list[int] = [f["lines"] for f in all_functions]
    threshold: int = config.get("ranking_threshold", 0)
    output_format: OutputFormat = args.output_format

    if args.statistics:
        summary: Summary = build_summary(counts)
        distribution: list[Bucket] = build_distribution(counts, config["buckets"])
        if output_format == OUTPUT_JSON:
            emit_statistics_json(summary, distribution, config)
        else:
            emit_statistics_text(summary, distribution)
    else:
        findings: list[Finding] = sorted(
            (f for f in all_functions if f["lines"] > threshold), key=lambda f: -f["lines"]
        )
        if output_format == OUTPUT_JSON:
            emit_findings_json(findings, threshold)
        else:
            emit_findings_text(findings, threshold, len(all_functions))

    return 0


if __name__ == "__main__":
    sys.exit(main())
