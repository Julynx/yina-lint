# yina

_A simple, yet opinionated linter for Python that helps you choose more descriptive variable names._

`pip install yina`

<br>

[![Button Hover](https://img.shields.io/badge/Github-c9510c?style=for-the-badge)](https://github.com/Julynx/yina-lint)
[![Button Hover](https://img.shields.io/badge/PyPi-006dad?style=for-the-badge)](https://pypi.org/project/yina)

<br>

<img src='https://i.imgur.com/bpKaIBR.png' width='80%'>

## Usage

- Run `yina lint file.py` to lint a file or `yina lint src/` for a directory.
- Use the `--level N` option to specify the strictness level. Defaults to level 3.
- With `yina init` you can generate a configuration file for the working directory with default values you can edit.

## Strictness levels

Yina lint operates on 5 strictness levels. Each level includes all the rules from the previous levels.

| Level                                                      | Rules                                                                                                                                                                                                                                                                                                                                     |
| :--------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Level 1: Length and charset**                            | - Variables must be at least 3 characters long.<br>- Variables can only contain characters: a-Z, A-Z, 0-9 and _.<br>- Variables cannot start with a number.                                                                                                                                                                               |
| **Level 2: Naming conventions**                            | - Snake case will be enforced for regular variables and camel case for class names.<br>- All constants must be fully capitalized.<br>- Snake case variables that are not constants cannot have capital letters.                                                                                                                           |
| **Level 3 (default): Word length, max length, repetition** | - Max variable length: 32 characters.<br>- **Applied for each "word" in a variable name, like "one" in "one_two_three":**<br>&nbsp;&nbsp;- No more than 2 underscores in a row.<br>&nbsp;&nbsp;- No more than 2 of the same letter in a row.<br>&nbsp;&nbsp;- At least 3 characters long. |
| **Level 4: Pronounceability**                              | - **Applied for each "word" in a variable name, like "one" in "one_two_three":**<br>&nbsp;&nbsp;- At least one vowel<br>&nbsp;&nbsp;- No more than 4 consonants in a row                                                                                                                  |
| **Level 5: Non vagueness**                                 | - No vague words like "item(s)", "thing(s)", "object(s)", "element(s)", "data", "value" or "result". "string" or "dataframe" are also disallowed. Applies only to the entire variable name, vague segments are allowed.<br>- No numbers.                                                                                                  |

## Configuration

- If there is a `.yina.toml` file in the working directory, it will be used.
- If not, the default `yina-lint/config/yina.toml` file will be applied.
