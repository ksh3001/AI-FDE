"""The single typed seam every real model call flows through.

Timeout, exponential backoff with jitter on 429/503/timeouts, capped attempts,
never retries 4xx client errors (other than 429). Token and cost accounting per
call -- aggregation per run happens one layer up, in the pipeline node.
"""

from __future__ import annotations

import asyncio
import random

import openai

# USD per 1K tokens, (prompt, completion). Not exhaustive -- unknown models cost $0
# rather than raising, so a misconfigured model id degrades to free cost tracking
# instead of crashing a run.
_PRICING_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-4.1": (0.002, 0.008),
    "gpt-4.1-mini": (0.0004, 0.0016),
    "gpt-5.1": (0.003, 0.012),
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prompt_rate, completion_rate = _PRICING_PER_1K.get(model, (0.0, 0.0))
    return (prompt_tokens / 1000) * prompt_rate + (completion_tokens / 1000) * completion_rate


class OpenAIClient:
    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 90.0,
        max_attempts: int = 4,
        base_url: str | None = None,
    ) -> None:
        self._client = openai.AsyncOpenAI(
            api_key=api_key, timeout=timeout_seconds, base_url=base_url
        )
        self._max_attempts = max_attempts

    async def complete(self, *, model: str, system: str, prompt: str):
        from ai_fde.core.models import LLMResponse, LLMUsage  # local import avoids a cycle

        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=model,
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
            except openai.APIStatusError as exc:
                # Any other 4xx is a client error -- never retried.
                raise

        assert last_error is not None
        raise last_error
