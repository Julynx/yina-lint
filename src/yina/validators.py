"""Validators for naming conventions across 5 strictness levels."""

import re
from enum import IntEnum
from typing import List

from colorama import Fore, Style

# Constants for validation rules
MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 32
MAX_CONSECUTIVE_UNDERSCORES = 2
MAX_CONSECUTIVE_SAME_LETTER = 2
MAX_CONSECUTIVE_CONSONANTS = 4
MIN_SEGMENT_LENGTH = 3


class StrictnessLevel(IntEnum):
    """Enum representing the 5 strictness levels."""

    LEVEL_ONE = 1
    LEVEL_TWO = 2
    LEVEL_THREE = 3
    LEVEL_FOUR = 4
    LEVEL_FIVE = 5


class ValidationError:
    """Represents a naming validation error."""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        message: str,
        level: StrictnessLevel,
        line_number: int = None,
        column_number: int = None,
    ):
        """Initialize validation error with name, message, level, and location."""
        self.name = name
        self.message = message
        self.level = level
        self.line_number = line_number
        self.column_number = column_number

    def __repr__(self):
        """String representation of validation error."""
        location = ""
        if self.line_number is not None:
            location = f" (line {self.line_number}"
            if self.column_number is not None:
                location += f", col {self.column_number}"
            location += ")"

        # Color the name in cyan
        colored_name = f"{Fore.CYAN}{self.name}{Style.RESET_ALL}"

        # Color segments in yellow when they appear in the message
        colored_message = self.message
        if "Segment '" in self.message:
            # Extract and color segment names
            colored_message = re.sub(
                r"Segment '([^']+)'",
                rf"Segment '{Fore.YELLOW}\1{Style.RESET_ALL}'",
                self.message,
            )

        return f"Level {self.level}: {colored_name}{location} - {colored_message}"

    def __str__(self):
        """Human-readable string representation."""
        return self.__repr__()


def get_segments(name: str, is_class: bool = False) -> List[str]:
    """
    Split a variable name into segments.

    For snake_case: split by underscore
    For CamelCase: split by capital letters
    """
    if is_class:
        # CamelCase: split before capital letters
        segments = re.findall(r"[A-Z][a-z0-9]*", name)
    else:
        # snake_case: split by underscore
        segments = name.split("_")

    return [seg for seg in segments if seg]


# Level One: Length and charset
def validate_level_one(name: str) -> List[ValidationError]:
    """
    Validate Level 1 rules: basic length and character set.

    - Variables must be at least 3 characters long
    - Variables can only contain: a-z, A-Z, 0-9, _
    - Variables cannot start with a number
    """
    errors = []

    if len(name) < MIN_NAME_LENGTH:
        errors.append(
            ValidationError(
                name,
                f"Name must be at least {MIN_NAME_LENGTH} characters long",
                StrictnessLevel.LEVEL_ONE,
            )
        )

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        errors.append(
            ValidationError(
                name,
                "Name must contain only letters, numbers, and underscores, "
                "and cannot start with a number",
                StrictnessLevel.LEVEL_ONE,
            )
        )

    return errors


# Level Two: Naming conventions
def validate_level_two(name: str, is_class: bool = False) -> List[ValidationError]:
    """
    Validate Level 2 rules: naming conventions.

    - Snake_case for regular variables
    - CamelCase for class names
    - CONSTANTS must be fully capitalized
    - Regular variables cannot have capital letters
    """
    errors = []

    is_constant = name.isupper()

    if is_class:
        # Class names should be CamelCase
        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
            errors.append(
                ValidationError(
                    name,
                    "Class names must use CamelCase (start with capital, no underscores)",
                    StrictnessLevel.LEVEL_TWO,
                )
            )
    elif is_constant:
        # Constants should be UPPER_SNAKE_CASE
        if not re.match(r"^[A-Z][A-Z0-9_]*$", name):
            errors.append(
                ValidationError(
                    name,
                    "Constants must be fully capitalized with underscores",
                    StrictnessLevel.LEVEL_TWO,
                )
            )
    else:
        # Regular variables should be snake_case (no capitals)
        if re.match(r".*[A-Z].*", name):
            errors.append(
                ValidationError(
                    name,
                    "Regular variables must use snake_case (lowercase only)",
                    StrictnessLevel.LEVEL_TWO,
                )
            )

    return errors


