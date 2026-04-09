"""
LLM service: calls a local Ollama model via its OpenAI-compatible API.
URL and model are set in .env (OLLAMA_URL, OLLAMA_MODEL_NAME).
Prompting is configured in prompts.yaml at the project root.
"""

from pathlib import Path
from typing import List

import yaml
from openai import OpenAI

from app.config import settings

PROMPTS_PATH = Path(__file__).resolve().parent.parent.parent / "prompts.yaml"


def _load_prompts() -> dict:
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_client() -> OpenAI:
    return OpenAI(base_url=f"{settings.ollama_url}/v1", api_key="ollama")


def _build_context(chunks: List[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        title = c.get("section_title", "")
        text = c.get("text", "")
        parts.append(f"[{i}] {title}\n{text}")
    return "\n\n".join(parts)


def _build_messages(question: str, chunks: List[dict]) -> list:
    prompts = _load_prompts()
    context = _build_context(chunks)
    return [
        {"role": "system", "content": prompts["system"].strip()},
        {"role": "user", "content": prompts["user"].format(context=context, question=question).strip()},
    ]


def answer_from_chunks(question: str, chunks: List[dict]) -> str:
    if not chunks:
        return _load_prompts().get("no_context", "No relevant context found.")

    prompts = _load_prompts()
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.ollama_model_name,
        messages=_build_messages(question, chunks),
        temperature=prompts.get("temperature", 0.2),
        max_tokens=settings.ollama_max_tokens,
    )
    text = response.choices[0].message.content
    return text.strip() if text else "The model did not return a response."


def stream_answer_from_chunks(question: str, chunks: List[dict]):
    if not chunks:
        yield _load_prompts().get("no_context", "No relevant context found.")
        return

    prompts = _load_prompts()
    client = _get_client()
    stream = client.chat.completions.create(
        model=settings.ollama_model_name,
        messages=_build_messages(question, chunks),
        temperature=prompts.get("temperature", 0.2),
        max_tokens=settings.ollama_max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
