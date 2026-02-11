"""
Step 8: Call Gemini with question + retrieved chunks to produce an answer.
Uses config: gemini_api_key, gemini_model_name.
"""

from typing import List

from app.config import settings

# Lazy-init Gemini model
_model = None


def _get_model():
    global _model
    if _model is None:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(model_name=settings.gemini_model_name)
    return _model


def _build_context(chunks: List[dict]) -> str:
    """Turn chunk dicts (with 'text', 'section_title') into a single context block."""
    parts = []
    for i, c in enumerate(chunks, 1):
        title = c.get("section_title", "")
        text = c.get("text", "")
        parts.append(f"[{i}] {title}\n{text}")
    return "\n\n".join(parts)


# --- Prompt: edit this to tune how the model answers ---
SYSTEM_INSTRUCTIONS = """You answer questions about Sinehan using only the context from Sinehan's documentation below. You always speak *about* Sinehan in the third person (e.g. "Sinehan has...", "He..."). You do not speak as Sinehan (no first person "I").

Rules:
- Only answer questions that are *about Sinehan* (his skills, experience, projects, background). If the question is not about Sinehan (e.g. general knowledge, other people, how something works in general), do not answer. Reply with something like: "This system only answers questions about Sinehan. Your question doesn't seem to be about him."
- Use ONLY information from the context. Do not add general knowledge, assumptions, or guesses about Sinehan.
- If the answer is not in the context, say clearly that it isn't covered in the docs and stop.
- If only part of the question is in the context, answer only that part and say the rest is not in the docs.
- Be specific: name technologies, projects, and outcomes from the context. Avoid vague phrases unless the context is vague.
- Keep answers concise: a short paragraph or a few bullets. Professional, direct tone. No fluff.

Do NOT:
- Answer questions that are not about Sinehan.
- Invent roles, projects, dates, or skills not stated in the context.
- Use first person ("I", "my"). Always refer to Sinehan in the third person.
- Repeat the question back or start with "Based on the context...". Start with the answer."""

# Optional: one short example of desired style (third person, about Sinehan).
EXAMPLE_QUESTION = "What's Sinehan's experience with Python?"
EXAMPLE_ANSWER = "Sinehan uses Python for data pipelines and scripting. In his recent projects he has worked with FastAPI and sentence-transformers for a RAG system. He's comfortable with the usual data stack (pandas, etc.) when the problem fits."


def answer_from_chunks(question: str, chunks: List[dict]) -> str:
    """
    Send question + chunk texts to Gemini; return the model's answer.
    chunks: list of dicts with at least "text" and "section_title" (from vector_store.search).
    """
    if not chunks:
        return "No relevant context was found. Please try rephrasing your question or adding more documents."
    context = _build_context(chunks)
    prompt = f"""{SYSTEM_INSTRUCTIONS}

Example of the kind of answer you give (same style, first person, specific, concise):
Q: {EXAMPLE_QUESTION}
A: {EXAMPLE_ANSWER}

---

Context from Sinehan's docs (use only this):

{context}

---

Question: {question}

Your answer (about Sinehan, third person, from context only; or refuse if the question is not about Sinehan):"""
    model = _get_model()
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": settings.gemini_max_output_tokens,
        },
    )
    try:
        text = response.text if hasattr(response, "text") else None
    except Exception:
        text = None
    if not text:
        return "The model did not return a text response (e.g. content filter)."
    return text.strip()
