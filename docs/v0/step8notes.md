# Step 8 & 9: Answer endpoint (question + chunks → LLM) + citations

## What we're doing

Step 7 returns top-k chunks for a question. Step 8 **sends the question and those chunks to the LLM** (Gemini, per step 1/2 notes) to produce an **answer**. Step 9 is **returning that answer plus citations** (metadata for the chunks used) so the client can show "Source: section X of doc Y" and links.

So we implement a single flow: **question → (embed + search) → (prompt with chunks → Gemini) → answer + citations**.

---

## Design

- **LLM:** Gemini (config: `gemini_api_key`, `gemini_model_name`). Step 1 notes chose hosted Gemini for quality and free tier; dev notes mentioned "DeepSeek" but config and step 2 use Gemini, so we use Gemini.
- **Prompt:** Context = numbered chunks (section_title + text). Instruction: answer using only the context; if not in context, say so; be concise. Temperature 0.2, max_output_tokens 1024.
- **Endpoint:** `POST /answer` with body `{ "question": str, "top_k": int? }` (default top_k 5). Internally: embed question → search top_k chunks → build prompt → call Gemini → return `{ "answer": str, "citations": [ { "chunk_id", "doc_id", "section_title", "url", "source_name" }, ... ] }`.
- **Citations:** One object per retrieved chunk (same order as context). Fields: chunk_id, doc_id, section_title, url, source_name (no full text in citations).

---

## Implementation

- **app/services/llm.py:** `answer_from_chunks(question, chunks)` — build context string from chunks, build prompt, call Gemini `generate_content`, return answer text. Lazy-init model. Handle empty/blocked response.
- **app/main.py:** `POST /answer` — run query (embed + search), call `answer_from_chunks(question, chunks)`, build citations from chunks, return AnswerResponse(answer, citations).
- **Dependency:** `google-generativeai`. Run: `pip install google-generativeai` or `pip install -r requirements-step8.txt`.
- **Supported models:** Use a model that supports `generateContent` in API v1beta. Default: `gemini-2.5-flash`. Others: `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-3-flash-preview`. Set `GEMINI_MODEL_NAME` in `.env`. Avoid deprecated/experimental IDs (e.g. `gemini-2.0-flash-exp`, `gemini-1.5-flash` may be unavailable).

---

## Manual test

1. Start the API: `uvicorn app.main:app --reload` (from project root with venv).
2. Ensure Qdrant has data: run `python scripts/manual_test_chunking.py` once (without `--no-store`).
3. Run: `python scripts/manual_test_answer.py`  
   Or: `python scripts/manual_test_answer.py "Your question" --top-k 3`  
   Or call the API directly (PowerShell):  
   `Invoke-RestMethod -Method Post -Uri http://localhost:8000/answer -ContentType "application/json" -Body '{"question": "What is this about?", "top_k": 3}'`

---

## Summary

Step 8: Answer endpoint runs query then LLM; returns answer + citations (step 9) in one response. LLM = Gemini; citations = metadata per chunk for display/links.
