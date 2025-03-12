# Development

## Install

```
pip install '.[dev]'
```

## Test

```
pytest -vv
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
