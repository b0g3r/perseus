# perseus

Tool for snapshot management. In early progress stage

## Prerequisites

- python >= 3.6
- pytest >= 4.0

## Installation

`pip install perseus`

## Usage

`perseus --help` or `python -m perseus --help`

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

### Local development
The project uses poetry as a dependency management tool. For local development convenient way to installing and
running project is using `poetry install`.

Poetry automatically creates venv (or uses already activated venv) and install all requirements to it and the project
itself as `editable` .
TIP: Use `poetry shell` or `poetry run` before running commands: they activate venv. If you want to connect venv to
your IDE, use `poetry env list --full-path`

## License
[MIT](https://choosealicense.com/licenses/mit/)
