from brainforgemd.chunking import ChunkSettings, chunk_markdown


def test_chunking_preserves_section_path_and_stable_ids() -> None:
    md = "# Alpha\n\n" + ("hello world. " * 300) + "\n\n## Beta\n\n" + ("more text. " * 300)
    settings = ChunkSettings(target_chars=1000, overlap_chars=100, min_chars=100)
    first = chunk_markdown(md, "src_1", "file.md", settings)
    second = chunk_markdown(md, "src_1", "file.md", settings)
    assert len(first) > 2
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert first[0].section_path == ["Alpha"]
    assert any(c.section_path == ["Alpha", "Beta"] for c in first)
