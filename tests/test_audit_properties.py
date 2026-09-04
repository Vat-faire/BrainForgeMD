"""Property-based tests for the invariants BrainForgeMD's output contract promises.

These are deliberately written against the documented contract rather than against the
implementation, so they can fail on inputs nobody thought to enumerate. Hypothesis is
optional; without it the module is skipped rather than silently passing.
"""

from __future__ import annotations

import json
import string
import zipfile
from pathlib import Path

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from brainforgemd.archive import ArchiveLimits, extract_archive  # noqa: E402
from brainforgemd.chunking import ChunkSettings, chunk_markdown  # noqa: E402
from brainforgemd.frontmatter import render_front_matter  # noqa: E402
from brainforgemd.pipeline import Pipeline, PipelineSettings  # noqa: E402
from brainforgemd.utils import (  # noqa: E402
    clean_text,
    decode_text,
    output_filename,
    safe_output_path,
)

SLOW = settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)

# Names that are legal on every host we target.
SAFE_NAME_CHARS = string.ascii_letters + string.digits + " .-_()[]&+=~é日🎉"
safe_names = st.text(alphabet=SAFE_NAME_CHARS, min_size=1, max_size=40).filter(
    lambda s: s.strip(" .") != "" and s not in {".", ".."} and "\x00" not in s
)


# --------------------------------------------------------------- chunking
@given(
    text=st.text(max_size=4000),
    target=st.integers(min_value=500, max_value=4000),
    ratio=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=200, deadline=None)
def test_chunking_invariants(text: str, target: int, ratio: int) -> None:
    overlap = target * ratio // 100
    chunks = chunk_markdown(text, "src_1", "a.md", ChunkSettings(target, overlap, 200))

    assert len({c.chunk_id for c in chunks}) == len(chunks), "chunk ids must be unique"
    assert [c.ordinal for c in chunks] == list(range(len(chunks))), "ordinals must be dense and ordered"
    for chunk in chunks:
        assert chunk.text.strip(), "no chunk may be blank"
        assert chunk.char_count == len(chunk.text)
        assert chunk.approx_tokens >= 1
        assert chunk.source_id == "src_1"
        assert chunk.source_path == "a.md"
    if not text.strip():
        assert chunks == []


