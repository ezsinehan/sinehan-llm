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


def answer_from_chunks(question: str, chunks: List[dict]) -> str:
    """
    Send question + chunk texts to Gemini; return the model's answer.
    chunks: list of dicts with at least "text" and "section_title" (from vector_store.search).
    """
    if not chunks:
        return "No relevant context was found. Please try rephrasing your question or adding more documents."
    context = _build_context(chunks)
    prompt = f"""Context from the knowledge base:

{context}

Question: {question}

Answer (based only on the context above):"""
    model = _get_model()
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2, "max_output_tokens": 1024},
    )
    try:
        text = response.text if hasattr(response, "text") else None
    except Exception:
        text = None
    if not text:
        return "The model did not return a text response (e.g. content filter)."
    return text.strip()
