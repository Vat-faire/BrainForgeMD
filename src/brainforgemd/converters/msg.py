from __future__ import annotations

import importlib.util
from pathlib import Path

from ..models import ConversionResult
from .base import ConversionUnavailable, Converter


class MsgConverter(Converter):
    name = "outlook-msg"
    extensions = frozenset({".msg"})

    def available(self) -> bool:
        return importlib.util.find_spec("extract_msg") is not None

    def convert(self, path: Path) -> ConversionResult:
        try:
            import extract_msg
        except ImportError as exc:
            raise ConversionUnavailable("Outlook .msg support requires: pip install 'brainforgemd[msg]'") from exc
        message = extract_msg.Message(str(path))
        try:
            subject = message.subject or path.stem
            lines = [f"# {subject}", ""]
            for label, value in (("From", message.sender), ("To", message.to), ("Cc", message.cc), ("Date", message.date)):
                if value:
                    lines.append(f"**{label}:** {value}")
            lines.extend(["", "## Body", "", message.body or "_No textual body._", ""])
            attachments = list(message.attachments)
            if attachments:
                lines.extend(["## Attachments", ""])
                for attachment in attachments:
                    name = getattr(attachment, "longFilename", None) or getattr(attachment, "shortFilename", None) or "unnamed"
                    lines.append(f"- `{name}`")
                lines.append("")
            return ConversionResult("\n".join(lines).rstrip() + "\n", self.name, subject, {"attachments": len(attachments)})
        finally:
            message.close()
