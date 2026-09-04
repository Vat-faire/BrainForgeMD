from __future__ import annotations

import re
from pathlib import Path

from ..models import ConversionResult
from ..utils import clean_text, decode_text
from .base import Converter


class SubtitleConverter(Converter):
    name = "subtitles"
    extensions = frozenset({".srt", ".vtt"})

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        text = clean_text(text)
        if path.suffix.lower() == ".vtt":
            text = re.sub(r"^WEBVTT[^\n]*\n+", "", text)
        blocks = re.split(r"\n\s*\n", text.strip())
        out = [f"# {path.stem}", "", "## Transcript", ""]
        cues = 0
        for block in blocks:
            lines = [line for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            if lines[0].isdigit():
                lines = lines[1:]
            if not lines:
                continue
            timing = lines[0] if "-->" in lines[0] else ""
            cue_text = " ".join(lines[1:] if timing else lines).strip()
            if cue_text:
                cues += 1
                out.append(f"- **{timing}** {cue_text}" if timing else f"- {cue_text}")
        return ConversionResult("\n".join(out) + "\n", self.name, path.stem, {"encoding": encoding, "cues": cues})
