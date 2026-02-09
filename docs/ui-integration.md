# Connecting your UI to this API

## 1. Run the API

From this repo (with venv):

```bash
uvicorn app.main:app --reload
```

API base URL: **http://localhost:8000** (or your deployed URL).

CORS is enabled so the browser can call the API from another origin (e.g. your UI on localhost:3000).

---

## 2. Endpoints your UI can call

### Ask a question (answer + citations)

**POST** `/answer`

**Request (JSON):**
```json
{
  "question": "What is this project about?",
  "top_k": 5
}
```
`top_k` is optional (default 5).

**Response (JSON):**
```json
{
  "answer": "The model's answer text...",
  "citations": [
    {
      "chunk_id": "sample-doc_0",
      "doc_id": "sample-doc",
      "section_title": "Introduction",
      "url": "https://example.com/doc",
      "source_name": "sample_doc.md"
    }
  ]
}
```
`url` may be `null`. Show citations under the answer (e.g. "Sources: Introduction (sample_doc.md), ...").

---

### Optional: get chunks only (no LLM)

**POST** `/query`

**Request:** `{ "question": "...", "top_k": 5 }`  
**Response:** `{ "chunks": [ { "text", "doc_id", "section_title", "url", "source_name", "chunk_id", "score" }, ... ] }`

---

### Optional: upload a document

**POST** `/ingest` (multipart form)

- **file** (required): the .md or text file
- **doc_id** (optional): stable id for this doc (default from filename)
- **url** (optional): link for citations

**Response:** `{ "status": "ok", "doc_id": "...", "source_name": "...", "chunks_stored": 8 }`

---

## 3. React + Netlify (your setup)

**Important:** Netlify hosts your **React frontend only**. This RAG API (FastAPI) must run somewhere else—e.g. **Railway**, **Render**, **Fly.io**, or a VPS. Your React app will call that API URL.

### Env var in the React repo

Use one env var for the API base URL so it works locally and in production:

- **Vite:** `VITE_API_URL` (use `import.meta.env.VITE_API_URL`)
- **Create React App:** `REACT_APP_API_URL` (use `process.env.REACT_APP_API_URL`)

**Local dev:** In `.env` or `.env.local`:
```env
VITE_API_URL=http://localhost:8000
```
(or `REACT_APP_API_URL=http://localhost:8000` for CRA)

**Netlify:** In Netlify dashboard → Site → Environment variables, add:
```env
VITE_API_URL=https://your-api-url.railway.app
```
(or whatever URL your deployed API has). Rebuild the site after adding the variable.

### Example: ask and show answer + citations

```jsx
const API_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL || "http://localhost:8000";

function AskForm() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [citations, setCitations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 5 }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAnswer(data.answer);
      setCitations(data.citations || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a question" />
      <button type="submit" disabled={loading}>{loading ? "..." : "Ask"}</button>
      {error && <p className="error">{error}</p>}
      {answer && (
        <div>
          <p>{answer}</p>
          {citations.length > 0 && (
            <ul>
              {citations.map((c, i) => (
                <li key={i}>
                  {c.section_title} ({c.source_name})
                  {c.url && <a href={c.url} target="_blank" rel="noopener noreferrer"> Link</a>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </form>
  );
}
```

### CORS when the API is deployed

This API has CORS enabled with `allow_origins=["*"]` so any origin (including your Netlify URL) can call it. For tighter security in production you can change that in `app/main.py` to your Netlify domain, e.g.:

```python
allow_origins=["https://your-site.netlify.app"]
```

---

## 4. Quick reference (any frontend)

1. **Set API base URL**  
   Env var in React: `VITE_API_URL` (Vite) or `REACT_APP_API_URL` (CRA). Local: `http://localhost:8000`; production: your deployed API URL.

2. **Call the API**  
   `POST ${API_URL}/answer` with body `{ "question": "...", "top_k": 5 }` → `{ "answer": "...", "citations": [...] }`.

3. **Display**  
   Show `answer` and list `citations` (section_title, source_name, url).

No API key needed for these endpoints.
