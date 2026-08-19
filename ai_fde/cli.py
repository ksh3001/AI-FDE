"""`ai-fde run <use-case.pptx>` — the CLI entry point.

Milestone 1 only needs this importable and able to prove the prompt library and
pipeline config load cleanly; the actual generate/validate/repair loop driven
from the CLI is Milestone 3.
"""

from __future__ import annotations

import argparse
import sys

from ai_fde.core.pipeline.config import PipelineConfig, validate_pipeline_bindings
from ai_fde.core.prompts.registry import PromptLoadError, PromptRegistry
from ai_fde.core.settings import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-fde")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the pipeline against a use case document")
    run_parser.add_argument("use_case", help="Path to the use case file (.pptx, .pdf, or .md)")

    args = parser.parse_args(argv)

    if args.command == "run":
        settings = Settings()
        try:
            registry = PromptRegistry(settings.prompt_library_dir)
            pipeline = PipelineConfig.load(settings.pipeline_config_path)
            validate_pipeline_bindings(pipeline, registry)
        except (PromptLoadError, FileNotFoundError, ValueError) as exc:
            print(f"ai-fde: prompt library / pipeline config invalid: {exc}", file=sys.stderr)
            return 1

        print(
            f"Prompt library and pipeline config OK "
            f"({len(registry.list_all())} prompts, {len(pipeline.stages)} stages).",
        )
        print(
            f"ai-fde run {args.use_case}: pipeline execution ships in Milestone 3.",
            file=sys.stderr,
        )
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
