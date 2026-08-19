"""Env-driven config. Never hardcode model ids or thresholds in logic — read this instead."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""

    # Azure OpenAI. Deployment names default to generator_model/validator_model
    # when *_deployment is unset -- set them explicitly if your Azure deployment
    # names differ from the model ids (they usually do).
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-10-21"
    generator_deployment: str = ""
    validator_deployment: str = ""

    # "fake" needs no API key and drives the demo pipeline deterministically;
    # "openai" uses the plain OpenAI adapter; "azure_openai" uses Azure OpenAI.
    # Defaults to "fake" so the app runs out of the box -- flip this once
    # credentials are set.
    llm_provider: str = "fake"

    generator_model: str = "gpt-4.1"
    validator_model: str = "gpt-5.1"
    validation_threshold: int = Field(default=60, ge=0, le=100)
    # 1 (default) = the spec's normal generate -> validate -> repair-once loop.
    # 0 = skip repair entirely; a stage that fails validation is accepted as-is
    # and flagged needs_review rather than spending a second generator call on
    # it. The repair node/code always stays -- this only gates whether the
    # graph ever routes to it. No value above 1 is meaningful: the graph can
    # only make a single repair pass per stage.
    max_repair_attempts: int = Field(default=1, ge=0, le=1)

    prompt_library_dir: Path = Path("prompts")
    pipeline_config_path: Path = Path("config/pipeline.yaml")
    artifact_store_dir: Path = Path("runs")
    checkpoint_db_path: Path = Path("runs/checkpoints.sqlite3")

    host: str = "0.0.0.0"
    port: int = 8000
