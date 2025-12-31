"""AST-based linter for analyzing Python code naming conventions."""

import ast
from pathlib import Path
from typing import Dict, List

from naming.validators import StrictnessLevel, ValidationError, validate_name


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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pylint: disable=invalid-name
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

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # pylint: disable=invalid-name
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

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # pylint: disable=invalid-name
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
) -> Dict[str, List[ValidationError]]:
    """
    Lint all Python files in a directory.

    Args:
        directory_path: Path to the directory to lint
        max_level: Maximum strictness level to apply
        recursive: Whether to search recursively
        config: Configuration dictionary

    Returns:
        Dictionary with file paths as keys and lists of errors as values
    """
    if config is None:
        config = {}

    all_errors = {}

    if recursive:
        python_files = directory_path.rglob("*.py")
    else:
        python_files = directory_path.glob("*.py")

    for file_path in python_files:
        file_errors = lint_file(file_path, max_level, config)
        if file_errors[str(file_path)]:
            all_errors.update(file_errors)

    return all_errors
