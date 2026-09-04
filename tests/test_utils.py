from brainforgemd.frontmatter import render_front_matter
from brainforgemd.utils import fenced, stable_id


def test_stable_id_is_stable() -> None:
    assert stable_id("src", "a", "b") == stable_id("src", "a", "b")
    assert stable_id("src", "a", "b") != stable_id("src", "a", "c")


def test_fence_expands_for_backticks() -> None:
    rendered = fenced("before ``` inside")
    assert rendered.startswith("````\n")


def test_frontmatter_quotes_strings() -> None:
    text = render_front_matter({"title": "a: b", "n": 2, "ok": True})
    assert 'title: "a: b"' in text
    assert "n: 2" in text
    assert "ok: true" in text
