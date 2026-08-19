"""PlantUML text-encoding and the HTTP renderer that turns a `.puml` source
into a PNG via the public plantuml.com server.

No local Java/Docker is assumed to be available -- rendering degrades by
raising, never by hanging: a diagram render must never be allowed to jam a
stage the way an unbounded LLM call can.
"""

from __future__ import annotations

import zlib

import httpx

_PLANTUML_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def _encode6bit(b: int) -> str:
    return _PLANTUML_ALPHABET[b & 0x3F]


def _append3bytes(b1: int, b2: int, b3: int) -> str:
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return _encode6bit(c1) + _encode6bit(c2) + _encode6bit(c3) + _encode6bit(c4)


def encode_plantuml(text: str) -> str:
    """PlantUML's documented text-encoding: UTF-8 -> raw deflate -> PlantUML's
    own 6-bit alphabet (not standard base64) -- see plantuml.com/text-encoding."""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = compressor.compress(text.encode("utf-8")) + compressor.flush()

    out = []
    for i in range(0, len(data), 3):
        chunk = data[i : i + 3]
        b1 = chunk[0]
        b2 = chunk[1] if len(chunk) > 1 else 0
        b3 = chunk[2] if len(chunk) > 2 else 0
        out.append(_append3bytes(b1, b2, b3))
    return "".join(out)


class PlantUMLRenderer:
    def __init__(self, *, base_url: str = "https://www.plantuml.com/plantuml", timeout_seconds: float = 20.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def render_png(self, source: str) -> bytes:
        encoded = encode_plantuml(source)
        response = await self._client.get(f"{self._base_url}/png/{encoded}")
        if response.status_code != 200:
            raise RuntimeError(f"plantuml render failed: HTTP {response.status_code}")
        if not response.content.startswith(b"\x89PNG"):
            raise RuntimeError("plantuml render failed: response was not a PNG")
        return response.content
