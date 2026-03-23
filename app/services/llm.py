"""
LLM service: calls a local Ollama model via its OpenAI-compatible API.
URL and model are set in .env (OLLAMA_URL, OLLAMA_MODEL_NAME).
"""

from typing import List

from openai import OpenAI

from app.config import settings


def _get_client() -> OpenAI:
    return OpenAI(base_url=f"{settings.ollama_url}/v1", api_key="ollama")


def _build_context(chunks: List[dict]) -> str:
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

EXAMPLE_QUESTION = "What's Sinehan's experience with Python?"
EXAMPLE_ANSWER = "Sinehan uses Python for data pipelines and scripting. In his recent projects he has worked with FastAPI and sentence-transformers for a RAG system. He's comfortable with the usual data stack (pandas, etc.) when the problem fits."


def answer_from_chunks(question: str, chunks: List[dict]) -> str:
    """
    Send question + chunk texts to Ollama; return the model's answer.
    chunks: list of dicts with at least "text" and "section_title".
    """
    if not chunks:
        return "No relevant context was found. Please try rephrasing your question or adding more documents."

    context = _build_context(chunks)
    user_message = f"""Example of the kind of answer you give (same style, third person, specific, concise):
Q: {EXAMPLE_QUESTION}
A: {EXAMPLE_ANSWER}

---

Context from Sinehan's docs (use only this):

{context}

---

Question: {question}

Your answer (about Sinehan, third person, from context only; or refuse if the question is not about Sinehan):"""

    client = _get_client()
    response = client.chat.completions.create(
        model=settings.ollama_model_name,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=settings.ollama_max_tokens,
    )
    text = response.choices[0].message.content
    return text.strip() if text else "The model did not return a response."
