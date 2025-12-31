# README

A simple, yet opinionated linter for Python that helps you choose more descriptive variable names.

## Strictness levels

Yina lint operates on 5 strictness levels. Each level includes all the rules from the previous levels.

### Level 1: Length and charset

- Variables must be at least 3 characters long.
- Variables can only contain characters: a-Z, A-Z, 0-9 and _.
- Variables cannot start with a number.

### Level 2: Naming conventions

- Snake case will be enforced for regular variables and camel case for class names.
- All constants must be fully capitalized.
- Snake case variables that are not constants cannot have capital letters.

### Level 3 (default): Word length, max length, repetition

- Max variable length: 32 characters.
- **Applied for each "segment" in a variable name, like "one" in "one_two_three", or "One" in "OneTwoThree" (for class names):**
  - No more than 2 underscores in a row.
  - No more than 2 of the same letter in a row.
  - At least 3 characters long.

### Level 4: Pronounceability

- **Applied for each "segment" in a variable name, like "one" in "one_two_three", or "One" in "OneTwoThree" (for class names):**
  - At least one vowel
  - No more than 4 consonants in a row

### Level 5: Non vagueness

- No vague words like "item(s)", "thing(s)", "object(s)", "element(s)", "data", "value" or "result". "string" or "dataframe" are also disallowed. Applies only to the entire variable name, vague segments are allowed.
- No numbers.

## Configuration

- If there is a `.naming.toml` file in the working directory, it will be used.
- If not, the default `yina-lint/config/naming.toml` file will be applied.

You can use the command `yina init` to create a configuration file for your project with the default values you can modify.
