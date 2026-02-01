"""AST-based linter for analyzing Python code naming conventions."""

import ast
from pathlib import Path
from typing import Dict, List, Tuple

import pathspec

from yina.validators import StrictnessLevel, ValidationError, validate_name


class NamingLinter(ast.NodeVisitor):
    """AST visitor that collects and validates variable and class names."""

    def __init__(self, max_level: StrictnessLevel, config: dict = None):
        """
        Initialize the linter with a maximum strictness level.

        Args:
            max_level: The maximum strictness level to apply
            config: Configuration dictionary
        """
        self.max_level = max_level
        self.config = config or {}
        self.errors: List[ValidationError] = []
        self.validated_names: set = set()

    def _validate_function_parameters(self, args: ast.arguments) -> None:
        """
        Validate function parameters (shared between regular and async functions).

        Args:
            args: Function arguments node from AST
        """
        for arg in args.args:
            param_name = arg.arg
            # Skip "self" (instance methods) and "cls" (class methods)
            if param_name not in self.validated_names and param_name not in (
                "self",
                "cls",
            ):
                self.validated_names.add(param_name)
                errors = validate_name(
                    param_name,
                    self.max_level,
                    is_class=False,
                    config=self.config,
                    line_number=arg.lineno,
                    column_number=arg.col_offset,
                )
                self.errors.extend(errors)

    def visit_Name(self, node: ast.Name) -> None:  # pylint: disable=invalid-name
        """Visit variable name nodes (method name required by ast.NodeVisitor)."""
        if isinstance(node.ctx, ast.Store):
            # Only validate when the name is being assigned/stored
            name = node.id
            # Skip private and dunder names (starting with _)
            if name not in self.validated_names and not name.startswith("_"):
                self.validated_names.add(name)
                errors = validate_name(
                    name,
                    self.max_level,
                    is_class=False,
                    config=self.config,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                )
                self.errors.extend(errors)
        self.generic_visit(node)

    # pylint: disable=invalid-name
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes (method name required by ast.NodeVisitor)."""
        name = node.name
        if name not in self.validated_names and not name.startswith("_"):
            self.validated_names.add(name)
            errors = validate_name(
                name,
                self.max_level,
                is_class=False,
                config=self.config,
                line_number=node.lineno,
                column_number=node.col_offset,
            )
            self.errors.extend(errors)

        # Validate function parameters
        self._validate_function_parameters(node.args)

        self.generic_visit(node)

    # pylint: disable=invalid-name
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes (method name required by ast.NodeVisitor)."""
        name = node.name
        if name not in self.validated_names and not name.startswith("_"):
            self.validated_names.add(name)
            errors = validate_name(
                name,
                self.max_level,
                is_class=False,
                config=self.config,
                line_number=node.lineno,
                column_number=node.col_offset,
            )
            self.errors.extend(errors)

        # Validate function parameters
        self._validate_function_parameters(node.args)

        self.generic_visit(node)

    # pylint: disable=invalid-name
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes (method name required by ast.NodeVisitor)."""
        name = node.name
        if name not in self.validated_names:
            self.validated_names.add(name)
            errors = validate_name(
                name,
                self.max_level,
                is_class=True,
                config=self.config,
                line_number=node.lineno,
                column_number=node.col_offset,
            )
            self.errors.extend(errors)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        """Visit argument nodes (function parameters)."""
        # Already handled in visit_FunctionDef
        self.generic_visit(node)


def lint_file(
    file_path: Path, max_level: StrictnessLevel, config: dict = None
) -> Dict[str, List[ValidationError]]:
    """
    Lint a Python file for naming convention violations.

    Args:
        file_path: Path to the Python file to lint
        max_level: Maximum strictness level to apply
        config: Configuration dictionary

    Returns:
        Dictionary with file path as key and list of errors as value
    """
    try:
        source_code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code, filename=str(file_path))

        linter = NamingLinter(max_level, config)
        linter.visit(tree)

        return {str(file_path): linter.errors}

    except SyntaxError as error:
        return {
            str(file_path): [
                ValidationError("", f"Syntax error: {error}", StrictnessLevel.LEVEL_ONE)
            ]
        }
    except (OSError, UnicodeDecodeError) as error:
        return {
            str(file_path): [
                ValidationError(
                    "", f"Error reading file: {error}", StrictnessLevel.LEVEL_ONE
                )
            ]
        }


def lint_directory(
    directory_path: Path,
    max_level: StrictnessLevel,
    recursive: bool = True,
    config: dict = None,
) -> Tuple[Dict[str, List[ValidationError]], bool]:
    """
    Lint all Python files in a directory.

    Args:
        directory_path: Path to the directory to lint
        max_level: Maximum strictness level to apply
        recursive: Whether to search recursively
        config: Configuration dictionary

    Returns:
        Tuple containing:
        - Dictionary with file paths as keys and lists of errors as values
        - Boolean indicating if .gitignore was used
    """
    if config is None:
        config = {}

    all_errors = {}
    gitignore_used = False
    spec = None

    # Load .gitignore if present
    gitignore_path = directory_path / ".gitignore"
    if gitignore_path.exists() and gitignore_path.is_file():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as gitignore_file:
                spec = pathspec.PathSpec.from_lines("gitwildmatch", gitignore_file)
            gitignore_used = True
        except (OSError, UnicodeDecodeError):
            # If we can't read .gitignore, just ignore it
            pass

    # Get exclude patterns from config
    exclude_globs = config.get("linter", {}).get("exclude_globs", [])

    if recursive:
        python_files = directory_path.rglob("*.py")
    else:
        python_files = directory_path.glob("*.py")

    for file_path in python_files:
        # Check .gitignore first
        if spec:
            try:
                relative_path = file_path.relative_to(directory_path)
                if spec.match_file(str(relative_path)):
                    continue
            except ValueError:
                # Should not happen as we are iterating files in directory_path
                pass

        # Check if file should be excluded
        should_exclude = False
        for pattern in exclude_globs:
            # Check if the file path or any of its parents match the pattern
            # Convert to relative path from directory_path for proper matching
            try:
                relative_path = file_path.relative_to(directory_path)
                # Check if any part of the path matches the exclusion pattern
                if relative_path.match(pattern):
                    should_exclude = True
                    break
                # Also check with /** appended to match files inside excluded directories
                if relative_path.match(f"{pattern}/**"):
                    should_exclude = True
                    break
                # Check each parent directory
                for parent in relative_path.parents:
                    if parent.match(pattern) or str(parent) == pattern.replace(
                        "**/", ""
                    ).replace("/**", ""):
                        should_exclude = True
                        break
                if should_exclude:
                    break
            except ValueError:
                # File is not relative to directory_path, skip it
                continue

        if should_exclude:
            continue

        file_errors = lint_file(file_path, max_level, config)
        if file_errors[str(file_path)]:
            all_errors.update(file_errors)

    return all_errors, gitignore_used
