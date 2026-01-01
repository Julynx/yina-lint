"""Command-line interface for the yina linter."""

import argparse
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init

from yina.config import init_config, load_config
from yina.linter import lint_directory, lint_file
from yina.validators import StrictnessLevel


def format_errors(errors_dict: dict) -> str:
    """
    Format errors dictionary into a human-readable string.

    Args:
        errors_dict: Dictionary mapping file paths to lists of ValidationError objects

    Returns:
        Formatted string with error details
    """
    if not errors_dict:
        return f"{Fore.GREEN}✓ No naming violations found!{Style.RESET_ALL}"

    output_lines = []
    total_errors = 0

    for file_path, errors in errors_dict.items():
        if errors:
            output_lines.append(f"\n{'=' * 80}")
            output_lines.append(f"File: {Fore.MAGENTA}{file_path}{Style.RESET_ALL}")
            output_lines.append("=" * 80)

            for error in errors:
                output_lines.append(f"  {error}")
                total_errors += 1

    output_lines.append(f"\n{'=' * 80}")
    output_lines.append(
        f"Total violations found: {Fore.RED}{total_errors}{Style.RESET_ALL}"
    )
    output_lines.append("=" * 80)

    return "\n".join(output_lines)


def handle_init_command(_args):
    """Handle the init command to create a config file."""
    try:
        config_path = init_config()
        print(f"✓ Created configuration file at: {config_path}")
        sys.exit(0)
    except FileExistsError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except (OSError, FileNotFoundError) as error:
        print(f"Error creating config file: {error}", file=sys.stderr)
        sys.exit(2)


def handle_lint_command(args):
    """Handle the main linting command."""
    target_path = Path(args.path)

    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Load configuration
    try:
        config = load_config()
        default_level = config.get("linter", {}).get("default_level", 5)
    except FileNotFoundError as error:
        print(f"Error: {error}", file=sys.stderr)
        print("Run 'yina init' to create a configuration file.", file=sys.stderr)
        sys.exit(1)

    # Use level from args or config
    strictness_level = StrictnessLevel(args.level if args.level else default_level)

    print("=" * 2 + " yina lint " + "=" * 67)

    print(
        f"-- Running with strictness level: {Fore.CYAN}{strictness_level.value}{Style.RESET_ALL}"
    )

    if args.verbose:
        print(f"Linting: {target_path}")
        print()

    try:
        if target_path.is_file():
            if target_path.suffix != ".py":
                print(
                    f"Error: File '{target_path}' is not a Python file.",
                    file=sys.stderr,
                )
                sys.exit(1)
            errors_dict = lint_file(target_path, strictness_level, config)
        else:
            errors_dict = lint_directory(
                target_path, strictness_level, recursive=True, config=config
            )

        output = format_errors(errors_dict)
        print(output)

        # Exit with error code if violations found
        if errors_dict and any(errors_dict.values()):
            sys.exit(1)
        else:
            sys.exit(0)

    except (OSError, UnicodeDecodeError) as error:
        print(f"Error during linting: {error}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(2)


def main():
    """Main entry point for the CLI."""
    # Initialize colorama for cross-platform color support
    colorama_init(autoreset=False)

    parser = argparse.ArgumentParser(
        description="Lint Python code for naming convention violations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Create a .yina.toml configuration file in the current directory"
    )
    init_parser.set_defaults(func=handle_init_command)

    # Lint command (default)
    lint_parser = subparsers.add_parser(
        "lint",
        help="Lint Python files for naming violations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Strictness Levels:
  1 - Length and charset (min 3 chars, alphanumeric + underscore)
  2 - Naming conventions (snake_case, CamelCase, CONSTANTS)
  3 - Max length, repetition, segment length
  4 - Pronounceability (consonants, vowels)
  5 - Non-vagueness (no vague words, no numbers)

Examples:
  yina lint myfile.py --level 3
  yina lint src/ --level 5
  yina lint . --level 2
        """,
    )

    lint_parser.add_argument(
        "path",
        type=str,
        help="Path to Python file or directory to lint",
    )

    lint_parser.add_argument(
        "-l",
        "--level",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help="Strictness level (1-5, uses config default if not specified)",
    )

    lint_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively lint all Python files in directory (default for directories)",
    )

    lint_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )

    lint_parser.set_defaults(func=handle_lint_command)

    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
