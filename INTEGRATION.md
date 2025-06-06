# Integrating ChaxAI

This document explains how to embed ChaxAI or communicate with the API from other applications. The steps below assume you already have the backend and frontend running or deployed.

## REST API

All functionality is available through a simple REST API served by FastAPI. The base URL defaults to `http://localhost:8000`. You can change this when deploying behind a proxy or container platform.

### Authentication

If `API_TOKENS` is set in the backend `.env` file, all modifying endpoints require the `X-API-Token` header. Tokens are compared using constant-time logic to guard against timing attacks.

```http
X-API-Token: your-token
```

### Endpoints

| Method | Path | Description |
| ----- | ---- | ----------- |
| `GET` | `/health` | Basic health check |
| `GET` | `/documents` | List indexed documents |
| `POST` | `/ask` | Ask a question. JSON: `{ "question": "..." }` |
| `POST` | `/upload` | Upload documents. Multipart form field `files` |
| `DELETE` | `/documents/{name}` | Remove a document |

All responses include an `X-Request-ID` header for tracing.
The React UI shows this ID with each answer.

### Error Handling

Errors are returned as JSON with a `detail` field. Common status codes include:

- `400` for invalid parameters or file types
- `403` for missing or invalid tokens
- `404` when requesting a non‑existent document
- `500` for unexpected server errors

## JavaScript Widget

To embed ChaxAI on your own site, build the widget bundle and initialize it.

```bash
cd frontend
npm run build:widget
```

Include the bundle and call `initChaxAI`:

```html
<div id="chaxai"></div>
<script src="/path/to/chaxai-widget.umd.cjs"></script>
<script>
  window.initChaxAI({
    elementId: 'chaxai',
    apiUrl: 'https://your-backend.example.com',
    apiToken: 'optional-token'
  });
</script>
```

The widget is self-contained and can be styled via Tailwind or custom CSS. It will communicate with the backend URL you provide.

## Custom Providers

ChaxAI supports multiple LLM providers. Set the following variables in `backend/.env` to switch models or point to custom endpoints:

- `LLM_PROVIDER` – `openai`, `grok`, or `claude`
- `OPENAI_API_KEY`, `GROK_API_KEY`, or `ANTHROPIC_API_KEY`
- `OPENAI_API_BASE`, `GROK_API_BASE`, `ANTHROPIC_API_BASE`

These settings control both embeddings and chat completions. When using alternative hosts like self-hosted OpenAI-compatible services, update the corresponding `*_API_BASE` variable.

## File Management

Files uploaded through `/upload` are stored in `backend/docs`. Filenames are sanitized to prevent path traversal. The ingestion pipeline updates the FAISS vector store automatically. Deleting a document triggers a rebuild of the store to keep search results accurate.

## Logging and Monitoring

Set `LOG_LEVEL` in `.env` to control verbosity. Each request is assigned an `X-Request-ID` which appears in the logs, making it easier to correlate requests with frontend activity.

## Next Steps

- Add automated tests using `pytest`
- Build Docker images for production deployments
- Implement user authentication beyond shared API tokens

ChaxAI is intentionally lightweight so you can integrate it with any platform. Feel free to adapt the code for your own workflows.

## Command Line Tools

The repository provides an ingestion script for adding documents to the
vector store. Run it from the `backend` directory:

```bash
python app/ingest.py /path/to/docs
```

You can call `ingest_paths` directly from your own Python code to integrate with
existing pipelines. Whenever documents are added or removed while the server is
running, the FAISS index is refreshed so subsequent questions reflect the latest
content.

For production deployments consider scheduling ingestion periodically or
triggering it whenever new files are uploaded through another system.

