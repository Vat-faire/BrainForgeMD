from __future__ import annotations

import csv
import html
import io
import json
import re
from pathlib import Path
from xml.parsers import expat

from ..models import ConversionResult
from ..utils import clean_text, decode_text, fenced
from .base import Converter

TEXT_EXTENSIONS = frozenset({
    ".txt", ".md", ".markdown", ".rst", ".log", ".adoc", ".asciidoc",
})

CODE_LANGUAGES = {
    ".py": "python", ".pyw": "python", ".js": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".ts": "typescript", ".tsx": "tsx", ".jsx": "jsx",
    ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp",
    ".cxx": "cpp", ".hpp": "cpp", ".cs": "csharp", ".go": "go", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".kts": "kotlin", ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
    ".fish": "fish", ".ps1": "powershell", ".bat": "batch", ".cmd": "batch",
    ".sql": "sql", ".r": "r", ".lua": "lua", ".pl": "perl", ".ex": "elixir",
    ".exs": "elixir", ".erl": "erlang", ".fs": "fsharp", ".fsx": "fsharp",
    ".scala": "scala", ".dart": "dart", ".groovy": "groovy", ".sol": "solidity",
    ".vue": "vue", ".svelte": "svelte", ".css": "css", ".scss": "scss",
    ".less": "less", ".tex": "latex", ".graphql": "graphql", ".gql": "graphql",
    ".proto": "protobuf", ".tf": "hcl", ".hcl": "hcl", ".dockerfile": "dockerfile",
}

CONFIG_EXTENSIONS = frozenset({
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties", ".env",
    ".editorconfig", ".gitignore", ".gitattributes", ".npmrc", ".dockerignore",
})


_NON_CONTENT_TAGS = "script|style|noscript|template"
_PAIRED_NON_CONTENT_RE = re.compile(rf"(?is)<({_NON_CONTENT_TAGS})\b[^>]*>.*?</\1\s*>")
_UNCLOSED_NON_CONTENT_RE = re.compile(rf"(?is)<({_NON_CONTENT_TAGS})\b[^>]*>.*\Z")
_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
_WHITESPACE_RUN_RE = re.compile(r"\s+")


def strip_non_content_elements(markup: str) -> str:
    """Remove script/style/noscript bodies and comments from HTML-ish markup.

    The backreference in the original pattern was written ``\\\\1`` inside a raw string,
    which matches a literal backslash and a one, so nothing was ever removed and script
    source and CSS ended up in the corpus as prose.
    """
    markup = _COMMENT_RE.sub("", markup)
    previous = None
    while previous != markup:
        previous = markup
        markup = _PAIRED_NON_CONTENT_RE.sub("", markup)
    # An opening tag with no closing tag would otherwise leak its whole tail.
    return _UNCLOSED_NON_CONTENT_RE.sub("", markup)


class PlainTextConverter(Converter):
    name = "text"
    extensions = TEXT_EXTENSIONS

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        return ConversionResult(clean_text(text), self.name, path.stem, {"encoding": encoding})


class CodeConverter(Converter):
    name = "code"
    extensions = frozenset(CODE_LANGUAGES) | CONFIG_EXTENSIONS

    def accepts(self, path: Path) -> bool:
        name = path.name.lower()
        if name in {"dockerfile", "makefile", "cmakelists.txt", "justfile"}:
            return True
        return super().accepts(path)

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        lang = CODE_LANGUAGES.get(path.suffix.lower(), "")
        if path.name.lower() == "dockerfile":
            lang = "dockerfile"
        elif path.name.lower() == "makefile":
            lang = "makefile"
        heading = f"# {path.name}\n\n"
        return ConversionResult(heading + fenced(clean_text(text), lang), self.name, path.name, {"encoding": encoding, "language": lang})


