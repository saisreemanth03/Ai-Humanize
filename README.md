# HumanizeAI

HumanizeAI refines awkward or overly robotic writing for clarity and flow while aiming to preserve the author's meaning. It is a writing-quality tool, not a detector-evasion product. The frontend supports text input and PDF, DOCX, and TXT extraction; the FastAPI backend calls OpenAI for rewriting and a separate comparison, with deterministic entity checks as a second safeguard.

## Features

- Natural, professional, conversational, polished, and concise tones across seven writing contexts.
- Minimal rewrite option; input and output remain separate.
- Separate AI comparison of meaning and factual consistency, plus deterministic checks for names/capitalized terms, dates, and numbers.
- Editable extracted text preview; text-based PDFs, DOCX paragraphs and tables, and UTF-8 TXT files are supported (5 MB upload limit).
- Copy and `.txt` download, useful error messages, responsive light UI, and no permanent document storage.

Automated checks can miss errors. They do not establish factual truth; review important text yourself. Scanned PDF OCR is not supported. Uploaded text is sent to the configured OpenAI model for processing.

## Technology

React, Vite, JavaScript, Lucide React; Python, FastAPI, Pydantic, Uvicorn, OpenAI Python SDK, pypdf, python-docx.

## Structure

```text
backend/app/       FastAPI endpoints, schemas, prompts, extraction and AI services
backend/tests/     API and extraction tests (AI calls are not used by the tests)
frontend/src/      React application and API client
```

## Prerequisites

- Windows 10/11, PowerShell, VS Code
- Python 3.10+ and Node.js 20+
- OpenAI API key for actual humanization and independent validation

## Install and run

From the project root (`C:\Users\saisr\OneDrive\Desktop\Ai_Dev`), create local environment files. These commands assume the files do not already exist; keep your existing values if they do:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Edit `backend\.env` and configure the backend settings below. `frontend\.env` sets the API base URL used by the browser. Restart the relevant server after changing either environment file.

| Variable | Required | Value |
|---|---|---|
| `OPENAI_API_KEY` | Yes, for humanization | Your OpenAI API key. Keep it only in `backend\.env`; never put it in the frontend. |
| `OPENAI_MODEL` | No | Model name; defaults to `gpt-4o-mini`. |
| `FRONTEND_ORIGIN` | For CORS | Exact browser origin, defaults to `http://localhost:5173`. Set it to the deployed frontend origin in deployment. |
| `VITE_API_BASE_URL` | Yes for this local setup | Backend base URL, normally `http://localhost:8000`. For deployment, set the public API origin before building the frontend. |

In PowerShell terminal 1, from the project root, create the virtual environment and install the backend packages:

```powershell
py -3 -m venv .\backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

Start the backend from the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir .\backend --reload --host 127.0.0.1 --port 8000
```

In PowerShell terminal 2, from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`). For a deployed frontend, configure `VITE_API_BASE_URL` before building, and set the backend `FRONTEND_ORIGIN` to the exact deployed origin. Never put the AI key in the frontend environment.

## API

- `GET /` — service information and whether the API key is configured.
- `GET /health` — health check.
- `POST /api/humanize` — JSON `{ "text": "...", "context": "General Writing", "tone": "Natural", "minimal_rewrite": false }`.
- `POST /api/extract-document` — multipart form field `file`; returns filename, type, extracted text, word and character counts, and warnings.
- `POST /api/humanize-document` — multipart `file`, `context`, `tone`, `minimal_rewrite`; runs extraction and the same processing pipeline.

Open `http://localhost:8000/docs` for the interactive API schema while the backend runs.

## Tests and build

From the project root:

```powershell
backend\.venv\Scripts\Activate.ps1
cd backend
python -m pytest
cd ..\frontend
npm run build
```

From the project root, run backend tests and build the frontend:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest .\backend\tests -q
Push-Location .\frontend
npm ci
npm run build
Pop-Location
```

The backend suite uses mocked AI calls, so it does not require an API key or incur model usage. It covers text and document route workflows, document extraction, missing-key handling, independent-validation failure, and file errors. It does not prove that a real account key/model can complete a live request; verify that separately after configuring `OPENAI_API_KEY`.

## Troubleshooting

- **AI service not configured:** set `OPENAI_API_KEY` in `backend\.env`, then restart Uvicorn.
- **Browser cannot connect:** confirm both servers are running; set `VITE_API_BASE_URL`; set backend `FRONTEND_ORIGIN` to the exact frontend origin and restart.
- **PDF has no text:** it may be scanned. This version does not include OCR.
- **`py` is unavailable:** install Python and enable the Python launcher, or create the environment with `python -m venv .\backend\.venv`; use the venv executable shown above for all later commands.
- **PowerShell blocks activation:** no activation is needed; invoke `backend\.venv\Scripts\python.exe` directly as shown above.
- **Model timeout or invalid response:** retry; the app reports a failure and does not replace the input with fake output.

## Security and privacy

The API key is read only by the backend. Upload size, extension, and text length are constrained; files are processed in memory and not saved. CORS allows only `FRONTEND_ORIGIN`. Use HTTPS, a protected secret store, and a private backend in deployment. Check your OpenAI account's data handling settings before sending sensitive text.

## Production Split-Deployment (Docker + Vercel)

### 1. Backend Containerization (Render / Cloud Run / Railway / Fly.io)
The backend includes a `Dockerfile` with system-level `ffmpeg` dependencies pre-installed for audio/video processing:
```bash
cd backend
docker build -t humanizeai-backend .
docker run -p 8000:8000 -e PORT=8000 -e GEMINI_API_KEY="your-key" humanizeai-backend
```
In your cloud dashboard, configure the following Environment Variables:
- `PORT`: `8000` (or platform default)
- `GEMINI_API_KEY` or `OPENAI_API_KEY`: Your AI provider credentials
- `FRONTEND_ORIGIN`: Your deployed frontend domain (e.g. `https://humanize-ai.vercel.app`)

### 2. Frontend SPA Deployment (Vercel / Cloudflare Pages)
The frontend is configured with `vercel.json` for React Router SPA rewrites:
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: `VITE_API_BASE_URL` pointing to your deployed backend (e.g., `https://your-backend.onrender.com`)
