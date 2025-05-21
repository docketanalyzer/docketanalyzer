# Docket Analyzer

Docket Analyzer is a toolkit for working with federal court dockets.
It wraps juriscraper for PACER downloads, manages docket files on disk or S3,
and provides simple language‑model agents for interacting with your data.

## Installation

```bash
pip install docketanalyzer
```

Optional extensions can be installed with extras. For PACER support:

```bash
pip install 'docketanalyzer[pacer]'
```

Install all available features (except OCR) with:

```bash
pip install 'docketanalyzer[all]'
```

After installing, run the configuration helper:

```bash
da configure
```

See the `docs/` directory or [documentation](https://docketanalyzer.com/docs)
for tutorials and API reference.
