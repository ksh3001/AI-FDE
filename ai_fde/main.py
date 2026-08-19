"""FastAPI app factory.

The prompt library and pipeline config are loaded and validated synchronously,
at create_app() time -- not inside the async lifespan -- so a malformed prompt
or a pipeline.yaml referencing a missing prompt fails loudly before the app can
ever serve a request, importable or not.

The checkpointer (needs an open event loop) and the run store are set up in the
async lifespan instead, along with a crash-recovery pass: any run left
"queued"/"parsing"/"running" when the process last stopped could not possibly
still be executing, so it's marked failed with a reason that tells the user to
retry rather than silently hanging forever.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_fde.adapters.diagrams import PlantUMLRenderer
from ai_fde.adapters.llm import AzureOpenAIClient, FakeLLMClient, OpenAIClient
from ai_fde.adapters.storage import LocalFilesystemArtifactStore
from ai_fde.adapters.storage.run_store import RunStore
from ai_fde.api.routes.prompts import router as prompts_router
from ai_fde.api.routes.runs import router as runs_router
from ai_fde.core.pipeline.config import PipelineConfig, validate_pipeline_bindings
from ai_fde.core.pipeline.runner import PipelineRunner
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.settings import Settings


def _build_llm_client(settings: Settings):
    if settings.llm_provider == "azure_openai":
        return AzureOpenAIClient(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            deployment_map={
                settings.generator_model: settings.generator_deployment or settings.generator_model,
                settings.validator_model: settings.validator_deployment or settings.validator_model,
            },
        )
    if settings.llm_provider == "openai":
        return OpenAIClient(api_key=settings.openai_api_key)
    return FakeLLMClient()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings: Settings = app.state.settings

    settings.checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(settings.checkpoint_db_path)) as checkpointer:
        run_store = await RunStore.create(settings.artifact_store_dir / "runs.sqlite3")
        artifact_store = LocalFilesystemArtifactStore(settings.artifact_store_dir)
        llm_client = _build_llm_client(settings)
        diagram_renderer = PlantUMLRenderer()

        runner = PipelineRunner(
            store=run_store,
            artifact_store=artifact_store,
            llm_client=llm_client,
            diagram_renderer=diagram_renderer,
            registry=app.state.prompt_registry,
            pipeline=app.state.pipeline_config,
            checkpointer=checkpointer,
            settings=settings,
            inputs_root=settings.artifact_store_dir,
        )

        # Crash recovery: nothing can still be "running" from a previous process.
        for record in await run_store.list_runs_by_status("queued", "parsing", "running"):
            await run_store.force_status(
                record.run_id, "failed", failure_reason="server restarted while this run was in progress"
            )

        app.state.run_store = run_store
        app.state.artifact_store = artifact_store
        app.state.runner = runner

        try:
            yield
        finally:
            await run_store.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    prompt_registry = PromptRegistry(settings.prompt_library_dir)
    pipeline_config = PipelineConfig.load(settings.pipeline_config_path)
    validate_pipeline_bindings(pipeline_config, prompt_registry)

    app = FastAPI(title="AI_FDE", version="0.1.0", lifespan=_lifespan)
    app.state.settings = settings
    app.state.prompt_registry = prompt_registry
    app.state.pipeline_config = pipeline_config
    app.state.background_tasks = set()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(prompts_router)
    app.include_router(runs_router)

    return app


app = create_app()