class JsonConverter(Converter):
    name = "json"
    extensions = frozenset({".json", ".jsonl", ".ndjson"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        suffix = path.suffix.lower()
        if suffix in {".jsonl", ".ndjson"}:
            lines = []
            for idx, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {idx}: {exc.msg}") from exc
                lines.append(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
            pretty = "\n".join(lines)
        else:
            obj = json.loads(text)
            pretty = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
        return ConversionResult(f"# {path.name}\n\n" + fenced(pretty, "json"), self.name, path.stem, {"encoding": encoding})


class CsvConverter(Converter):
    name = "csv"
    extensions = frozenset({".csv", ".tsv"})
    max_rows = 5000
    max_columns = 200
    max_cell_chars = 1000

    @staticmethod
    def _cell(value: str) -> str:
        # A quoted cell can legitimately span lines; collapse the whole run of
        # whitespace so CRLF sources do not leave a double space in the table.
        value = _WHITESPACE_RUN_RE.sub(" ", value).strip()
        value = value[: CsvConverter.max_cell_chars]
        return value.replace("|", "\\|")

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        sample = text[:8192]
        if path.suffix.lower() == ".csv":
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                delimiter = dialect.delimiter
            except csv.Error:
                pass
        # Feed the raw text, not splitlines(): stripping the newlines first makes the csv
        # module concatenate the halves of a quoted multi-line cell into one word.
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
        rows = []
        truncated = False
        for index, row in enumerate(reader):
            if index >= self.max_rows:
                truncated = True
                break
            rows.append(row[: self.max_columns])
        if not rows:
            return ConversionResult(f"# {path.name}\n\n_Empty table._\n", self.name, path.stem, {"encoding": encoding, "rows": 0})
        width = max(len(row) for row in rows)
        padded = [row + [""] * (width - len(row)) for row in rows]
        header = padded[0]
        body = padded[1:]
        out = [f"# {path.name}", "", "| " + " | ".join(self._cell(v) for v in header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
        out.extend("| " + " | ".join(self._cell(v) for v in row) + " |" for row in body)
        if truncated:
            out.extend(["", f"> Output truncated at {self.max_rows} rows."])
        return ConversionResult("\n".join(out) + "\n", self.name, path.stem, {"encoding": encoding, "rows_emitted": len(rows), "columns": width, "truncated": truncated})


class _EntityRejected(ValueError):
    """Raised when a document declares XML entities, which expat expands without limit."""


def validate_xml(text: str) -> None:
    """Check well-formedness with entity expansion disabled.

    ``xml.etree`` hands documents to expat, which expands internal entities with no size
    cap, so a few hundred bytes can be inflated into gigabytes of memory (the 'billion
    laughs' attack) and external entities can reach the filesystem or network. The C
    implementation of ``ElementTree.XMLParser`` exposes no handle on the underlying
    expat parser, so validation runs on expat directly with those handlers refused.
    """
    parser = expat.ParserCreate()

    def _reject_entity(*_args: object) -> None:
        raise _EntityRejected("XML entity declarations are rejected (expansion attack surface)")

    def _reject_external(*_args: object) -> bool:
        raise _EntityRejected("External XML entities are rejected")

    parser.EntityDeclHandler = _reject_entity
    parser.UnparsedEntityDeclHandler = _reject_entity
    parser.ExternalEntityRefHandler = _reject_external
    try:
        parser.Parse(text, True)
    except _EntityRejected as exc:
        raise ValueError(f"Unsafe XML: {exc}") from exc
    except expat.ExpatError as exc:
        message = expat.ErrorString(exc.code)
        if "entity" in message.lower():
            raise ValueError(f"Unsafe XML: {message}") from exc
        raise ValueError(f"Invalid XML: {message} (line {exc.lineno})") from exc


class XmlConverter(Converter):
    name = "xml"
    extensions = frozenset({".xml", ".xsd", ".svg"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        validate_xml(text)
        return ConversionResult(f"# {path.name}\n\n" + fenced(clean_text(text), "xml"), self.name, path.stem, {"encoding": encoding})


class HtmlConverter(Converter):
    name = "html"
    extensions = frozenset({".html", ".htm", ".xhtml"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        # Dependency-free conservative extraction: remove scripts/styles, preserve links/headings/paragraphs.
        text = strip_non_content_elements(text)
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1)).strip()) if title_match else path.stem
        for level in range(6, 0, -1):
            text = re.sub(
                fr"(?is)<h{level}[^>]*>(.*?)</h{level}>",
                lambda m, level=level: "\n" + "#" * level + " " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n",
                text,
            )
        text = re.sub(r'(?is)<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', lambda m: f"[{re.sub(r'<[^>]+>', '', m.group(2)).strip()}]({m.group(1)})", text)
        # The <head> is metadata, and leaving it in duplicated the title into the body.
        text = re.sub(r"(?is)<head[^>]*>.*?</head>", "", text)
        text = re.sub(r"(?is)<br\s*/?>", "\n", text)
        text = re.sub(r"(?is)</(td|th)>", " | ", text)
        text = re.sub(r"(?is)</(p|div|li|tr|section|article|h[1-6]|table|blockquote)>", "\n", text)
        text = re.sub(r"(?is)<li[^>]*>", "- ", text)
        # Drop remaining tags for a space, not for nothing: adjacent cells and inline
        # elements used to fuse into tokens that match neither word ("AlphaBeta").
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"(?m)^[ \t]*\|[ \t]*|[ \t]*\|[ \t]*$", "", text)
        text = re.sub(r"(?m)^[ \t]+", "", text)
        text = re.sub(r"\n{3,}", "\n\n", clean_text(text))
        return ConversionResult(f"# {title}\n\n{text}", self.name, title, {"encoding": encoding})
