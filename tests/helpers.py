"""Test-only doubles. Not part of the shipped adapters."""

from __future__ import annotations

from ai_fde.core.models import LLMResponse, LLMUsage


class ScriptedLLMClient:
    """Returns responses from a fixed script, in call order, regardless of prompt
    content. Used to pin exact routing behaviour in graph tests -- the demo
    pipeline uses ai_fde.adapters.llm.fake.FakeLLMClient instead, which infers
    its response from prompt content rather than call order.
    """

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, str]] = []

    async def complete(self, *, model: str, system: str, prompt: str) -> LLMResponse:
        self.calls.append({"model": model, "system": system, "prompt": prompt})
        if not self._responses:
            raise AssertionError(f"ScriptedLLMClient ran out of scripted responses at call {len(self.calls)}")
        content = self._responses.pop(0)
        return LLMResponse(
            content=content,
            model=model,
            usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2, cost_usd=0.0),
        )
