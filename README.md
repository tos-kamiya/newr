# newr

*“Need to copy the last three images I downloaded—uh, what were the extensions again?”*

`newr` is a command-line file selector that allows you to pick files by modification time, with optional filtering by file type (kind) and flexible selection with count and order controls.
Supports glob patterns and MIME-type based filtering for documents, spreadsheets, presentations, and archives.

## Features

* Select files by modification time with a configurable count and optional oldest-first ordering.
* Filter files by kind (`doc`, `xls`, `ppt`, `zip`, etc.) based on MIME type.
* Supports glob patterns and multiple input files.
* Quiet mode and empty-result-safe mode.
* Outputs absolute file paths to stdout.

## Installation

You can install the latest version using `pipx`:

```sh
pipx install http://github.com/tos-kamiya/newr
```

**Note on Dependencies**

This tool uses `python-magic` to determine file types.
`python-magic` depends on the system `libmagic` library, so you may need to install `libmagic` separately depending on your OS.
For more details, please refer to the [official python-magic page](https://github.com/ahupp/python-magic).

## Usage

```sh
newr [OPTIONS] FILES...
```

### Examples

* Show the newest `.pdf` file in Downloads:

  ```sh
  newr -n 1 ~/Downloads/*.pdf
  ```

* Show the 3 oldest `.docx` files:

  ```sh
  newr -n 3 --reverse ~/Documents/*.docx
  ```

* Show the newest spreadsheet file (`xls` kind: `.xlsx`, `.xls`, `.ods`):

  ```sh
  newr -k xls -n 1 ~/Downloads/*
  ```

* Quiet mode (no log output), allow empty result:

  ```sh
  newr -q -0 -k ppt -n 1 ~/Downloads/*
  ```

**Copy the newest image file in your `~/Pictures` folder to the current directory**

* **Fish shell:**

  ```fish
  cp (newr -k image -n 1 ~/Pictures/*) .
  ```

* **Bash:**

  ```bash
  cp $(newr -k image -n 1 ~/Pictures/*) .
  ```

> The `-k image` option selects any file recognized as an image (such as `.jpg`, `.jpeg`, `.png`, `.gif`, etc.) based on its MIME type.
> In Bash, use `$(...)` for command substitution; in Fish, use `(...)`.

## Options

* `-n N, --number N`
  Select this many files (default: 1).

* `-r, --reverse`
  Sort in ascending (oldest-first) order before selecting files.

* `-k, --kind KIND`
  Filter files by kind:
  `doc`, `xls`, `ppt`, `zip`, `image`, `video`, `audio`, `text`, etc.

* `-q, --quiet`
  Suppress all log output to stderr.

* `-0, --allow-empty-result`
  Exit successfully even if no files are found (otherwise, exits with error).

* `--version`
  Show version and exit.

### Supported Kinds

| Kind | Description            | Extensions Included                 |
| ---- | ---------------------- | ----------------------------------- |
| doc  | MS Word, ODF Text      | `.doc`, `.docx`, `.odt`             |
| xls  | Excel, ODF Spreadsheet | `.xls`, `.xlsx`, `.ods`             |
| ppt  | PowerPoint, ODF Slides | `.ppt`, `.pptx`, `.odp`             |
| zip  | Zip/Tar/7z/Archive     | `.zip`, `.tar`, `.7z`, `.rar`, etc. |

For other kinds (such as `image`, `audio`, `video`, `text`), all files whose MIME type starts with the given prefix (before the `/`) will be matched.

## Changelog

v0.4.0: Renamed project to `newr` and updated CLI/tooling references.
v0.3.0: Renamed project to `newer` and replaced `--newest/--oldest` with unified `--number` and `--reverse` options.

## License

MIT License
