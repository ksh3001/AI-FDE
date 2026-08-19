"""Assembles solution-pack-{slug}-{date}.zip.

Built to a temp file on disk (never held fully in memory) via asyncio.to_thread,
then streamed out and deleted by the route. A run that is running,
awaiting_approval, failed, or cancelled still produces a bundle -- whatever
stages have been accepted, with manifest.json marking it partial and listing
what's missing. Only a complete run produces partial: false.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ai_fde.adapters.storage.run_store import RunStore
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.prompts.registry import PromptRegistry


def _slugify(name: str) -> str:
    stem = Path(name).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug or "use-case"


def _validation_markdown(stage_id: str, report: dict[str, Any] | None) -> str:
    if report is None:
        return f"# {stage_id} -- validation unavailable\n\nThe validator did not return a parseable report.\n"
    lines = [
        f"# {stage_id} -- validation report",
        "",
        f"**Overall score:** {report['overall_score']}/100 ({report['verdict']})",
        "",
        "| Criterion | Score | Weight | Comment |",
        "|---|---|---|---|",
    ]
    for c in report.get("criteria", []):
        lines.append(f"| {c['name']} | {c['score']} | {c['weight']} | {c['comment']} |")
    if report.get("issues"):
        lines += ["", "## Issues", ""]
        for issue in report["issues"]:
            lines.append(f"- **{issue['severity']}** ({issue['location']}): {issue['problem']} -- _fix:_ {issue['fix']}")
    return "\n".join(lines) + "\n"


async def build_bundle_zip(
    run_id: str,
    *,
    store: RunStore,
    pipeline: PipelineConfig,
    registry: PromptRegistry,
    inputs_root: Path,
) -> tuple[Path, str]:
    record = await store.get_run(run_id)
    artifacts = await store.list_stage_artifacts(run_id)
    artifacts_by_stage = {a.stage_id: a for a in artifacts}

    attempts_by_stage: dict[str, list[dict[str, Any]]] = {}
    for stage_id in artifacts_by_stage:
        attempts_by_stage[stage_id] = await store.get_stage_attempts(run_id, stage_id) or []

    all_stage_ids = [s.id for s in pipeline.stages]
    missing_stages = [sid for sid in all_stage_ids if sid not in artifacts_by_stage]
    partial = record.status != "complete"

    slug = _slugify(record.use_case.filename) if record.use_case else run_id[:8]
    pack_name = f"solution-pack-{slug}-{date.today().isoformat()}"

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "partial": partial,
        "status": record.status,
        "mode": record.mode,
        "missing_stages": missing_stages,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "use_case": record.use_case.filename if record.use_case else None,
            "evidence": [d.filename for d in record.evidence],
        },
        "stages": [],
    }

    readme_lines = [
        f"# {pack_name}",
        "",
        f"- **run_id:** {run_id}",
        f"- **status:** {record.status}" + (" (partial pack)" if partial else ""),
        f"- **mode:** {record.mode}",
        "",
        "| Stage | Prompt | Score | Verdict | Needs review |",
        "|---|---|---|---|---|",
    ]

    for stage_cfg in pipeline.stages:
        artifact = artifacts_by_stage.get(stage_cfg.id)
        if artifact is None:
            readme_lines.append(f"| {stage_cfg.id} | - | - | missing | - |")
            continue
        readme_lines.append(
            f"| {stage_cfg.id} | {artifact.prompt_id}@{artifact.prompt_version} | "
            f"{artifact.score} | {artifact.verdict} | {artifact.needs_review} |"
        )
        manifest["stages"].append(
            {
                "stage_id": stage_cfg.id,
                "prompt_id": artifact.prompt_id,
                "prompt_version": artifact.prompt_version,
                "score": artifact.score,
                "verdict": artifact.verdict,
                "needs_review": artifact.needs_review,
                "validation_unavailable": artifact.validation_unavailable,
                "repaired": len(attempts_by_stage.get(stage_cfg.id, [])) > 1,
            }
        )

    def _write(tmp_path: Path) -> None:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{pack_name}/00-README.md", "\n".join(readme_lines) + "\n")

            for stage_cfg in pipeline.stages:
                artifact = artifacts_by_stage.get(stage_cfg.id)
                if artifact is None:
                    continue

                zf.writestr(f"{pack_name}/{stage_cfg.artifact_filename}", artifact.content)

                attempts = attempts_by_stage.get(stage_cfg.id, [])
                winner_report = next(
                    (a["validation_report"] for a in attempts if a["content"] == artifact.content),
                    None,
                )
                zf.writestr(
                    f"{pack_name}/validation/{stage_cfg.id}.report.json", json.dumps(winner_report, indent=2)
                )
                zf.writestr(
                    f"{pack_name}/validation/{stage_cfg.id}.report.md",
                    _validation_markdown(stage_cfg.id, winner_report),
                )

                if len(attempts) > 1:
                    for i, attempt in enumerate(attempts, start=1):
                        if attempt["content"] != artifact.content:
                            zf.writestr(
                                f"{pack_name}/attempts/{stage_cfg.id}.attempt-{i}-rejected.md",
                                attempt["content"],
                            )

                diagrams_dir = inputs_root / run_id / stage_cfg.id / "diagrams"
                if diagrams_dir.is_dir():
                    for path in sorted(diagrams_dir.iterdir()):
                        zf.write(path, f"{pack_name}/{stage_cfg.id}/diagrams/{path.name}")

            use_case_dir = inputs_root / run_id / "use_case"
            evidence_dir = inputs_root / run_id / "evidence"
            for directory in (use_case_dir, evidence_dir):
                if directory.is_dir():
                    for path in directory.iterdir():
                        zf.write(path, f"{pack_name}/inputs/{path.name}")

            zf.writestr(f"{pack_name}/manifest.json", json.dumps(manifest, indent=2))

    fd, tmp_path_str = tempfile.mkstemp(suffix=".zip", prefix="ai-fde-bundle-")
    import os

    os.close(fd)
    tmp_path = Path(tmp_path_str)

    await asyncio.to_thread(_write, tmp_path)
    return tmp_path, f"{pack_name}.zip"
