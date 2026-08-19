from __future__ import annotations

import pytest

from ai_fde.adapters.diagrams.plantuml_renderer import PlantUMLRenderer, encode_plantuml

# Golden value: encode_plantuml() of this exact string, confirmed live against
# https://www.plantuml.com/plantuml/png/<value> (HTTP 200, real PNG) before
# being pinned here as a regression fixture -- tests never hit the network.
_REFERENCE_TEXT = "@startuml\nAlice -> Bob: hello\n@enduml"
_REFERENCE_ENCODED = "SoWkIImgAStDuNBCoKnELT2rKt3AJx9Io4ZDoSddSaZDIm7A0G00"


def test_encode_plantuml_matches_known_good_encoding() -> None:
    assert encode_plantuml(_REFERENCE_TEXT) == _REFERENCE_ENCODED


def test_encode_plantuml_is_deterministic() -> None:
    assert encode_plantuml("@startuml\nA -> B\n@enduml") == encode_plantuml("@startuml\nA -> B\n@enduml")


def test_encode_plantuml_uses_only_the_plantuml_alphabet() -> None:
    alphabet = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_")
    encoded = encode_plantuml("@startuml\nrectangle X\n@enduml")
    assert set(encoded) <= alphabet


class _FakeResponse:
    def __init__(self, status_code: int, content: bytes) -> None:
        self.status_code = status_code
        self.content = content


class _FakeHttpClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.requested_url: str | None = None

    async def get(self, url: str) -> _FakeResponse:
        self.requested_url = url
        return self._response


async def test_render_png_returns_bytes_on_success() -> None:
    renderer = PlantUMLRenderer()
    renderer._client = _FakeHttpClient(_FakeResponse(200, b"\x89PNG\r\n\x1a\nrest-of-file"))  # type: ignore[assignment]

    png = await renderer.render_png("@startuml\nA -> B\n@enduml")

    assert png.startswith(b"\x89PNG")
    assert renderer._client.requested_url.endswith(encode_plantuml("@startuml\nA -> B\n@enduml"))  # type: ignore[union-attr]


async def test_render_png_raises_on_non_200() -> None:
    renderer = PlantUMLRenderer()
    renderer._client = _FakeHttpClient(_FakeResponse(400, b"error"))  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="HTTP 400"):
        await renderer.render_png("@startuml\nA -> B\n@enduml")


async def test_render_png_raises_on_non_png_response() -> None:
    renderer = PlantUMLRenderer()
    renderer._client = _FakeHttpClient(_FakeResponse(200, b"<html>not a png</html>"))  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="not a PNG"):
        await renderer.render_png("@startuml\nA -> B\n@enduml")
