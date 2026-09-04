from brainforgemd.graph import build_graph
from brainforgemd.models import Chunk


def test_graph_has_contains_next_and_urls() -> None:
    docs = [{
        "source_id": "src_1", "source_path": "a.md", "title": "A", "sha256": "abc",
        "markdown": "See https://example.com and [B](b.md)",
    }, {
        "source_id": "src_2", "source_path": "b.md", "title": "B", "sha256": "def", "markdown": "B",
    }]
    chunks = [
        Chunk("chk_1", "src_1", "a.md", 0, [], "one", 3, 1, "1"),
        Chunk("chk_2", "src_1", "a.md", 1, [], "two", 3, 1, "2"),
    ]
    nodes, edges = build_graph(docs, chunks)
    types = {e["type"] for e in edges}
    assert {"contains", "next", "references_url", "links_to"}.issubset(types)
    assert any(n["type"] == "url" for n in nodes)
