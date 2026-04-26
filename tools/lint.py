from pathlib import Path
import ast
import py_compile
import sys
import tokenize


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    ROOT / "src" / "ocr_app" / "__init__.py",
    ROOT / "src" / "ocr_app" / "main.py",
    ROOT / "src" / "ocr_app" / "ocr_service.py",
    ROOT / "src" / "ocr_app" / "ocr_utils.py",
    ROOT / "src" / "ocr_app" / "templates" / "index.html",
    ROOT / "src" / "requirements.txt",
    ROOT / "tools" / "Makefile",
    ROOT / "tools" / "lint.py",
    ROOT / "tools" / "smoke_test.py",
    ROOT / "tests" / "test_ocr_utils.py",
    ROOT / "README.md",
    ROOT / "Dockerfile",
    ROOT / "docker-compose.yml",
)

PYTHON_SOURCES = (
    ROOT / "src" / "ocr_app" / "__init__.py",
    ROOT / "src" / "ocr_app" / "main.py",
    ROOT / "src" / "ocr_app" / "ocr_service.py",
    ROOT / "src" / "ocr_app" / "ocr_utils.py",
    ROOT / "tools" / "lint.py",
    ROOT / "tools" / "smoke_test.py",
    ROOT / "tests" / "test_ocr_utils.py",
)


def assert_no_comments_or_docstrings(path: Path, errors: list[str]) -> None:
    with path.open(encoding="utf-8") as source:
        for token in tokenize.generate_tokens(source.readline):
            if token.type == tokenize.COMMENT:
                errors.append(f"{path.relative_to(ROOT)}: comments are not allowed")
                break

    tree = ast.parse(path.read_text(encoding="utf-8"))
    if ast.get_docstring(tree) is not None:
        errors.append(f"{path.relative_to(ROOT)}: module docstrings are not allowed")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node) is not None:
                errors.append(f"{path.relative_to(ROOT)}: docstrings are not allowed")
                break


def main() -> int:
    errors: list[str] = []

    visible_root_files = {
        path.name
        for path in ROOT.iterdir()
        if path.is_file() and not path.name.startswith(".")
    }
    if visible_root_files != {"Dockerfile", "docker-compose.yml"}:
        errors.append("Root directory must contain only Dockerfile and docker-compose.yml as visible files")

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")

    for path in PYTHON_SOURCES:
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as error:
            errors.append(f"{path.relative_to(ROOT)}: {error.msg}")
            continue
        assert_no_comments_or_docstrings(path, errors)

    html_path = ROOT / "src" / "ocr_app" / "templates" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    required_snippets = (
        'method="post"',
        'enctype="multipart/form-data"',
        'type="file"',
        'type="number"',
        "<select id=\"sort\" name=\"sort\">",
        "{{ result_image }}",
        "{% if words %}",
        "{% if error_title %}",
    )

    for snippet in required_snippets:
        if snippet not in html:
            errors.append(f"Template is missing snippet: {snippet}")

    if "<!--" in html:
        errors.append("Template comments are not allowed")

    if errors:
        print("Lint failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Lint passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
