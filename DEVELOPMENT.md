# Development

## Install

```
pip install '.[dev]'
```

# Docs

```
mkdocs serve
mkdocs build
```

## Test

```
pytest -vv
pytest -vv -m "cost" # for tests that incur PACER fees
```

## Format

```
ruff format . && ruff check --fix .
```

## Build and Push to PyPi

```
da build
da build --push
```
