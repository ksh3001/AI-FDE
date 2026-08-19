"""Azure OpenAI adapter behind the same LLMClient port as OpenAIClient.

Azure addresses models by *deployment name*, not model id, so `model` as passed
in by the pipeline nodes (settings.generator_model / settings.validator_model)
is translated through `deployment_map` before the call. Retry/backoff and cost
accounting mirror OpenAIClient exactly -- the two adapters should behave
identically from the pipeline's point of view.
"""

from __future__ import annotations

import asyncio
import random

import openai

from ai_fde.adapters.llm.openai_client import _estimate_cost


class AzureOpenAIClient:
    def __init__(
        self,
        *,
        api_key: str,
        azure_endpoint: str,
        api_version: str,
        deployment_map: dict[str, str] | None = None,
        timeout_seconds: float = 90.0,
        max_attempts: int = 4,
    ) -> None:
        self._client = openai.AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            timeout=timeout_seconds,
        )
        self._deployment_map = deployment_map or {}
        self._max_attempts = max_attempts

    def _deployment_for(self, model: str) -> str:
        return self._deployment_map.get(model, model)

    async def complete(self, *, model: str, system: str, prompt: str):
        from ai_fde.core.models import LLMResponse, LLMUsage  # local import avoids a cycle

        deployment = self._deployment_for(model)

        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=deployment,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                )
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0
                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=model,
                    usage=LLMUsage(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        cost_usd=_estimate_cost(model, prompt_tokens, completion_tokens),
                    ),
                )
            except (openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError) as exc:
                last_error = exc
                if attempt == self._max_attempts:
                    break
                backoff = min(2**attempt, 30) + random.uniform(0, 1)
                await asyncio.sleep(backoff)
            except openai.APIStatusError:
                # Any other 4xx is a client error -- never retried.
                raise

        assert last_error is not None
        raise last_error
