"""Regression tests for defects found during the independent audit.

Every test here failed against commit 29f27d5 and must keep passing afterwards.
See INDEPENDENT_AUDIT_REPORT.md for the analysis behind each one.
"""

from __future__ import annotations

import json
import os
import time
import zipfile
from pathlib import Path

import pytest

from brainforgemd.archive import ArchiveLimits, extract_archive
from brainforgemd.chunking import ChunkSettings, chunk_markdown
from brainforgemd.converters.email import EmlConverter
from brainforgemd.converters.text import CsvConverter, HtmlConverter, XmlConverter
from brainforgemd.graph import build_graph
from brainforgemd.pipeline import Pipeline, PipelineSettings
from brainforgemd.utils import decode_text, guess_mime


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


# --------------------------------------------------------------- AUDIT-01
def test_html_script_and_style_bodies_are_stripped(tmp_path: Path) -> None:
    """AUDIT-01: the backreference in the script/style regex was written ``\\\\1``,
    a literal backslash-one, so it never matched and script/CSS text leaked into the corpus."""
    path = tmp_path / "page.html"
    path.write_text(
        "<html><head><title>Doc</title>"
        "<style>body{color:red}</style>"
        "<script>var SECRET='leak';alert(1)</script></head>"
        "<body><p>Real prose.</p><noscript>NOSCRIPTTEXT</noscript></body></html>",
        encoding="utf-8",
    )
    markdown = HtmlConverter().convert(path).markdown
    assert "Real prose." in markdown
    assert "SECRET" not in markdown
    assert "alert(1)" not in markdown
    assert "color:red" not in markdown
    assert "NOSCRIPTTEXT" not in markdown


def test_html_unterminated_script_does_not_leak(tmp_path: Path) -> None:
    path = tmp_path / "page.html"
    path.write_text("<html><body><p>Kept.</p><script>var LEAKED=1;", encoding="utf-8")
    markdown = HtmlConverter().convert(path).markdown
    assert "Kept." in markdown
    assert "LEAKED" not in markdown


def test_eml_html_script_body_is_stripped(tmp_path: Path) -> None:
    """AUDIT-01: the same broken backreference was duplicated in the EML converter."""
    path = tmp_path / "mail.eml"
    path.write_text(
        "From: a@example.test\nTo: b@example.test\nSubject: HTML only\n"
        "Content-Type: text/html; charset=utf-8\n\n"
        "<html><body><script>var TRACKER='leak'</script><p>Message body.</p></body></html>\n",
        encoding="utf-8",
    )
    markdown = EmlConverter().convert(path).markdown
    assert "Message body." in markdown
    assert "TRACKER" not in markdown


# --------------------------------------------------------------- AUDIT-02
def test_utf32_text_is_decoded_as_utf32(tmp_path: Path) -> None:
    """AUDIT-02: the UTF-32 BOM test sat after the UTF-16 test, and a UTF-32 LE BOM
    starts with the UTF-16 LE BOM, so UTF-32 was always decoded as UTF-16."""
    original = "Cafe Quebec \U0001F600 ok"
    text, encoding = decode_text(original.encode("utf-32"))
    assert encoding.startswith("utf-32")
    assert text == original


def test_utf16_bom_with_broken_payload_falls_back_instead_of_failing() -> None:
    """AUDIT-02: a BOM-declared decode that raised aborted the file entirely rather than
    falling through to the permissive ladder that ends at latin-1."""
    text, encoding = decode_text(b"\xff\xfeodd-length-body-x")
    assert text
    assert encoding


# --------------------------------------------------------------- AUDIT-03
def test_blank_document_produces_no_chunks() -> None:
    """AUDIT-03: an empty body produced one zero-length chunk with approx_tokens=1."""
    for body in ["", "\n", "   \n\n  \n"]:
        assert chunk_markdown(body, "src_x", "a.txt", ChunkSettings(1000, 100, 200)) == []


