import ast
from pathlib import Path


def count_code_lines(node, src_lines):
    """Count non-blank, non-docstring, non-comment lines in a function body."""
    start = (
        node.body[0].end_lineno
        if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)
        else node.body[0].lineno - 1
    )
    # Skip the docstring
    body_nodes = node.body
    if body_nodes and isinstance(body_nodes[0], ast.Expr) and isinstance(body_nodes[0].value, ast.Constant):
        body_nodes = body_nodes[1:]
    if not body_nodes:
        return 0
    first_line = body_nodes[0].lineno
    last_line = node.end_lineno
    count = 0
    for i in range(first_line - 1, last_line):
        line = src_lines[i].strip()
        if line and not line.startswith("#"):
            count += 1
    return count


files = list(Path("__src__").rglob("*.py"))
violations = []
for f in sorted(files):
    try:
        src = f.read_text(encoding="utf-8")
        tree = ast.parse(src)
        lines = src.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                n = count_code_lines(node, lines)
                if n > 25:
                    violations.append((n, str(f), node.name, node.lineno))
    except Exception:
        pass

for n, f, name, line in sorted(violations, reverse=True):
    print(f"{n:3d}  {f}:{line}  {name}")
