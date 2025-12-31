# README

Variable name linter for Python projects.

## Strictness levels

### Level One: Length and charset

- Variables must be at least 3 characters long.
- Variables can only contain characters: a-Z, A-Z, 0-9 and _.
- Variables cannot start with a number.

### Level Two: Naming conventions

- Snake case will be enforced for regular variables and camel case for class names.
- All constants must be fully capitalized.
- Snake case variables that are not constants cannot have capital letters.

### Level three: Word length, max length, repetition

- Max variable length: 20
- **Applied for each "segment", like "one" in "one_two_three", or "One" in "OneTwoThree" (classes):**
  - No more than 2 underscores in a row.
  - No more than 2 of the same letter in a row.
  - At least 3 characters long.

### Level four: Pronounceability

- **Applied for each "segment", like "one" in "one_two_three", or "One" in "OneTwoThree" (classes):**
  - At least one vowel
  - No more than 3 consonants in a row

### Level five: Non vagueness

- No vague words like "item(s)", "thing(s)", "object(s)", "element(s)", "data", "value" or "result". "string" or "dataframe" are also disallowed. Applies only to the entire variable name, vague segments are allowed.
- No numbers.

## Configuration

The package `config/naming.toml` will be used if the working directory does not contain a `.naming.toml` file. If it does, only the local file will be used.

A command line option like `init` will copy the package config file to the working directory.

### Allowed names and segments

You can define a list of `allowed_names` and `allowed_segments` in the config file to allow certain variable names or segments that would otherwise be disallowed by the linter. The same for `banned_names` and `banned_segments` to ban certain names or segments regardless of the strictness level.
