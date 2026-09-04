from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path
from xml.etree import ElementTree

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
        value = value.replace("\r", " ").replace("\n", " ").strip()
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
        rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
        if not rows:
            return ConversionResult(f"# {path.name}\n\n_Empty table._\n", self.name, path.stem, {"encoding": encoding, "rows": 0})
        rows = [row[: self.max_columns] for row in rows[: self.max_rows]]
        width = max(len(row) for row in rows)
        padded = [row + [""] * (width - len(row)) for row in rows]
        header = padded[0]
        body = padded[1:]
        out = [f"# {path.name}", "", "| " + " | ".join(self._cell(v) for v in header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
        out.extend("| " + " | ".join(self._cell(v) for v in row) + " |" for row in body)
        truncated = len(list(csv.reader(text.splitlines(), delimiter=delimiter))) > self.max_rows
        if truncated:
            out.extend(["", f"> Output truncated at {self.max_rows} rows."])
        return ConversionResult("\n".join(out) + "\n", self.name, path.stem, {"encoding": encoding, "rows_emitted": len(rows), "columns": width, "truncated": truncated})


class XmlConverter(Converter):
    name = "xml"
    extensions = frozenset({".xml", ".xsd", ".svg"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        try:
            ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise ValueError(f"Invalid XML: {exc}") from exc
        return ConversionResult(f"# {path.name}\n\n" + fenced(clean_text(text), "xml"), self.name, path.stem, {"encoding": encoding})


class HtmlConverter(Converter):
    name = "html"
    extensions = frozenset({".html", ".htm", ".xhtml"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        # Dependency-free conservative extraction: remove scripts/styles, preserve links/headings/paragraphs.
        text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\\1>", "", text)
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1)).strip()) if title_match else path.stem
        for level in range(6, 0, -1):
            text = re.sub(
                fr"(?is)<h{level}[^>]*>(.*?)</h{level}>",
                lambda m, level=level: "\n" + "#" * level + " " + re.sub(r"<[^>]+>", "", m.group(1)).strip() + "\n",
                text,
            )
        text = re.sub(r'(?is)<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', lambda m: f"[{re.sub(r'<[^>]+>', '', m.group(2)).strip()}]({m.group(1)})", text)
        text = re.sub(r"(?is)<br\s*/?>", "\n", text)
        text = re.sub(r"(?is)</(p|div|li|tr|section|article)>", "\n", text)
        text = re.sub(r"(?is)<li[^>]*>", "- ", text)
        text = re.sub(r"(?is)<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub(r"\n{3,}", "\n\n", clean_text(text))
        return ConversionResult(f"# {title}\n\n{text}", self.name, title, {"encoding": encoding})