def test_empty_source_file_adds_no_empty_chunk_to_corpus(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "empty.txt").write_text("", encoding="utf-8")
    (source / "real.txt").write_text("actual knowledge content", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())
    chunks = _jsonl(out / "chunks.jsonl")
    assert [c for c in chunks if c["char_count"] == 0] == []
    assert any(c["source_path"] == "real.txt" for c in chunks)


# --------------------------------------------------------------- AUDIT-04
def test_malformed_markdown_link_does_not_abort_the_run(tmp_path: Path) -> None:
    """AUDIT-04: urlparse raises ValueError on an unterminated IPv6 literal, and the graph
    stage was unguarded, so one bad link killed the whole corpus build."""
    docs = [
        {
            "source_id": "src_1",
            "source_path": "a.md",
            "title": "A",
            "sha256": "x",
            "markdown": "[bad](http://[nothost/page) and [ok](b.md)",
        },
        {"source_id": "src_2", "source_path": "b.md", "title": "B", "sha256": "y", "markdown": "B"},
    ]
    _nodes, edges = build_graph(docs, [])
    assert any(e["type"] == "links_to" for e in edges)


def test_pipeline_survives_hostile_link_and_still_writes_full_corpus(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "good.txt").write_text("healthy content", encoding="utf-8")
    (source / "hostile.md").write_text("# H\n\n[bad](http://[nothost/page)\n", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())
    for name in ["manifest.jsonl", "chunks.jsonl", "nodes.jsonl", "edges.jsonl", "INDEX.md", "REPORT.md"]:
        assert (out / name).is_file(), name
    assert (out / ".brainforgemd" / "state.json").is_file()


# --------------------------------------------------------------- AUDIT-05
def test_readme_and_readme_md_do_not_overwrite_each_other(tmp_path: Path) -> None:
    """AUDIT-05: ``README`` and ``README.md`` both mapped to documents/README.md, so one
    source was silently destroyed and its manifest row pointed at the other's text."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "README").write_text("EXTENSIONLESS_BODY", encoding="utf-8")
    (source / "README.md").write_text("# Md\n\nMARKDOWN_BODY", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())

    manifest = _jsonl(out / "manifest.jsonl")
    assert len(manifest) == 2
    assert len({m["output_path"] for m in manifest}) == 2, "each source needs its own output file"
    bodies = {m["source_path"]: (out / m["output_path"]).read_text(encoding="utf-8") for m in manifest}
    assert "EXTENSIONLESS_BODY" in bodies["README"]
    assert "MARKDOWN_BODY" in bodies["README.md"]


def test_colliding_outputs_keep_correct_provenance_across_incremental_runs(tmp_path: Path) -> None:
    """The second run took the cached branch and re-read the surviving file for both sources,
    attributing one document's text to the other document's provenance."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "notes.txt").write_text("UNIQUE_TXT_CONTENT", encoding="utf-8")
    (source / "notes.txt.md").write_text("UNIQUE_MD_CONTENT", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())
    Pipeline().run(source, out, PipelineSettings())

    by_source = {c["source_path"]: c["text"] for c in _jsonl(out / "chunks.jsonl")}
    assert "UNIQUE_TXT_CONTENT" in by_source["notes.txt"]
    assert "UNIQUE_MD_CONTENT" in by_source["notes.txt.md"]