# Level Three: Word length, max length, repetition
def validate_level_three(
    name: str,
    is_class: bool = False,
    allowed_segments: list = None,
) -> List[ValidationError]:
    """
    Validate Level 3 rules: length limits and repetition.

    - Max variable length: 20
    - No more than 2 underscores in a row
    - No more than 2 of the same letter in a row (checked per segment)
    - Each segment must be at least 3 characters long

    Args:
        name: Variable name to validate
        is_class: Whether this is a class name
        allowed_segments: List of segments that bypass all checks

    Returns:
        List of ValidationError objects
    """
    if allowed_segments is None:
        allowed_segments = []

    errors = []

    # Convert to lowercase set for O(1) lookups
    allowed_segments_lower = {seg.lower() for seg in allowed_segments}

    if len(name) > MAX_NAME_LENGTH:
        errors.append(
            ValidationError(
                name,
                f"Name exceeds maximum length of {MAX_NAME_LENGTH} characters",
                StrictnessLevel.LEVEL_THREE,
            )
        )

    if "_" * (MAX_CONSECUTIVE_UNDERSCORES + 1) in name:
        errors.append(
            ValidationError(
                name,
                f"Name contains more than {MAX_CONSECUTIVE_UNDERSCORES} underscores in a row",
                StrictnessLevel.LEVEL_THREE,
            )
        )

    # Check segment-specific rules
    segments = get_segments(name, is_class)
    for segment in segments:
        # Skip allowed segments
        if segment.lower() in allowed_segments_lower:
            continue

        # Check for more than 2 of the same letter in a row in this segment
        if re.search(rf"([a-zA-Z])\1{{{MAX_CONSECUTIVE_SAME_LETTER},}}", segment):
            error_message = (
                f"Segment '{segment}' contains more than "
                f"{MAX_CONSECUTIVE_SAME_LETTER} of the same letter in a row"
            )
            errors.append(
                ValidationError(
                    name,
                    error_message,
                    StrictnessLevel.LEVEL_THREE,
                )
            )

        # Check segment length (skip if Level 1 length check already failed)
        skip_segment_length = len(name) < MIN_NAME_LENGTH <= MIN_SEGMENT_LENGTH
        if not skip_segment_length and len(segment) < MIN_SEGMENT_LENGTH:
            errors.append(
                ValidationError(
                    name,
                    f"Segment '{segment}' is shorter than {MIN_SEGMENT_LENGTH} characters",
                    StrictnessLevel.LEVEL_THREE,
                )
            )

    return errors


# Level Four: Pronounceability
def validate_level_four(
    name: str, is_class: bool = False, allowed_segments: list = None
) -> List[ValidationError]:
    """
    Validate Level 4 rules: pronounceability.

    - No more than 3 consonants in a row (checked per segment)
    - Each segment must contain at least one vowel (including y)

    Args:
        name: Variable name to validate
        is_class: Whether this is a class name
        allowed_segments: List of segments that bypass all checks

    Returns:
        List of ValidationError objects
    """
    if allowed_segments is None:
        allowed_segments = []

    errors = []
    vowels = "aeiouyAEIOUY"

    # Convert to lowercase set for O(1) lookups
    allowed_segments_lower = {seg.lower() for seg in allowed_segments}
    segments = get_segments(name, is_class)

    for segment in segments:
        # Skip allowed segments
        if segment.lower() in allowed_segments_lower:
            continue

        # Check for more than MAX_CONSECUTIVE_CONSONANTS consonants in a row
        consonant_pattern = rf"[^aeiouyAEIOUY]{{{MAX_CONSECUTIVE_CONSONANTS + 1},}}"
        if re.search(consonant_pattern, segment):
            error_message = (
                f"Segment '{segment}' contains more than "
                f"{MAX_CONSECUTIVE_CONSONANTS} consonants in a row"
            )
            errors.append(
                ValidationError(
                    name,
                    error_message,
                    StrictnessLevel.LEVEL_FOUR,
                )
            )

        # Check segment has at least one vowel
        if not any(char in vowels for char in segment):
            errors.append(
                ValidationError(
                    name,
                    f"Segment '{segment}' does not contain a vowel",
                    StrictnessLevel.LEVEL_FOUR,
                )
            )

    return errors


