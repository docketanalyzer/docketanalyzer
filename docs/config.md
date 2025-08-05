# Package Configuration

Use the `da configure` to run the interactive configuration script. This will cache various keys and settings in `~/.cache/docketanalyzer/config.json`.

You can access these keys in code like this:

```python
from docketanalyzer import env

print(env.DA_DATA_DIR)
```

You can also set these variables manually in your environment.
Environment variables will take precedence over the cached values.

| Variable | Description |
|---|---|
| `DA_DATA_DIR` | Directory for storing data managed by Docket Analyzer. |
| `PACER_USERNAME` | PACER login username. |
| `PACER_PASSWORD` | PACER login password. |
| `COURTLISTENER_TOKEN` | CourtListener API token. |
| `HF_TOKEN` | Hugging Face API token. |
| `WANDB_API_KEY` | Weights & Biases API key. |
| `ANTHROPIC_API_KEY` | Anthropic API key. |
| `OPENAI_API_KEY` | OpenAI API key. |
| `GEMINI_API_KEY` | Gemini API key. |
| `COHERE_API_KEY` | Cohere API key. |
| `GROQ_API_KEY` | Groq API key. |
| `ELASTIC_HOST` | Elasticsearch host. |
| `ELASTIC_PORT` | Elasticsearch port. |
| `POSTGRES_HOST` | PostgreSQL host. |
| `POSTGRES_PORT` | PostgreSQL port. |
| `POSTGRES_DB` | PostgreSQL database name. |
| `POSTGRES_USER` | PostgreSQL username. |
| `POSTGRES_PASSWORD` | PostgreSQL password. |
| `REDIS_HOST` | Redis host. |
| `REDIS_PORT` | Redis port. |
| `AWS_S3_BUCKET_NAME` | AWS S3 bucket name. |
| `AWS_S3_ENDPOINT_URL` | AWS S3 endpoint URL for S3-compatible storage. |
| `AWS_ACCESS_KEY_ID` | AWS access key ID. |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key. |
| `PYPI_TOKEN` | PyPI API token for package deployment. |
