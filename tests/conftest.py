from __future__ import annotations

from pathlib import Path

import pytest

from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.prompts.registry import PromptRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _no_real_llm_provider_in_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings() reads the developer's real .env file by default (env_file=".env"),
    so without this a locally-configured LLM_PROVIDER=openai/azure_openai would
    make the test suite fire real, billed API calls. Force "fake" for every test;
    individual tests may still override it explicitly if they need to."""
    monkeypatch.setenv("LLM_PROVIDER", "fake")


@pytest.fixture(scope="session")
def prompt_registry() -> PromptRegistry:
    return PromptRegistry(REPO_ROOT / "prompts")


@pytest.fixture(scope="session")
def pipeline_config() -> PipelineConfig:
    return PipelineConfig.load(REPO_ROOT / "config" / "pipeline.yaml")
