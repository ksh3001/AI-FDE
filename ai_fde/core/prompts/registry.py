"""Loads the prompt library from disk once, validates it, and renders by id.

Two independent substitution passes happen at render time, never at edit time —
the on-disk prompt bodies inherited from the original library are never rewritten:

1. Jinja2 `{{ }}` — used by prompts authored fresh for this platform (e.g.
   repair/repair.md's `{{ original_prompt }}`, `{{ failed_draft }}`, ...).
2. Single-brace domain tokens (`{DOMAIN}`, `{SYSTEM}`, `{AUTHORITY_MATRIX}`, ...) —
   inherited verbatim from the original library's placeholder-substitution
   convention (see docs/PROMPT-LIBRARY.md). These are inert to Jinja2 and are
   resolved separately via literal, allow-listed token replacement so an
   unrelated `{...}` in a prompt body (e.g. templates/10_adr_template.md's
   `{NUMBER}` / `{TITLE}`, which the *generator model* fills in, not the
   registry) is left untouched rather than blindly `.format()`-ed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, StrictUndefined

from ai_fde.core.prompts.models import PromptFrontMatter

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)\Z", re.DOTALL)
_DOMAIN_TOKEN_RE = re.compile(r"\{([A-Z][A-Z_]*)\}")

#: Every stage prompt titles itself "# Prompt NN — Title" (see Prompts/stages/*.md).
#: Shared here so both FakeLLMClient (labelling demo output) and the /prompts API
#: (labelling library cards) read the same title without hand-maintaining it twice.
_TITLE_RE = re.compile(r"(?m)^#[ \t]+Prompt\s+\S+\s+[—-]\s+(.+?)[ \t]*$")


def extract_title(body: str) -> str | None:
    match = _TITLE_RE.search(body)
    return match.group(1).strip() if match else None


class PromptLoadError(RuntimeError):
    """A prompt file is missing, malformed, or fails front-matter validation.

    Raised only at registry construction time (startup) — never at request time.
    """


@dataclass(frozen=True)
class PromptDocument:
    front_matter: PromptFrontMatter
    body: str
    path: Path


#: Only these subdirectories are loaded as pipeline prompts, matching the build
#: spec's declared tree exactly. Anything else under the prompt library root
#: (e.g. prompts/_reference/, holding the original un-front-mattered library)
#: is deliberately not scanned, so raw reference material can sit alongside the
#: wrapped prompts without the registry choking on files that carry no
#: front-matter by design.
_LOADED_SUBDIRS = ("_shared", "stages", "validators", "repair")


class PromptRegistry:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._by_id: dict[str, PromptDocument] = {}
        self._jinja = Environment(undefined=StrictUndefined, autoescape=False)
        self._load()

    def _load(self) -> None:
        if not self._root.is_dir():
            raise PromptLoadError(f"prompt directory not found: {self._root}")

        paths = sorted(
            path
            for subdir in _LOADED_SUBDIRS
            for path in (self._root / subdir).rglob("*.md")
        )
        if not paths:
            raise PromptLoadError(
                f"no prompt files found under {self._root} in {_LOADED_SUBDIRS}"
            )

        errors: list[str] = []
        for path in paths:
            try:
                doc = self._load_file(path)
            except Exception as exc:  # noqa: BLE001 - collect every error before failing
                errors.append(f"{path}: {exc}")
                continue

            if doc.front_matter.id in self._by_id:
                other = self._by_id[doc.front_matter.id].path
                errors.append(
                    f"{path}: duplicate prompt id {doc.front_matter.id!r} "
                    f"(already loaded from {other})"
                )
                continue

            self._by_id[doc.front_matter.id] = doc

        if errors:
            joined = "\n".join(f"  - {e}" for e in errors)
            raise PromptLoadError(f"failed to load prompt library:\n{joined}")

    def _load_file(self, path: Path) -> PromptDocument:
        raw = path.read_text(encoding="utf-8")
        match = _FRONT_MATTER_RE.match(raw)
        if not match:
            raise ValueError("missing YAML front-matter block (file must start with '---')")

        raw_front_matter, body = match.groups()
        try:
            data = yaml.safe_load(raw_front_matter) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid YAML front-matter: {exc}") from exc

        front_matter = PromptFrontMatter.model_validate(data)
        return PromptDocument(front_matter=front_matter, body=body.strip("\n"), path=path)

    def get(self, prompt_id: str) -> PromptDocument:
        try:
            return self._by_id[prompt_id]
        except KeyError:
            raise PromptLoadError(f"unknown prompt id: {prompt_id!r}") from None

    def list_all(self) -> list[PromptDocument]:
        return sorted(self._by_id.values(), key=lambda d: d.front_matter.id)

    def render(
        self,
        prompt_id: str,
        *,
        jinja_context: dict[str, str] | None = None,
        domain_config: dict[str, str] | None = None,
    ) -> str:
        doc = self.get(prompt_id)
        text = doc.body

        if jinja_context:
            text = self._jinja.from_string(text).render(**jinja_context)

        if domain_config:

            def _substitute(m: re.Match[str]) -> str:
                return domain_config.get(m.group(1), m.group(0))

            text = _DOMAIN_TOKEN_RE.sub(_substitute, text)

        return text