# Level Five: Non-vagueness
def validate_level_five(
    name: str, vague_words: set, allow_numbers: bool
) -> List[ValidationError]:
    """
    Validate Level 5 rules: avoid vagueness.

    Args:
        name: Variable name to validate
        vague_words: Set of vague words to check against
        allow_numbers: Whether to allow numbers in names

    Returns:
        List of ValidationError objects
    """
    errors = []

    # Check if the entire variable name is vague (case-insensitive)
    if name.lower() in vague_words:
        errors.append(
            ValidationError(
                name,
                "Name is a vague word and should be more descriptive",
                StrictnessLevel.LEVEL_FIVE,
            )
        )

    # Check for numbers
    if not allow_numbers and re.search(r"\d", name):
        errors.append(
            ValidationError(name, "Name contains numbers", StrictnessLevel.LEVEL_FIVE)
        )

    return errors


def check_allowed_banned(
    name: str,
    is_class: bool,
    banned_names: list,
    banned_segments: list,
) -> List[ValidationError]:
    """
    Check if name is in banned lists.

    Args:
        name: Variable or class name to validate
        is_class: Whether this is a class name
        banned_names: List of names that are always banned
        banned_segments: List of segments that are banned

    Returns:
        List of ValidationError objects
    """
    errors = []

    # Convert to lowercase sets for O(1) lookups
    banned_names_lower = {banned_name.lower() for banned_name in banned_names}
    banned_segments_lower = {
        banned_segment.lower() for banned_segment in banned_segments
    }

    # Check banned names
    if name.lower() in banned_names_lower:
        errors.append(
            ValidationError(
                name,
                "Name is banned by configuration",
                StrictnessLevel.LEVEL_ONE,
            )
        )
        return errors  # If banned, no need to check further

    # Check banned segments
    segments = get_segments(name, is_class)
    for segment in segments:
        if segment.lower() in banned_segments_lower:
            errors.append(
                ValidationError(
                    name,
                    f"Segment '{segment}' is banned by configuration",
                    StrictnessLevel.LEVEL_ONE,
                )
            )

    return errors


def validate_name(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    name: str,
    max_level: StrictnessLevel,
    is_class: bool = False,
    config: dict = None,
    line_number: int = None,
    column_number: int = None,
) -> List[ValidationError]:
    """
    Validate a name against all rules up to the specified strictness level.

    Args:
        name: The variable or class name to validate
        max_level: The maximum strictness level to apply
        is_class: Whether this is a class name (affects Level 2 rules)
        config: Configuration dictionary with validation settings
        line_number: Line number where the name appears
        column_number: Column number where the name appears

    Returns:
        List of ValidationError objects
    """
    if config is None:
        config = {}

    # Extract config values
    allowed_names = config.get("linter", {}).get("allowed_names", [])
    allowed_segments = config.get("linter", {}).get("allowed_segments", [])
    banned_names = config.get("linter", {}).get("banned_names", [])
    banned_segments = config.get("linter", {}).get("banned_segments", [])
    vague_words = set(config.get("level_five", {}).get("vague_words", []))
    allow_numbers = config.get("level_five", {}).get("allow_numbers", False)

    # Convert to lowercase set for O(1) lookup
    allowed_names_lower = {allowed_name.lower() for allowed_name in allowed_names}

    # Check if name is in allowed list (bypass all checks)
    if name.lower() in allowed_names_lower:
        return []

    # Check allowed/banned lists first
    all_errors = check_allowed_banned(name, is_class, banned_names, banned_segments)

    # If already banned, return early
    if all_errors:
        # Add line/column info to existing errors
        for error in all_errors:
            error.line_number = line_number
            error.column_number = column_number
        return all_errors

    if max_level >= StrictnessLevel.LEVEL_ONE:
        level_one_errors = validate_level_one(name)
        all_errors.extend(level_one_errors)

    if max_level >= StrictnessLevel.LEVEL_TWO:
        all_errors.extend(validate_level_two(name, is_class))

    if max_level >= StrictnessLevel.LEVEL_THREE:
        all_errors.extend(validate_level_three(name, is_class, allowed_segments))

    if max_level >= StrictnessLevel.LEVEL_FOUR:
        all_errors.extend(validate_level_four(name, is_class, allowed_segments))

    if max_level >= StrictnessLevel.LEVEL_FIVE:
        all_errors.extend(validate_level_five(name, vague_words, allow_numbers))

    # Add line and column info to all errors
    for error in all_errors:
        error.line_number = line_number
        error.column_number = column_number

    return all_errors
