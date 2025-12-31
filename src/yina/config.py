"""Configuration loading and management for the yina linter."""

import shutil
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# Configuration file names
CONFIG_FILENAME = ".yina.toml"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "yina.toml"


def load_config(working_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from working directory or use default.

    Args:
        working_dir: Directory to search for config file (defaults to current directory)

    Returns:
        Dictionary containing configuration values
    """
    if working_dir is None:
        working_dir = Path.cwd()

    # Check for config in working directory
    local_config_path = working_dir / CONFIG_FILENAME

    if local_config_path.exists():
        return load_config_file(local_config_path)

    # Use default config
    if DEFAULT_CONFIG_PATH.exists():
        return load_config_file(DEFAULT_CONFIG_PATH)

    raise FileNotFoundError(
        "No configuration file found. Run 'yina init' to create one."
    )


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a TOML file.

    Args:
        config_path: Path to the config file

    Returns:
        Dictionary containing configuration values
    """
    try:
        with open(config_path, "rb") as config_file:
            return tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Error loading config from {config_path}: {error}") from error


def init_config(target_dir: Optional[Path] = None) -> Path:
    """
    Copy default configuration to target directory.

    Args:
        target_dir: Directory to create config file in (defaults to current directory)

    Returns:
        Path to the created config file

    Raises:
        FileExistsError: If config file already exists
        OSError: If file operations fail
    """
    if target_dir is None:
        target_dir = Path.cwd()

    target_path = target_dir / CONFIG_FILENAME

    if target_path.exists():
        raise FileExistsError(f"Config file already exists at {target_path}")

    if not DEFAULT_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Default config template not found at {DEFAULT_CONFIG_PATH}"
        )

    # Copy from default location
    shutil.copy2(DEFAULT_CONFIG_PATH, target_path)

    return target_path