def test_collision_disambiguation_is_stable_across_runs(tmp_path: Path) -> None:
    """Disambiguation is decided by source path, so repeated runs over the same sources
    always assign the same output file to the same source."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "README").write_text("EXTENSIONLESS_BODY", encoding="utf-8")
    (source / "README.md").write_text("MARKDOWN_BODY", encoding="utf-8")
    (source / "notes.txt").write_text("plain notes", encoding="utf-8")

    first = tmp_path / "out1"
    second = tmp_path / "out2"
    Pipeline().run(source, first, PipelineSettings())
    Pipeline().run(source, second, PipelineSettings())
    mapping = {m["source_path"]: m["output_path"] for m in _jsonl(first / "manifest.jsonl")}
    assert mapping == {m["source_path"]: m["output_path"] for m in _jsonl(second / "manifest.jsonl")}
    assert (first / "manifest.jsonl").read_bytes() == (second / "manifest.jsonl").read_bytes()
    # A non-colliding source keeps the plain, readable name.
    assert mapping["notes.txt"] == "documents/notes.txt.md"


def test_removing_a_collider_reconverts_and_leaves_no_stale_file(tmp_path: Path) -> None:
    """When a collider disappears the survivor may reclaim the plain name; the corpus
    must then be rebuilt for it rather than serving the cached disambiguated file."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "README").write_text("EXTENSIONLESS_BODY", encoding="utf-8")
    (source / "README.md").write_text("MARKDOWN_BODY", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())

    (source / "README").unlink()
    Pipeline().run(source, out, PipelineSettings())

    manifest = _jsonl(out / "manifest.jsonl")
    assert [m["source_path"] for m in manifest] == ["README.md"]
    on_disk = {p.relative_to(out).as_posix() for p in (out / "documents").rglob("*.md")}
    assert on_disk == {manifest[0]["output_path"]}
    assert "MARKDOWN_BODY" in (out / manifest[0]["output_path"]).read_text(encoding="utf-8")


