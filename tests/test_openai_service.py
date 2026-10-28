from types import SimpleNamespace

import pytest

from backend.services.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_real_completion_records_usage_and_finish_reason(monkeypatch):
    service = OpenAIService(api_key="sk-test")
    expected = SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content="```python\npass\n```"),
            )
        ],
        model="gpt-4o-test",
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    class Completions:
        async def create(self, **kwargs):
            assert kwargs["max_completion_tokens"] > 0
            assert kwargs["temperature"] == 0.0
            return expected

    service.client.chat.completions = Completions()
    result = await service.generate_solution("prompt")

    assert result["modo"] == "openai_api_oficial"
    assert result["motivo_finalizacion"] == "stop"
    assert result["uso_tokens"] == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


@pytest.mark.asyncio
async def test_missing_api_key_fails_instead_of_simulating(monkeypatch):
    monkeypatch.setattr("backend.services.openai_service.OPENAI_API_KEY", "")
    service = OpenAIService()

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        await service.generate_solution("prompt")
