# address-standardizer

A Python library that parses and standardizes address strings using OpenStreetMap data.

## Installation

```bash
pip install address-standardizer
```

## Usage

```python
from address_standardizer import AddressStandardizer

# Initialize the standardizer
standardizer = AddressStandardizer()

# Parse and standardize an address
result = standardizer.standardize("123 Main St, New York, NY 10001")
print(result)
```

## Features

- Parses address strings into structured components
- Standardizes address formatting
- Validates addresses against OpenStreetMap data
- Supports multiple address formats

## Contributing

### Setup

1. Clone the repository:
```bash
git clone https://github.com/KUKARAF/address_helper.git
cd address_helper
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

### Development Workflow

The project uses the following tools for code quality:

- **ruff**: Code formatting and linting
- **pytest**: Testing framework
- **mypy**: Static type checking

#### Running Checks Manually

```bash
# Format code
ruff format .

# Lint with fixes
ruff check --fix .

# Run tests
pytest

# Type checking
mypy address_standardizer
```

#### Pre-commit Hooks

Pre-commit hooks automatically run on every commit:
- Ruff formatting checks
- Ruff linting with fixes
- Test suite

If checks fail, fix the issues and try committing again. You can also run `pre-commit run --all-files` to check all files before committing.

### Code Style

- Line length: 100 characters
- Target Python version: 3.10+
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) conventions

### Testing

All new features must include tests. Run the test suite with:

```bash
pytest
```

For coverage reports:
```bash
pytest --cov=address_standardizer
```

## License

MIT
