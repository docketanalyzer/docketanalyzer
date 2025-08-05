# Docket Analyzer Python Package

The Docket Analyzer Python package is a toolkit for working with federal court dockets.

> **Note** These docs are a work in progress. Will finish by v1.0.0.

You can install it with `pip`:

```bash
pip install 'docketanalyzer[all]'
```

Then run the interactive configuration script:

```bash
da configure
```

Alternatively, you can install just the core package and/or specific extensions:

```bash
pip install docketanalyzer
pip install 'docketanalyzer[pacer]'
```

Most of the docketanalyzer utilities are extremely high-level, opinionated wrappers around existing tools (e.g. Juriscraper, LiteLLM, HuggingFace, etc.). If the design choices don't fit your use case, we encourage you to use the underlying tools directly.