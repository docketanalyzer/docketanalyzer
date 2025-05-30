# Package Configuration

Use the `da configure` to run the interactive configuration script. This will cache various keys and settings in `~/.cache/docketanalyzer/config.json`.

You can access these keys in code like this:

```python
from docketanalyzer import env

print(env.DA_DATA_DIR)
```

| Variable | Description |
|----------|-------------|
| `DA_DATA_DIR` | Directory for storing data managed by docketanalyzer |
| `PACER_USERNAME` | PACER login username |
| `PACER_PASSWORD` | PACER login password |
| `COURTLISTENER_TOKEN` | CourtListener API token |
| `HF_TOKEN` | Hugging Face access token |
| `WANDB_API_KEY` | Weights & Biases key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `COHERE_API_KEY` | Cohere API key |
| `GROQ_API_KEY` | Groq API key |
| `TOGETHER_API_KEY` | Together AI API key |
| `RUNPOD_API_KEY` | Runpod API key |
| `RUNPOD_INFERENCE_ENDPOINT_ID` | Runpod Inference endpoint |
| `RUNPOD_ROUTINES_ENDPOINT_ID` | Runpod Routines endpoint |
| `RUNPOD_OCR_ENDPOINT_ID` | Runpod OCR endpoint |
| `ELASTIC_URL` | Elasticsearch connection URL |
| `POSTGRES_URL` | Postgres connection URL |
| `REDIS_URL` | Redis connection URL |
| `AWS_ACCESS_KEY_ID` | S3 access key |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key |
| `AWS_S3_BUCKET_NAME` | S3 bucket name |
| `AWS_S3_ENDPOINT_URL` | Custom S3 endpoint |
