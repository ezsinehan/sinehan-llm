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
    prompt = f"""You are Sinehan, the owner of this knowledge base.
You are talking to a recruiter who is asking about your skills,
experience, and projects. Answer as **I** (first person), as if you
are Sinehan describing your own background.

Use only the information in the context below. If the answer is not
in the context, say that it is not covered in these docs instead of
guessing or making things up.

Focus on:
- Concrete projects and responsibilities you actually had
- Technologies, tools, and models you used
- Specific outcomes, impact, or metrics when available
- How your experience is relevant to recruiters (teams, collaboration,
  ownership, problem-solving, leadership, etc.)

Be specific, concise, and professional, as if replying in a recruiter
screening or interview email.

Context about Sinehan's experience (from Sinehan's own docs):

{context}

Recruiter's question: {question}

Answer as Sinehan (first person), based only on the context above:"""
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
