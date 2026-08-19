"""GET /prompts — makes the prompt library inspectable from the UI."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ai_fde.api.schemas import PromptDetail, PromptLibraryResponse, PromptSummary
from ai_fde.core.prompts.registry import PromptLoadError, extract_title

router = APIRouter(tags=["prompts"])


@router.get("/prompts", response_model=PromptLibraryResponse)
def list_prompts(request: Request) -> PromptLibraryResponse:
    registry = request.app.state.prompt_registry
    pipeline = request.app.state.pipeline_config
    stage_order = {stage.id: stage.order for stage in pipeline.stages}

    def sort_key(front_matter) -> tuple[int, str]:  # noqa: ANN001
        return (stage_order.get(front_matter.stage, len(stage_order)), front_matter.id)

    docs = sorted(registry.list_all(), key=lambda doc: sort_key(doc.front_matter))
    summaries = [
        PromptSummary(
            id=doc.front_matter.id,
            title=extract_title(doc.body),
            version=doc.front_matter.version,
            stage=doc.front_matter.stage,
            model_role=doc.front_matter.model_role,
            output_format=doc.front_matter.output_format,
        )
        for doc in docs
    ]
    return PromptLibraryResponse(prompts=summaries)


@router.get("/prompts/{prompt_id}", response_model=PromptDetail)
def get_prompt(prompt_id: str, request: Request) -> PromptDetail:
    registry = request.app.state.prompt_registry
    try:
        doc = registry.get(prompt_id)
    except PromptLoadError:
        raise HTTPException(status_code=404, detail=f"no prompt with id {prompt_id!r}") from None

    return PromptDetail(
        id=doc.front_matter.id,
        title=extract_title(doc.body),
        version=doc.front_matter.version,
        stage=doc.front_matter.stage,
        model_role=doc.front_matter.model_role,
        output_format=doc.front_matter.output_format,
        body=doc.body,
    )
