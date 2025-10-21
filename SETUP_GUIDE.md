# Installation and Setup Guide

## Install Package in Development Mode

After updating all imports, install the package in development mode:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate

# Install package in editable mode
pip install -e .
```

This will:
- Make the `app` package importable from anywhere
- Allow changes to take effect immediately without reinstalling
- Eliminate the need for manual sys.path manipulation

## Verify Installation

Test that imports work correctly:

```python
# Test in Python REPL
python -c "from app.service.traffic import compute_match; print('Success!')"
```

## Run the Application

```bash
# Start the API server
python -m app.app

# Or using uvicorn directly
uvicorn app.rest.private.main:app --reload --host 0.0.0.0 --port 8000
```

## Benefits of pyproject.toml Approach

1. **Clean Imports**: No more `sys.path` hacks
2. **Standard Structure**: Follows Python packaging standards
3. **Dependency Management**: All dependencies in one place
4. **IDE Support**: Better autocomplete and type hints
5. **Testing**: Easier to run tests with proper package structure

## Import Pattern

All imports now follow this pattern:
```python
from app.module.submodule import function
```

Examples:
- `from app.service.traffic import compute_match`
- `from app.config.db import get_db`
- `from app.utils.logger import api_logger`
