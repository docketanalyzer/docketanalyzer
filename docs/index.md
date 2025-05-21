# Docket Analyzer Documentation

Docket Analyzer helps you manage federal court dockets and related documents. It
includes tools for downloading data from PACER and RECAP, storing files in S3 and
a PostgreSQL database, and running language‑model agents on your data.

## Installation

Install the base package:

```bash
pip install docketanalyzer
```

To enable PACER features install the optional `pacer` extras:

```bash
pip install 'docketanalyzer[pacer]'
```

Or install everything (excluding OCR for now) with:

```bash
pip install 'docketanalyzer[all]'
```

After installation run the interactive configuration script:

```bash
da configure
```
