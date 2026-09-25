"""Unit tests for live API adapter and API judge integrations."""

from unittest.mock import MagicMock, patch
import pytest
from agentguard.integrations.api_adapter import APIModelAdapter
from agentguard.integrations.base import ModelResponse
from agentguard.judges.api_judge import APIJudge
from agentguard.judges.base import Rubric


def test_api_adapter_initialization():
    adapter_openai = APIModelAdapter(provider="openai", model_id="gpt-4o", api_key="test-key")
    assert adapter_openai.provider == "openai"
    assert adapter_openai.base_url == "https://api.openai.com/v1"
    assert adapter_openai.api_key == "test-key"

    adapter_anthropic = APIModelAdapter(provider="anthropic", model_id="claude-3-5-sonnet", api_key="anth-key")
    assert adapter_anthropic.provider == "anthropic"
    assert adapter_anthropic.base_url == "https://api.anthropic.com/v1"

    adapter_gemini = APIModelAdapter(provider="gemini", model_id="gemini-1.5-pro", api_key="gem-key")
    assert adapter_gemini.provider == "gemini"
    assert "googleapis.com" in adapter_gemini.base_url


def test_api_adapter_openai_mocked_http():
    mock_response_payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Order ORD-123 is delivered.",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30,
        },
    }

    adapter = APIModelAdapter(provider="openai", model_id="gpt-4o-mini", api_key="dummy")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_cm = MagicMock()
        mock_cm.read.return_value = json_bytes(mock_response_payload)
        mock_cm.__enter__.return_value = mock_cm
        mock_urlopen.return_value = mock_cm

        resp = adapter.generate("Where is order ORD-123?")
        assert resp.content == "Order ORD-123 is delivered."
        assert resp.prompt_tokens == 20
        assert resp.completion_tokens == 10
        assert resp.total_tokens == 30
        assert resp.retries == 0


def test_api_judge_multi_sample_consensus(sample_rubric: Rubric):
    mock_adapter = MagicMock()
    # Mock judge returning valid structured JSON with reasoning
    judge_json = '{"reasoning": "Accurate and polite response complying with rubric.", "score": 4.5, "confidence": 0.90}'
    mock_adapter.generate.return_value = ModelResponse(content=judge_json)

    judge = APIJudge(model_adapter=mock_adapter, rubric=sample_rubric, samples=2)
    result = judge.evaluate(
        prompt="Where is my order?",
        response="Your order ORD-100 is delivered.",
        ground_truth="Order ORD-100 is delivered.",
    )

    assert result.score == 4.5
    assert result.confidence == 0.90
    assert result.is_passing is True
    assert "Accurate and polite" in result.rationale
    assert result.metadata.get("samples") == 2


def json_bytes(obj: dict) -> bytes:
    import json
    return json.dumps(obj).encode("utf-8")
