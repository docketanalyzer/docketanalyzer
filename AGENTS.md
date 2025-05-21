# Repo Guidelines

This repository houses the `docketanalyzer` package and its documentation. Agents working in this repository should follow these guidelines.

## Documentation Goals

The docs are built with **MkDocs** using the Material theme and `mkdocstrings`. The current content is minimal. The goal is to expand it with:

1. **Project Overview and Installation** – Describe the package purpose and how to install it. Mention optional extensions. Use `pip install docketanalyzer[pacer]` or `pip install docketanalyzer[all]` to enable the PACER features. Ignore the OCR extension for now.
2. **Quickstart Guides** – Create short tutorials for major parts of the package:
   - PACER usage
   - Docket management
   - Services (database, redis, s3)
   - Agents
3. **Extended Examples** – Demonstrate full workflows such as downloading dockets, storing files in S3 and parsing results into a database. Include example CLI commands when relevant.
4. **API Reference** – Use `mkdocstrings` to document the modules in `docketanalyzer.*`. Ensure docstrings are complete so that the reference pages are meaningful.
5. **Configuration Details** – Document the environment variables and settings in `docketanalyzer.config.env`.

Whenever new pages are added, update `mkdocs.yml` to keep the navigation in sync. New assets (images, css, etc.) belong under `docs/static`.

## Testing

Before committing any changes, run:

```bash
pytest -q
```

Some tests require optional dependencies and credentials (marked with `@pytest.mark.local`). It is fine if those tests are skipped or fail because the environment lacks those dependencies.

When documentation is modified, run:

```bash
mkdocs build --strict
```

This ensures there are no build errors or broken references.

