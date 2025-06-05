# ChaxAI

ChaxAI is a self‑hosted assistant that answers questions using the contents of your documents. It combines FastAPI, LangChain, and OpenAI with a FAISS vector store. A lightweight React interface enables chatting with the backend. The project is designed for easy local deployment and extension.

## Features

- Parse PDF, Markdown, and text files
- Create a FAISS vector index locally
- Ask questions through a REST API with source citations
- React + Tailwind chat UI with light/dark mode
- Health check and document listing endpoints

## Getting Started

### 1. Ingest Documents

Place your files in `backend/docs/` and run:

```bash
cd backend
cp .env.example .env  # add your OpenAI key
# optionally set VECTORSTORE_DIR if you wish to store embeddings elsewhere
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
npm run dev
```

Open <http://localhost:3000> and start asking questions.

### API Endpoints

The backend exposes a few endpoints:

| Method | Path        | Description                    |
| ------ | ----------- | ------------------------------ |
| `GET`  | `/health`   | Returns `{"status": "ok"}`      |
| `GET`  | `/documents`| List document sources in the vector store |
| `POST` | `/ask`      | Ask a question using JSON `{ "question": "..." }` |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
