# tests/test_llm.py
"""Automated tests for app.services.llm (step 8). Mocks Ollama API."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.services import llm


def test_build_context_format():
    """_build_context produces numbered sections with section_title and text."""
    chunks = [
        {"section_title": "Intro", "text": "First paragraph."},
        {"section_title": "Details", "text": "Second paragraph."},
    ]
    out = llm._build_context(chunks)
    assert "[1] Intro" in out
    assert "First paragraph." in out
    assert "[2] Details" in out
    assert "Second paragraph." in out
    print("[PASS] _build_context format")


def test_answer_from_chunks_empty():
    """answer_from_chunks with no chunks returns fallback message."""
    result = llm.answer_from_chunks("Question?", [])
    assert "No relevant context" in result or "rephrasing" in result.lower()
    print("[PASS] answer_from_chunks empty chunks returns fallback")


def _mock_chat_response(text):
    """Create a mock OpenAI chat completion response."""
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def test_answer_from_chunks_returns_model_text():
    """answer_from_chunks with mocked model returns response text."""
    chunks = [
        {"section_title": "S", "text": "Some context."},
    ]
    with patch.object(llm, "_get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_chat_response("The answer is 42.")
        mock_get.return_value = mock_client
        result = llm.answer_from_chunks("What is it?", chunks)
    assert result == "The answer is 42."
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
    user_msg = messages[-1]["content"]
    assert "Some context." in user_msg
    assert "What is it?" in user_msg
    print("[PASS] answer_from_chunks returns model text and passes prompt")


def test_answer_from_chunks_handles_empty_response():
    """answer_from_chunks when model returns no text returns fallback."""
    chunks = [{"section_title": "S", "text": "x"}]
    with patch.object(llm, "_get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_chat_response("")
        mock_get.return_value = mock_client
        result = llm.answer_from_chunks("Q?", chunks)
    assert "did not return" in result
    print("[PASS] answer_from_chunks handles empty/blocked response")


def run_all():
    test_build_context_format()
    test_answer_from_chunks_empty()
    test_answer_from_chunks_returns_model_text()
    test_answer_from_chunks_handles_empty_response()
    print("\n" + "=" * 50)
    print("All LLM tests passed.")
    print("=" * 50)


if __name__ == "__main__":
    run_all()
