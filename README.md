# Ultra Doc Intelligence

Ultra Doc Intelligence is a document Q&A and extraction app for logistics documents.

It provides:
- Document upload (`.pdf`, `.docx`, `.txt`, `.md`, `.csv`, `.json`)
- Retrieval-Augmented Generation (RAG) question answering
- Structured shipment data extraction as JSON
- Browser frontend + Flask backend API (Vercel-ready)

## Tech Stack

- Frontend: HTML/CSS/JS (served by Flask) + optional Streamlit local app
- Backend API: Flask + Flask-CORS
- Retrieval: SentenceTransformers + FAISS (cosine similarity)
- LLM: Google Gemini via `google-genai`
- Document parsing: `pdfplumber`, `pypdf`, `python-docx`

## Project Structure

```text
ultra-doc-intelligence/
|-- backend/
|   |-- app.py            # Flask API routes
|   |-- static/index.html # Browser UI served at /
|   |-- config.py         # Env config + Gemini client
|   |-- parser.py         # PDF/DOCX/TXT parsing + cleanup
|   |-- embeddings.py     # Chunking + embedding + FAISS index
|   |-- rag_pipeline.py   # Retrieve + answer + confidence
|   `-- extractor.py      # Structured JSON extraction
|-- frontend/
|   `-- app.py            # Optional Streamlit UI for local use
|-- api/
|   `-- index.py          # Vercel Python entrypoint
|-- data/
|   `-- uploads/          # Uploaded docs saved here
|-- vercel.json           # Vercel routing/build config
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Prerequisites

- Python 3.10+ (3.12 recommended)
- pip
- A Gemini API key

## 1) Setup Environment

From project root:

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2) Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Notes:
- `GEMINI_API_KEY` is required.
- `GEMINI_MODEL` is optional; default is `gemini-2.5-flash`.
- You can also use `GOOGLE_API_KEY` instead of `GEMINI_API_KEY`.

## 3) Start the Backend (Flask)

Open terminal 1 at project root:

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python app.py
```

### macOS/Linux

```bash
source .venv/bin/activate
cd backend
python app.py
```

Backend default URL:
- `http://127.0.0.1:5000`

## 4) Open The Browser UI

Visit:
- `http://127.0.0.1:5000`

## 5) How to Use

1. Upload a logistics document from the web UI.
2. Ask questions in natural language.
3. Click **Extract Structured Data** to get shipment fields in JSON.

## Deploy To Vercel

1. Push this repo to GitHub.
2. In Vercel, click **Add New > Project** and import the repo.
3. Set Environment Variables in Vercel project settings:
   - `GEMINI_API_KEY` (required)
   - `GEMINI_MODEL` (optional, default is `gemini-2.5-flash`)
4. Deploy.

After deployment:
- Open your Vercel URL to use the app UI.
- API routes are available at `/upload`, `/ask`, and `/extract`.

Notes for Vercel serverless runtime:
- Uploaded files are stored in `/tmp` during a request lifecycle (ephemeral).
- In-memory FAISS/chunks can reset on cold starts or instance changes.
- For production persistence, move docs/chunks/index to external storage (DB/object store/vector DB).


## API Endpoints

### `POST /upload`

Uploads and indexes one document.

Request:
- `multipart/form-data`
- field: `file`

Success response:

```json
{
  "message": "Document processed successfully",
  "chunks": 12,
  "filename": "sample.pdf"
}
```

### `POST /ask`

Asks a question against uploaded document context.

Request:

```json
{
  "query": "What is the shipment ID?"
}
```

Response:

```json
{
  "answer": "LD 53657",
  "confidence": 0.64,
  "sources": ["..."]
}
```

### `POST /extract`

Extracts structured shipment data from uploaded document text.

Response:

```json
{
  "data": {
    "shipment_id": "LD 53657",
    "shipper": "...",
    "consignee": "...",
    "pickup_datetime": null,
    "delivery_datetime": null,
    "equipment_type": "Flatbed",
    "mode": "FTL",
    "rate": 400,
    "currency": "USD",
    "weight": null,
    "carrier_name": "..."
  }
}
```

## Configuration

Set in `backend/config.py` through env:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL`

Defaults:
- Model: `gemini-2.5-flash`

## Dependency List

Current `requirements.txt`:
- flask
- flask-cors
- streamlit
- faiss-cpu
- sentence-transformers
- pypdf
- pdfplumber
- python-docx
- google-genai
- numpy
- python-dotenv

## Troubleshooting

### 1. "Missing Gemini API key"
- Ensure `.env` exists in project root.
- Set `GEMINI_API_KEY=...`.
- Restart backend after changes.

### 2. Frontend says backend is unreachable
- Confirm backend is running on `http://127.0.0.1:5000`.
- Check terminal for Flask errors.

### 3. Upload works but answers are poor
- Re-upload document after backend restart.
- Use clearer factual queries (e.g., "What is the carrier name?").

### 4. Source text looks incomplete or odd
- PDF extraction can vary by file formatting.
- Current parser uses `pdfplumber` word-based reconstruction with cleanup heuristics.

### 5. `Extract Structured Data` fails
- Ensure a file was uploaded in current backend session.
- Check backend logs for Gemini/model errors.

## Development Notes

- Backend currently keeps FAISS index and chunks in memory only.
- `data/uploads/` stores uploaded files.
- CORS is enabled for local frontend-backend communication.

