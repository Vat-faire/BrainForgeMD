"""Whole-corpus integrity checker for a BrainForgeMD output directory.

Validates the published output contract independently of the code that produced it:
identity uniqueness, chunk/source referential integrity, graph edge endpoints, ordinal
density, front-matter validity and agreement with the manifest, INDEX.md link targets,
and that no chunk text was invented.

Usage: python audit/check_corpus.py <corpus-dir>
Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    corpus = Path(sys.argv[1])
    failures: list[str] = []
    notes: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    manifest = jsonl(corpus / "manifest.jsonl")
    chunks = jsonl(corpus / "chunks.jsonl")
    nodes = jsonl(corpus / "nodes.jsonl")
    edges = jsonl(corpus / "edges.jsonl")
    errors = jsonl(corpus / "errors.jsonl")

    notes.append(f"manifest={len(manifest)} chunks={len(chunks)} nodes={len(nodes)} "
                 f"edges={len(edges)} errors={len(errors)}")

    # ---- identity uniqueness
    source_ids = [m["source_id"] for m in manifest]
    check(len(set(source_ids)) == len(source_ids), "duplicate source_id in manifest")
    source_paths = [m["source_path"] for m in manifest]
    check(len(set(source_paths)) == len(source_paths), "duplicate source_path in manifest")
    output_paths = [m["output_path"] for m in manifest]
    check(len(set(output_paths)) == len(output_paths), "two sources share one output_path")
    chunk_ids = [c["chunk_id"] for c in chunks]
    check(len(set(chunk_ids)) == len(chunk_ids), "duplicate chunk_id")
    node_ids = [n["id"] for n in nodes]
    check(len(set(node_ids)) == len(node_ids), "duplicate node id")

    # ---- chunk -> source integrity
    by_id = {m["source_id"]: m for m in manifest}
    orphans = [c["chunk_id"] for c in chunks if c["source_id"] not in by_id]
    check(not orphans, f"{len(orphans)} orphan chunks reference a source not in the manifest")
    for chunk in chunks:
        parent = by_id.get(chunk["source_id"])
        if parent and chunk["source_path"] != parent["source_path"]:
            failures.append(f"chunk {chunk['chunk_id']} source_path disagrees with its manifest row")
            break
    check(all(c["char_count"] == len(c["text"]) for c in chunks), "char_count disagrees with text")
    check(all(c["text"].strip() for c in chunks), "a chunk is blank")
    check(all(c["approx_tokens"] >= 1 for c in chunks), "approx_tokens below 1")
    check(all(isinstance(c["section_path"], list) for c in chunks), "section_path is not a list")

    # ---- ordinals dense and ordered per source
    per_source: dict[str, list[int]] = {}
    for chunk in chunks:
        per_source.setdefault(chunk["source_id"], []).append(chunk["ordinal"])
    bad = [sid for sid, ordinals in per_source.items() if sorted(ordinals) != list(range(len(ordinals)))]
    check(not bad, f"{len(bad)} sources have non-dense chunk ordinals")

    # ---- manifest chunk_count agrees with chunks.jsonl
    counted = {sid: len(v) for sid, v in per_source.items()}
    mismatch = [m["source_id"] for m in manifest if counted.get(m["source_id"], 0) != m["chunk_count"]]
    check(not mismatch, f"{len(mismatch)} manifest rows disagree with the chunk count")

    # ---- graph endpoints
    ids = set(node_ids)
    dangling = [e["id"] for e in edges if e["source"] not in ids or e["target"] not in ids]
    check(not dangling, f"{len(dangling)} edges point at a node that does not exist")
    doc_nodes = {n["id"] for n in nodes if n["type"] == "document"}
    chunk_nodes = {n["id"] for n in nodes if n["type"] == "chunk"}
    check(doc_nodes == set(source_ids), "document nodes do not match the manifest")
    check(chunk_nodes == set(chunk_ids), "chunk nodes do not match chunks.jsonl")
    allowed = {"contains", "next", "links_to", "references_url"}
    unknown = {e["type"] for e in edges} - allowed
    check(not unknown, f"speculative or unknown edge types present: {unknown}")
    contains = [e for e in edges if e["type"] == "contains"]
    check(len(contains) == len(chunks), "every chunk needs exactly one contains edge")

    # ---- documents on disk match the manifest exactly
    on_disk = {p.relative_to(corpus).as_posix() for p in (corpus / "documents").rglob("*.md")}
    check(on_disk == set(output_paths),
          f"documents/ and manifest disagree: {len(on_disk - set(output_paths))} orphan file(s), "
          f"{len(set(output_paths) - on_disk)} missing file(s)")

    # ---- front matter present, parseable, and agreeing with the manifest
    try:
        import yaml
    except ImportError:
        yaml = None
        notes.append("pyyaml absent: front matter parsed structurally only")
    checked_bodies = 0
    for row in manifest:
        path = corpus / row["output_path"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            failures.append(f"{row['output_path']} has no front matter")
            break
        head, _, body = text[4:].partition("\n---\n\n")
        if yaml is not None:
            try:
                meta = yaml.safe_load(head)
            except Exception as exc:
                failures.append(f"{row['output_path']} front matter is not valid YAML: {exc}")
                break
            if meta.get("source_id") != row["source_id"] or meta.get("sha256") != row["sha256"]:
                failures.append(f"{row['output_path']} front matter disagrees with the manifest")
                break
            if meta.get("source_path") != row["source_path"]:
                failures.append(f"{row['output_path']} front matter source_path disagrees")
                break
        # every chunk's text must actually come from this document's body
        for chunk in chunks:
            if chunk["source_id"] == row["source_id"] and chunk["text"] not in body:
                failures.append(
                    f"chunk {chunk['chunk_id']} text is not present in {row['output_path']}"
                )
                break
        checked_bodies += 1
    notes.append(f"verified front matter and chunk provenance for {checked_bodies} documents")

    # ---- sha256 shape
    check(all(re.fullmatch(r"[0-9a-f]{64}", m["sha256"] or "") for m in manifest),
          "a manifest sha256 is not a 64-character hex digest")

    # ---- INDEX.md links resolve
    index = (corpus / "INDEX.md")
    if index.is_file():
        targets = re.findall(r"\]\(([^)\s]*)\)", index.read_text(encoding="utf-8"))
        broken = [t for t in targets if not (corpus / unquote(t)).is_file()]
        check(not broken, f"{len(broken)} INDEX.md links do not resolve: {broken[:3]}")
        check(len(targets) == len(manifest), "INDEX.md does not list every document")

    for note in notes:
        print(f"  info: {note}")
    if failures:
        print(f"\nFAILED {len(failures)} corpus integrity check(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nAll corpus integrity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
