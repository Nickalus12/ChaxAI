# ChaxAI

ChaxAI is a self‑hosted assistant that answers questions using the contents of your documents. It combines FastAPI, LangChain, and optional OpenAI, Grok, or Claude models with a FAISS vector store. A lightweight React interface enables chatting with the backend. The project is designed for easy local deployment and extension.

## Features

- Parse PDF, Markdown, and text files
- Create a FAISS vector index locally
- Ask questions through a REST API with source citations
- React + Tailwind chat UI with light/dark mode
- Chat history persists locally for convenience
- Health check and document listing endpoints
- Modular React components with an API helper for easier customization

## Getting Started

### 1. Ingest Documents

Place your files in `backend/docs/` and run:

```bash
cd backend
# copy and edit .env.example
# set LLM_PROVIDER to openai, grok, or claude
# supply OPENAI_API_KEY, GROK_API_KEY, or ANTHROPIC_API_KEY accordingly
# optionally set OPENAI_API_BASE, ANTHROPIC_API_BASE, or GROK_API_BASE
# optionally set VECTORSTORE_DIR if you wish to store embeddings elsewhere
# you can also set ALLOWED_ORIGINS for CORS, comma-separated
# set API_TOKENS to require an API token for the backend
# set LOG_LEVEL to control logging verbosity
# set LOG_FILE to log to a file and MAX_UPLOAD_MB to limit upload size
pip install -r requirements.txt
python app/ingest.py
```

### 2. Start the Backend

```bash
uvicorn app.main:app --reload
```

### 3. Start the Frontend

```bash
cd frontend
npm install
cp .env.example .env  # adjust VITE_API_URL if backend runs elsewhere
npm run dev
```

`VITE_API_URL` sets the backend URL used by the chat UI. Change it if the
backend runs on a different host or port. If the backend requires an API token,
set `VITE_API_TOKEN` accordingly.

Open <http://localhost:3000> and start asking questions.

You can also upload additional files through the `/upload` endpoint or the
upload form in the UI. Filenames are sanitized to prevent path traversal.
New documents are added to the vector store automatically. Documents can be
removed with `DELETE /documents/{name}` or via the delete buttons in the UI.

### Docker (optional)

Dockerfiles are provided to simplify deployment. Build and run both services
with:

```bash
docker-compose build
docker-compose up
```

This will launch the backend on port 8000 and the frontend on port 3000.
Container logs are stored in the local `logs/` directory.

### Development Tips

* For faster iteration, run `uvicorn app.main:app --reload` so code changes are
  reloaded automatically.
* The React app uses Vite. The dev server reloads on file changes when running
  `npm run dev`.
* Vector stores can grow large. Clean the `backend/vectorstore` directory if you
  want to rebuild from scratch.
* Adjust `ALLOWED_ORIGINS` in `.env` if you host the frontend on another domain.
* Use `API_TOKENS` in `.env` to protect the API with shared tokens. Tokens are
  compared using constant-time checks for improved security.
* Set `LLM_PROVIDER` to `openai`, `grok`, or `claude` to choose the model.
* Set the matching API key (`OPENAI_API_KEY`, `GROK_API_KEY`, or
  `ANTHROPIC_API_KEY`).
* Optionally set `OPENAI_API_BASE`, `ANTHROPIC_API_BASE`, or `GROK_API_BASE`
  to point at custom endpoints.
* Set `LOG_LEVEL` in `.env` to control log verbosity.
* Set `LOG_FILE` to enable file logging and `MAX_UPLOAD_MB` to enforce an upload size limit.
* Lint your code before submitting PRs to keep the codebase tidy.

### API Endpoints

The backend exposes a few endpoints:

| Method | Path        | Description                    |
| ------ | ----------- | ------------------------------ |
| `GET`  | `/health`   | Returns `{"status": "ok"}`      |
| `GET`  | `/documents`| List document sources in the vector store |
| `POST` | `/ask`      | Ask a question using JSON `{ "question": "..." }` |
| `POST` | `/upload`   | Upload one or more documents |
| `DELETE` | `/documents/{name}` | Remove a document and rebuild the store |

When `API_TOKENS` is configured, include an `X-API-Token` header with one
of the allowed tokens when calling protected endpoints.
Each response also includes an `X-Request-ID` header that can be used for
tracing requests in logs.
The React chat UI displays this ID with each answer for easier debugging.

### Embedding the Chat Widget

You can include the frontend on any website as a small widget. Build the library
bundle with:

```bash
cd frontend
npm run build:widget
```

This creates `dist/chaxai-widget.umd.cjs` (and related files). Include the
script on your page and call `initChaxAI`:

```html
<div id="chaxai"></div>
<script src="/path/to/chaxai-widget.umd.cjs"></script>
<script>
  window.initChaxAI({ elementId: 'chaxai', apiUrl: 'http://localhost:8000' });
</script>
```

For advanced integration tips, see [INTEGRATION.md](INTEGRATION.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