@given(
    text=st.text(max_size=3000),
    target=st.integers(min_value=500, max_value=3000),
)
@settings(max_examples=100, deadline=None)
def test_chunking_is_deterministic(text: str, target: int) -> None:
    settings_obj = ChunkSettings(target, target // 10, 200)
    first = chunk_markdown(text, "src_1", "a.md", settings_obj)
    second = chunk_markdown(text, "src_1", "a.md", settings_obj)
    assert [c.to_dict() for c in first] == [c.to_dict() for c in second]


@given(text=st.text(max_size=6000), target=st.integers(min_value=500, max_value=2000))
@settings(max_examples=80, deadline=None)
def test_chunk_text_does_not_explode(text: str, target: int) -> None:
    """Total chunk text stays bounded relative to the source, whatever the overlap."""
    chunks = chunk_markdown(text, "s", "p", ChunkSettings(target, target // 2, 200))
    total = sum(c.char_count for c in chunks)
    assert total <= max(len(text) * 3 + 1000, 4000)


# --------------------------------------------------------------- front matter
@given(
    values=st.dictionaries(
        st.text(alphabet=string.ascii_lowercase + "_", min_size=1, max_size=12),
        st.one_of(
            st.text(max_size=200),
            st.integers(),
            st.booleans(),
            st.none(),
            st.lists(st.text(max_size=30), max_size=5),
        ),
        max_size=8,
    )
)
@settings(max_examples=200, deadline=None)
def test_front_matter_always_parses_as_yaml(values: dict) -> None:
    yaml = pytest.importorskip("yaml")
    rendered = render_front_matter(values)
    assert rendered.startswith("---\n")
    assert rendered.endswith("---\n\n")
    inner = rendered[len("---\n") : -len("---\n\n")]
    parsed = yaml.safe_load(inner) or {}
    assert set(parsed) == set(values)


@given(values=st.dictionaries(st.just("title"), st.text(max_size=300), min_size=1, max_size=1))
@settings(max_examples=100, deadline=None)
def test_front_matter_cannot_be_terminated_early(values: dict) -> None:
    """A value must never be able to close the block and inject document body."""
    rendered = render_front_matter(values)
    body_start = rendered.index("---\n", 4)
    assert rendered[body_start:] == "---\n\n"


# --------------------------------------------------------------- text decoding
@given(data=st.binary(max_size=3000))
@settings(max_examples=300, deadline=None)
def test_decode_text_never_raises(data: bytes) -> None:
    text, encoding = decode_text(data)
    assert isinstance(text, str)
    assert isinstance(encoding, str)


@given(text=st.text(max_size=2000))
@settings(max_examples=200, deadline=None)
def test_clean_text_output_is_normalised(text: str) -> None:
    cleaned = clean_text(text)
    assert "\r" not in cleaned
    assert cleaned.endswith("\n")
    assert all(not line.endswith((" ", "\t")) for line in cleaned.splitlines())


# --------------------------------------------------------------- output paths
@given(name=safe_names)
@settings(max_examples=200, deadline=None)
def test_output_path_never_escapes_the_documents_directory(name: str) -> None:
    root = Path("C:/corpus") if Path("C:/").drive else Path("/corpus")
    documents = (root / "documents").resolve()
    try:
        target = safe_output_path(root, name)
    except ValueError:
        return
    assert documents in target.parents or target.parent == documents


@given(a=safe_names, b=safe_names)
@settings(max_examples=200, deadline=None)
def test_output_filename_disambiguation_is_injective(a: str, b: str) -> None:
    """Two distinct sources must never end up owning the same Markdown file once the
    second one is disambiguated."""
    if a == b:
        return
    if output_filename(a) == output_filename(b):
        assert output_filename(a, disambiguate=True) != output_filename(b)
        assert output_filename(a) != output_filename(b, disambiguate=True)


@given(name=safe_names)
@settings(max_examples=200, deadline=None)
def test_output_filename_is_a_pure_function_of_the_source_path(name: str) -> None:
    assert output_filename(name) == output_filename(name)
    assert output_filename(name, disambiguate=True) == output_filename(name, disambiguate=True)


# --------------------------------------------------------------- archives
@given(
    members=st.lists(
        st.tuples(
            st.text(alphabet=SAFE_NAME_CHARS + "/\\.:", min_size=1, max_size=40),
            st.binary(max_size=200),
        ),
        min_size=1,
        max_size=6,
    )
)
@SLOW
def test_archive_extraction_never_writes_outside_destination(tmp_path_factory, members) -> None:
    base = Path(tmp_path_factory.mktemp("arch"))
    sentinel = base / "OUTSIDE_MARKER"
    sentinel.mkdir()
    archive_path = base / "a.zip"
    destination = base / "dest"
    seen: set[str] = set()
    with zipfile.ZipFile(archive_path, "w") as archive:
        for name, payload in members:
            if name in seen:
                continue
            seen.add(name)
            archive.writestr(name, payload)
    try:
        produced = extract_archive(archive_path, destination, ArchiveLimits())
    except ValueError:
        produced = []
    resolved_destination = destination.resolve()
    for path in produced:
        assert resolved_destination in path.resolve().parents
    assert list(sentinel.iterdir()) == []
    assert not any(p.name.startswith("OUTSIDE") for p in base.glob("*") if p.is_file())


# --------------------------------------------------------------- whole corpus
@given(
    files=st.lists(
        st.tuples(safe_names, st.text(max_size=500)),
        min_size=1,
        max_size=6,
    )
)
@SLOW
def test_corpus_integrity_holds_for_arbitrary_text_trees(tmp_path_factory, files) -> None:
    base = Path(tmp_path_factory.mktemp("corpus"))
    source = base / "src"
    source.mkdir()
    written = 0
    for name, body in files:
        path = source / (name + ".txt")
        if path.exists():
            continue
        try:
            path.write_text(body, encoding="utf-8")
        except OSError:
            continue
        written += 1
    if not written:
        return

    out = base / "out"
    Pipeline().run(source, out, PipelineSettings(chunk_chars=800, overlap_chars=80))

    def rows(name: str) -> list[dict]:
        return [json.loads(line) for line in (out / name).read_text(encoding="utf-8").splitlines() if line]

    manifest = rows("manifest.jsonl")
    chunks = rows("chunks.jsonl")
    nodes = rows("nodes.jsonl")
    edges = rows("edges.jsonl")

    source_ids = {m["source_id"] for m in manifest}
    node_ids = {n["id"] for n in nodes}

    assert len(source_ids) == len(manifest), "source ids must be unique"
    assert len({m["output_path"] for m in manifest}) == len(manifest), "output paths must be unique"
    assert len({c["chunk_id"] for c in chunks}) == len(chunks), "chunk ids must be unique"
    assert len(node_ids) == len(nodes), "node ids must be unique"

    for chunk in chunks:
        assert chunk["source_id"] in source_ids, "every chunk must reference a real source"
    for edge in edges:
        assert edge["source"] in node_ids, "edges must not dangle"
        assert edge["target"] in node_ids, "edges must not dangle"
    for row in manifest:
        assert (out / row["output_path"]).is_file(), "manifest must point at a real file"
        assert len(row["sha256"]) == 64

    by_source: dict[str, list[int]] = {}
    for chunk in chunks:
        by_source.setdefault(chunk["source_id"], []).append(chunk["ordinal"])
    for ordinals in by_source.values():
        assert sorted(ordinals) == list(range(len(ordinals))), "ordinals must be dense per source"


@given(files=st.lists(st.tuples(safe_names, st.text(max_size=300)), min_size=1, max_size=5))
@SLOW
def test_second_run_is_byte_identical(tmp_path_factory, files) -> None:
    base = Path(tmp_path_factory.mktemp("stable"))
    source = base / "src"
    source.mkdir()
    written = 0
    for name, body in files:
        path = source / (name + ".txt")
        if path.exists():
            continue
        try:
            path.write_text(body, encoding="utf-8")
        except OSError:
            continue
        written += 1
    if not written:
        return

    out = base / "out"
    Pipeline().run(source, out, PipelineSettings(chunk_chars=800, overlap_chars=80))
    before = {
        name: (out / name).read_bytes()
        for name in ["manifest.jsonl", "chunks.jsonl", "nodes.jsonl", "edges.jsonl", "INDEX.md"]
    }
    Pipeline().run(source, out, PipelineSettings(chunk_chars=800, overlap_chars=80))
    for name, payload in before.items():
        assert (out / name).read_bytes() == payload, name
