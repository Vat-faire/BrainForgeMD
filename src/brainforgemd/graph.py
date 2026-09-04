from __future__ import annotations

import re
from itertools import pairwise
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from .models import Chunk
from .utils import stable_id

_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+")


def _safe_urlparse(value: str):
    """urlparse raises ValueError on things like an unterminated IPv6 literal
    (``http://[nothost/page``). One such link in one document used to abort the
    entire corpus build, so parse failures are treated as 'not a URL'."""
    try:
        return urlparse(value)
    except ValueError:
        return None


def build_graph(
    documents: list[dict[str, Any]], chunks: list[Chunk]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    doc_by_source = {doc["source_path"]: doc for doc in documents}

    for doc in documents:
        nodes.append(
            {
                "id": doc["source_id"],
                "type": "document",
                "source_path": doc["source_path"],
                "title": doc["title"],
                "sha256": doc["sha256"],
            }
        )

    chunks_by_source: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        chunks_by_source.setdefault(chunk.source_id, []).append(chunk)
        nodes.append(
            {
                "id": chunk.chunk_id,
                "type": "chunk",
                "source_id": chunk.source_id,
                "source_path": chunk.source_path,
                "ordinal": chunk.ordinal,
                "section_path": chunk.section_path,
                "sha256": chunk.sha256,
            }
        )
        edges.append(
            {
                "id": stable_id("edge", chunk.source_id, chunk.chunk_id, "contains"),
                "source": chunk.source_id,
                "target": chunk.chunk_id,
                "type": "contains",
            }
        )

    for source_chunks in chunks_by_source.values():
        ordered = sorted(source_chunks, key=lambda c: c.ordinal)
        for left, right in pairwise(ordered):
            edges.append(
                {
                    "id": stable_id("edge", left.chunk_id, right.chunk_id, "next"),
                    "source": left.chunk_id,
                    "target": right.chunk_id,
                    "type": "next",
                }
            )

    url_nodes: dict[str, str] = {}
    for doc in documents:
        markdown = doc.get("markdown", "")
        explicit_links = [m.group(1).strip().strip("<>") for m in _MD_LINK_RE.finditer(markdown)]
        urls = set(_URL_RE.findall(markdown))
        for link in explicit_links:
            parsed = _safe_urlparse(link)
            if parsed is not None and parsed.scheme in {"http", "https"}:
                urls.add(link)
        for url in sorted(urls):
            url_id = url_nodes.setdefault(url, stable_id("url", url))
            edges.append(
                {
                    "id": stable_id("edge", doc["source_id"], url_id, "references_url"),
                    "source": doc["source_id"],
                    "target": url_id,
                    "type": "references_url",
                }
            )

        base = PurePosixPath(doc["source_path"]).parent
        for link in explicit_links:
            parsed = _safe_urlparse(link)
            if parsed is None or parsed.scheme or link.startswith("#"):
                continue
            candidate = str((base / unquote(parsed.path)).as_posix())
            # normalize simple ./ and ../ path components
            parts: list[str] = []
            for part in PurePosixPath(candidate).parts:
                if part in {"", "."}:
                    continue
                if part == "..":
                    if parts:
                        parts.pop()
                else:
                    parts.append(part)
            normalized = "/".join(parts)
            target = doc_by_source.get(normalized)
            if target:
                edges.append(
                    {
                        "id": stable_id("edge", doc["source_id"], target["source_id"], "links_to"),
                        "source": doc["source_id"],
                        "target": target["source_id"],
                        "type": "links_to",
                    }
                )

    for url, node_id in sorted(url_nodes.items()):
        nodes.append({"id": node_id, "type": "url", "url": url})

    nodes.sort(key=lambda n: n["id"])
    edges.sort(key=lambda e: e["id"])
    return nodes, edges