# --------------------------------------------------------------- AUDIT-06
def test_xml_entity_expansion_is_rejected(tmp_path: Path) -> None:
    """AUDIT-06: xml.etree expands internal entities without any limit, so a small file
    could be inflated into gigabytes of memory (billion laughs)."""
    path = tmp_path / "bomb.xml"
    path.write_text(
        '<?xml version="1.0"?>\n<!DOCTYPE lolz [\n'
        ' <!ENTITY a "' + "A" * 50 + '">\n'
        ' <!ENTITY b "' + "&a;" * 10 + '">\n'
        ' <!ENTITY c "' + "&b;" * 10 + '">\n'
        ' <!ENTITY d "' + "&c;" * 10 + '">\n'
        ']>\n<lolz>&d;</lolz>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"(?i)entity"):
        XmlConverter().convert(path)


def test_xml_external_entity_is_rejected(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP_SECRET_VALUE", encoding="utf-8")
    path = tmp_path / "xxe.xml"
    path.write_text(
        '<?xml version="1.0"?>\n<!DOCTYPE r [<!ENTITY x SYSTEM "file:///'
        + secret.as_posix()
        + '">]>\n<r>&x;</r>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        XmlConverter().convert(path)
    assert "TOP_SECRET_VALUE" not in path.read_text(encoding="utf-8")


def test_plain_xml_still_converts(tmp_path: Path) -> None:
    path = tmp_path / "ok.xml"
    path.write_text('<?xml version="1.0"?><root><item>value</item></root>', encoding="utf-8")
    assert "value" in XmlConverter().convert(path).markdown


# --------------------------------------------------------------- AUDIT-07
def test_csv_quoted_newline_does_not_glue_words_together(tmp_path: Path) -> None:
    """AUDIT-07: splitlines() stripped the newline inside quoted fields, so
    "line one\\nline two" was emitted as "line oneline two"."""
    path = tmp_path / "multi.csv"
    path.write_text('name,note\nalpha,"line one\nline two"\nbeta,ok\n', encoding="utf-8")
    result = CsvConverter().convert(path)
    assert "line one line two" in result.markdown
    assert "line oneline two" not in result.markdown
    assert result.metadata["rows_emitted"] == 3


# --------------------------------------------------------------- AUDIT-08
def test_overlap_close_to_target_is_rejected() -> None:
    """AUDIT-08: overlap only had to be < target, so target=500/overlap=499 advanced one
    character per chunk and inflated a 200 KB document into ~100 MB of chunk text."""
    with pytest.raises(ValueError, match="overlap_chars"):
        ChunkSettings(target_chars=500, overlap_chars=499).validate()
    ChunkSettings(target_chars=5000, overlap_chars=500).validate()


def test_chunk_text_total_stays_bounded() -> None:
    settings = ChunkSettings(target_chars=1000, overlap_chars=500, min_chars=1)
    settings.validate()
    chunks = chunk_markdown("x" * 100_000, "s", "p", settings)
    assert sum(c.char_count for c in chunks) < 100_000 * 3


# --------------------------------------------------------------- AUDIT-09
def test_deleted_and_renamed_sources_do_not_leave_orphan_documents(tmp_path: Path) -> None:
    """AUDIT-09: documents/ kept Markdown for sources that no longer exist, so anyone
    consuming documents/**/*.md (as the README recommends) read deleted content."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "alpha.txt").write_text("alpha content", encoding="utf-8")
    (source / "beta.txt").write_text("beta content", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())

    (source / "beta.txt").unlink()
    (source / "alpha.txt").rename(source / "alpha-renamed.txt")
    Pipeline().run(source, out, PipelineSettings())

    on_disk = {p.name for p in (out / "documents").rglob("*.md")}
    assert on_disk == {"alpha-renamed.txt.md"}


def test_single_file_run_never_prunes_sibling_documents(tmp_path: Path) -> None:
    """Pruning must only apply to a full directory scan; a one-file run must not wipe
    the rest of an existing corpus."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("a content", encoding="utf-8")
    (source / "b.txt").write_text("b content", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())
    assert {p.name for p in (out / "documents").rglob("*.md")} == {"a.txt.md", "b.txt.md"}

    Pipeline().run(source / "a.txt", out, PipelineSettings())
    assert (out / "documents" / "b.txt.md").is_file()


# --------------------------------------------------------------- AUDIT-10
def test_write_failure_on_one_document_is_isolated_not_fatal(tmp_path: Path, monkeypatch) -> None:
    """AUDIT-10: any OSError while writing one document (a Windows path over MAX_PATH,
    a permission problem, a full disk) escaped and aborted the entire run, leaving a
    half-written corpus and no incremental state."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "ok.txt").write_text("healthy content", encoding="utf-8")
    (source / "doomed.txt").write_text("doomed content", encoding="utf-8")

    real_write_text = Path.write_text

    def flaky_write_text(self: Path, *args, **kwargs):
        if "doomed" in self.name:
            raise OSError(2, "No such file or directory")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", flaky_write_text)
    out = tmp_path / "out"
    stats = Pipeline().run(source, out, PipelineSettings())
    monkeypatch.undo()

    assert (out / "manifest.jsonl").is_file()
    assert (out / ".brainforgemd" / "state.json").is_file()
    assert stats.converted == 1
    assert stats.failed == 1
    assert [m["source_path"] for m in _jsonl(out / "manifest.jsonl")] == ["ok.txt"]
    errors = _jsonl(out / "errors.jsonl")
    assert [e["source_path"] for e in errors] == ["doomed.txt"]
    assert errors[0]["stage"] == "write"


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH only constrains Windows")
def test_windows_long_output_path_is_isolated_not_fatal(tmp_path: Path) -> None:
    """The output path is always longer than the source path (it gains ``documents/``
    and ``.md``), so a source comfortably inside MAX_PATH can produce an output over it."""
    source = tmp_path / "s"
    source.mkdir()
    (source / "ok.txt").write_text("healthy content", encoding="utf-8")
    padding = max(10, 258 - len(str(source)) - len("/.txt"))
    (source / ("n" * padding + ".txt")).write_text("payload", encoding="utf-8")

    out = tmp_path / "o"
    stats = Pipeline().run(source, out, PipelineSettings())
    assert (out / ".brainforgemd" / "state.json").is_file()
    assert any(m["source_path"] == "ok.txt" for m in _jsonl(out / "manifest.jsonl"))
    assert stats.converted >= 1


def test_source_removed_mid_run_is_reported_not_fatal(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "keep.txt").write_text("keep me", encoding="utf-8")
    vanishing = source / "vanish.txt"
    vanishing.write_text("gone soon", encoding="utf-8")

    pipeline = Pipeline()
    original = pipeline.registry.convert

    def convert(path: Path):
        if path.name == "vanish.txt":
            os.remove(path)
        return original(path)

    pipeline.registry.convert = convert  # type: ignore[method-assign]
    out = tmp_path / "out"
    stats = pipeline.run(source, out, PipelineSettings())
    assert stats.converted >= 1
    assert (out / ".brainforgemd" / "state.json").is_file()


# --------------------------------------------------------------- AUDIT-11
def test_mime_type_is_deterministic_for_declared_formats() -> None:
    """AUDIT-11: guess_mime delegated to mimetypes, which reads the Windows registry and
    changes between Python releases, so manifest.jsonl was not reproducible across hosts."""
    expected = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".yaml": "application/yaml",
        ".zip": "application/zip",
        ".ts": "text/x-typescript",
        ".py": "text/x-python",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".ipynb": "application/x-ipynb+json",
    }
    for extension, mime in expected.items():
        assert guess_mime(Path("sample" + extension)) == mime, extension


def test_typescript_is_not_reported_as_video() -> None:
    assert not guess_mime(Path("module.ts")).startswith("video/")


# --------------------------------------------------------------- AUDIT-12
def test_nested_archive_expansion_is_globally_bounded(tmp_path: Path) -> None:
    """AUDIT-12: the expanded-size budget was per archive, so every nested archive got a
    fresh allowance and a 7 KB input produced a 115 MB corpus."""
    import io

    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as z:
        for i in range(20):
            z.writestr(f"f{i}.txt", "B" * 200_000)
    payload = inner.getvalue()
    outer = tmp_path / "nested.zip"
    with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as z:
        for i in range(10):
            z.writestr(f"n{i}.zip", payload)

    out = tmp_path / "out"
    stats = Pipeline().run(outer, out, PipelineSettings(archive_max_expanded_mb=8))
    produced = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    assert produced < 40 * 1024 * 1024, f"corpus grew to {produced} bytes despite an 8 MiB budget"
    assert stats.failed >= 1, "hitting the global budget must be reported"


def test_archive_member_count_is_globally_bounded(tmp_path: Path) -> None:
    inner = zipfile_bytes({f"f{i}.txt": "x" for i in range(40)})
    outer = tmp_path / "many.zip"
    with zipfile.ZipFile(outer, "w") as z:
        for i in range(10):
            z.writestr(f"n{i}.zip", inner)
    out = tmp_path / "out"
    stats = Pipeline().run(outer, out, PipelineSettings(archive_max_files=100))
    assert stats.converted <= 100


def zipfile_bytes(members: dict[str, str]) -> bytes:
    import io

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buffer.getvalue()


# --------------------------------------------------------------- AUDIT-13
def test_fail_on_error_flag_reports_a_non_zero_exit(tmp_path: Path) -> None:
    """AUDIT-13: a run where every source failed still exited 0, so CI could not detect it."""
    from brainforgemd.cli import main

    source = tmp_path / "src"
    source.mkdir()
    (source / "big.txt").write_text("x" * 4096, encoding="utf-8")
    assert main(["convert", str(source), "-o", str(tmp_path / "o1"), "--max-file-mb", "0"]) == 0
    assert (
        main(["convert", str(source), "-o", str(tmp_path / "o2"), "--max-file-mb", "0", "--fail-on-error"])
        != 0
    )


# --------------------------------------------------------------- archive hardening
def test_archive_member_with_invalid_host_name_is_a_clean_error(tmp_path: Path) -> None:
    """A member name that is illegal on the host filesystem raised a bare OSError from
    inside extraction instead of the documented ValueError."""
    archive_path = tmp_path / "weird.zip"
    with zipfile.ZipFile(archive_path, "w") as z:
        z.writestr("....//escape.txt", "payload")
    with pytest.raises(ValueError):
        extract_archive(archive_path, tmp_path / "dest", ArchiveLimits())
    assert not (tmp_path / "escape.txt").exists()


def test_chunking_stays_fast_on_a_large_document() -> None:
    settings = ChunkSettings(target_chars=5000, overlap_chars=500, min_chars=200)
    started = time.time()
    chunks = chunk_markdown("word " * 200_000, "s", "p", settings)
    assert time.time() - started < 10
    assert len(chunks) > 100


# --------------------------------------------------------------- AUDIT-14
def test_html_table_cells_do_not_fuse_into_one_token(tmp_path: Path) -> None:
    """AUDIT-14: remaining tags were replaced with nothing, so adjacent cells and inline
    elements fused into tokens that match neither word ("AlphaBeta")."""
    path = tmp_path / "t.html"
    path.write_text(
        "<html><body><table><tr><td>Alpha</td><td>Beta</td></tr>"
        "<tr><td>One</td><td>Two</td></tr></table>"
        "<p><span>Left</span><span>Right</span></p></body></html>",
        encoding="utf-8",
    )
    markdown = HtmlConverter().convert(path).markdown
    assert "AlphaBeta" not in markdown
    assert "LeftRight" not in markdown
    for token in ["Alpha", "Beta", "One", "Two", "Left", "Right"]:
        assert token in markdown


def test_html_title_is_not_duplicated_into_the_body(tmp_path: Path) -> None:
    path = tmp_path / "t.html"
    path.write_text(
        "<html><head><title>My Title</title></head><body><p>Body text.</p></body></html>",
        encoding="utf-8",
    )
    result = HtmlConverter().convert(path)
    assert result.title == "My Title"
    body = result.markdown.split("\n\n", 1)[1]
    assert "My Title" not in body
    assert body.strip() == "Body text."


# --------------------------------------------------------------- AUDIT-15
def test_pdf_without_a_backend_is_reported_not_dumped_as_text(tmp_path: Path) -> None:
    """AUDIT-15: an uncompressed PDF is mostly printable ASCII, so the last-resort text
    converter accepted it whenever no rich backend was installed and wrote PDF object
    syntax into the corpus as prose, reported as a successful conversion."""
    from brainforgemd.converters.generic_text import GenericTextConverter

    path = tmp_path / "doc.pdf"
    path.write_text(
        "%PDF-1.3\n1 0 obj\n<<\n/Type /Page\n>>\nendobj\ntrailer\n<<\n/Size 2\n>>\n%%EOF\n",
        encoding="utf-8",
    )
    assert not GenericTextConverter().accepts(path)


@pytest.mark.parametrize(
    "name", ["a.pdf", "a.docx", "a.xlsx", "a.pptx", "a.odt", "a.png", "a.mp3", "a.mp4",
             "a.zip", "a.tar.gz", "a.sqlite", "a.parquet", "a.epub"]
)
def test_binary_families_are_never_claimed_by_the_text_fallback(tmp_path: Path, name: str) -> None:
    from brainforgemd.converters.generic_text import GenericTextConverter

    path = tmp_path / name
    path.write_text("plain looking bytes", encoding="utf-8")
    assert not GenericTextConverter().accepts(path)


def test_text_fallback_still_rescues_unknown_and_extensionless_files(tmp_path: Path) -> None:
    from brainforgemd.converters.generic_text import GenericTextConverter

    for name in ["README", "notes.unknownext", "CHANGELOG"]:
        path = tmp_path / name
        path.write_text("real prose content", encoding="utf-8")
        assert GenericTextConverter().accepts(path), name


# --------------------------------------------------------------- AUDIT-16
def test_formats_marks_backends_that_are_not_installed(monkeypatch) -> None:
    """AUDIT-16: the docs call `brainforgemd formats` the authority for a machine, but it
    listed every rich extension even when the backend behind it was absent and each of
    those files would fail."""
    from brainforgemd.registry import build_default_registry

    rows = {name: available for name, _, available in build_default_registry().format_rows()}
    assert rows["text"] is True
    assert rows["csv"] is True
    assert "docling" in rows
    assert "markitdown" in rows

    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    rows = {name: available for name, _, available in build_default_registry().format_rows()}
    assert rows["docling"] is False
    assert rows["markitdown"] is False
    assert rows["outlook-msg"] is False
    assert rows["parquet"] is False
    assert rows["text"] is True


# --------------------------------------------------------------- AUDIT-17
def test_control_characters_in_a_title_keep_front_matter_valid_yaml(tmp_path: Path) -> None:
    """AUDIT-17: json.dumps escapes code points below 0x20 but leaves DEL, the C1 block
    and U+2028/U+2029 raw, and YAML rejects those even inside a quoted scalar. A title
    carrying one produced a document whose front matter no YAML parser would read."""
    yaml = pytest.importorskip("yaml")
    from brainforgemd.frontmatter import render_front_matter

    for bad in [chr(0x7F), chr(0x85), chr(0x9F), chr(0x2028), chr(0x2029), chr(0xFEFF)]:
        rendered = render_front_matter({"title": f"before{bad}after"})
        parsed = yaml.safe_load(rendered[len("---\n") : -len("---\n\n")])
        assert parsed["title"] == f"before{bad}after"


def test_front_matter_keys_that_spell_yaml_keywords_stay_strings() -> None:
    """AUDIT-17: an unquoted key such as `true` or `null` is read back as a boolean or
    None rather than as the string it was written as."""
    yaml = pytest.importorskip("yaml")
    from brainforgemd.frontmatter import render_front_matter

    rendered = render_front_matter({"true": 1, "null": 2, "off": 3, "title": "x", "n": 4})
    parsed = yaml.safe_load(rendered[len("---\n") : -len("---\n\n")])
    assert set(parsed) == {"true", "null", "off", "title", "n"}
    # Ordinary keys must keep the documented unquoted rendering.
    assert "\ntitle: " in rendered
    assert "\nn: 4" in rendered


# --------------------------------------------------------------- AUDIT-18
def test_index_links_survive_parentheses_and_hashes(tmp_path: Path) -> None:
    """AUDIT-18: only [ and ] were escaped, so a ")" in a filename closed the Markdown
    link early and documents/paren(1).txt.md resolved to "documents/paren(1"."""
    import re
    from urllib.parse import unquote

    source = tmp_path / "src"
    source.mkdir()
    for name in ["plain.txt", "with space.txt", "paren(1).txt", "hash#3.txt", "amp&4.txt"]:
        (source / name).write_text("content", encoding="utf-8")
    out = tmp_path / "out"
    Pipeline().run(source, out, PipelineSettings())

    index = (out / "INDEX.md").read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)\s]*)\)", index)
    assert len(targets) == len(_jsonl(out / "manifest.jsonl"))
    for target in targets:
        assert (out / unquote(target)).is_file(), target


def test_source_modified_during_conversion_is_reported(tmp_path: Path) -> None:
    """AUDIT-18: if the source changed between hashing and conversion, manifest.jsonl
    published a sha256 for bytes the stored Markdown never came from."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "stable.txt").write_text("stable content", encoding="utf-8")
    racing = source / "racing.txt"
    racing.write_text("ORIGINAL_CONTENT", encoding="utf-8")

    pipeline = Pipeline()
    original = pipeline.registry.convert

    def convert(path: Path):
        if path.name == "racing.txt":
            time.sleep(0.01)
            path.write_text("MUTATED_CONTENT_THAT_IS_LONGER", encoding="utf-8")
        return original(path)

    pipeline.registry.convert = convert  # type: ignore[method-assign]
    out = tmp_path / "out"
    stats = pipeline.run(source, out, PipelineSettings())

    assert stats.converted == 1
    assert [m["source_path"] for m in _jsonl(out / "manifest.jsonl")] == ["stable.txt"]
    errors = _jsonl(out / "errors.jsonl")
    assert [e["error_type"] for e in errors] == ["SourceChangedDuringRead"]


# --------------------------------------------------------------- AUDIT-19
def test_corpus_index_files_are_written_atomically(tmp_path: Path) -> None:
    """AUDIT-19: the index files were opened with mode "w", which truncates first, so an
    interrupted write left a zero-length manifest.jsonl that no consumer could parse."""
    from brainforgemd.utils import atomic_write_text

    target = tmp_path / "manifest.jsonl"
    target.write_text('{"kept": true}\n', encoding="utf-8")

    class Boom(Exception):
        pass

    real_write_text = Path.write_text

    def exploding(self: Path, *args, **kwargs):
        if self.name.endswith(".tmp"):
            real_write_text(self, *args, **kwargs)
            raise Boom("interrupted mid-write")
        return real_write_text(self, *args, **kwargs)

    Path.write_text = exploding  # type: ignore[method-assign]
    try:
        with pytest.raises(Boom):
            atomic_write_text(target, "replacement\n")
    finally:
        Path.write_text = real_write_text  # type: ignore[method-assign]

    assert target.read_text(encoding="utf-8") == '{"kept": true}\n'
    assert list(tmp_path.glob("*.tmp")) == [], "the temporary file must not be left behind"


def test_a_second_concurrent_run_is_refused(tmp_path: Path) -> None:
    """AUDIT-19: two runs sharing one output directory interleaved and each pruned the
    other's documents as orphans, leaving chunks with no source and broken INDEX links."""
    from brainforgemd.lock import CorpusLock, CorpusLocked

    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("content", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    with CorpusLock(out), pytest.raises(CorpusLocked, match="Another BrainForgeMD run"):
        Pipeline().run(source, out, PipelineSettings())

    # The lock is released, so an ordinary run works again.
    stats = Pipeline().run(source, out, PipelineSettings())
    assert stats.converted == 1
    assert not (out / ".brainforgemd" / "lock").exists()


def test_lock_is_released_when_a_run_fails(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.bin").write_bytes(b"\x00binary")
    out = tmp_path / "out"
    with pytest.raises(RuntimeError):
        Pipeline().run(source, out, PipelineSettings(strict=True))
    assert not (out / ".brainforgemd" / "lock").exists()
    Pipeline().run(source, out, PipelineSettings())


# --------------------------------------------------------------- AUDIT-20
def test_output_directory_containing_the_source_is_rejected(tmp_path: Path) -> None:
    """AUDIT-20: an output directory above the source excluded every file through the
    "never re-ingest the corpus" filter, so `convert ./docs -o .` reported discovered=0,
    wrote an empty corpus and exited 0."""
    out = tmp_path / "work"
    source = out / "knowledge"
    source.mkdir(parents=True)
    for index in range(3):
        (source / f"f{index}.txt").write_text(f"real content {index}", encoding="utf-8")

    with pytest.raises(ValueError, match="contains the source directory"):
        Pipeline().run(source, out, PipelineSettings())

    # The supported arrangement, output nested inside the source, still works.
    nested = source / "context-out"
    stats = Pipeline().run(source, nested, PipelineSettings())
    assert stats.converted == 3


def test_archive_members_differing_only_by_case_are_reported(tmp_path: Path) -> None:
    """AUDIT-20: archive names are case-sensitive but Windows and macOS filesystems are
    not, so a ZIP holding Report.txt and report.txt extracted into one file and the
    manifest attributed the surviving text to both source paths."""
    archive_path = tmp_path / "case.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("Report.txt", "UPPERCASE_SOURCE_CONTENT")
        archive.writestr("report.txt", "lowercase_source_content")

    out = tmp_path / "out"
    stats = Pipeline().run(archive_path, out, PipelineSettings())

    if os.path.normcase("A") == os.path.normcase("a"):
        # Case-insensitive host: the clash must be reported, never silently resolved.
        assert stats.converted == 0
        assert stats.failed == 1
        assert "same file" in _jsonl(out / "errors.jsonl")[0]["message"]
    else:
        # Case-sensitive host: both members are genuinely distinct files.
        assert stats.converted == 2
        texts = {c["source_path"]: c["text"] for c in _jsonl(out / "chunks.jsonl")}
        assert "UPPERCASE_SOURCE_CONTENT" in texts["case.zip!/Report.txt"]
        assert "lowercase_source_content" in texts["case.zip!/report.txt"]


def test_distinct_archive_members_still_extract(tmp_path: Path) -> None:
    archive_path = tmp_path / "ok.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("a/one.txt", "first")
        archive.writestr("b/one.txt", "second")
        archive.writestr("two.txt", "third")
    out = tmp_path / "out"
    assert Pipeline().run(archive_path, out, PipelineSettings()).converted == 3
