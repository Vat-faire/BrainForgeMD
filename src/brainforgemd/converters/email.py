from __future__ import annotations

import contextlib
import email
import html
import re
from email import policy
from pathlib import Path

from ..models import ConversionResult
from .base import Converter
from .text import strip_non_content_elements


class EmlConverter(Converter):
    name = "email-eml"
    extensions = frozenset({".eml"})

    def convert(self, path: Path) -> ConversionResult:
        message = email.message_from_bytes(path.read_bytes(), policy=policy.default)
        subject = str(message.get("subject") or path.stem)
        lines = [f"# {subject}", ""]
        for header in ("From", "To", "Cc", "Date", "Message-ID", "In-Reply-To", "References"):
            value = message.get(header)
            if value:
                lines.append(f"**{header}:** {value}")
        lines.append("")
        text_parts: list[str] = []
        html_parts: list[str] = []
        attachments: list[tuple[str, str, int]] = []
        parts = message.walk() if message.is_multipart() else [message]
        for part in parts:
            disposition = part.get_content_disposition()
            filename = part.get_filename()
            content_type = part.get_content_type()
            if disposition == "attachment" or filename:
                payload = part.get_payload(decode=True) or b""
                attachments.append((filename or "unnamed", content_type, len(payload)))
                continue
            if content_type == "text/plain":
                try:
                    text_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    text_parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
            elif content_type == "text/html":
                with contextlib.suppress(Exception):
                    html_parts.append(part.get_content())
        body = "\n\n".join(text_parts).strip()
        if not body and html_parts:
            raw = "\n".join(html_parts)
            raw = strip_non_content_elements(raw)
            raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
            raw = re.sub(r"(?is)</p>", "\n\n", raw)
            body = html.unescape(re.sub(r"(?is)<[^>]+>", "", raw)).strip()
        lines.extend(["## Body", "", body or "_No textual body._", ""])
        if attachments:
            lines.extend(["## Attachments", ""])
            for filename, content_type, size in attachments:
                lines.append(f"- `{filename}` — `{content_type}` — {size} bytes")
            lines.append("")
        return ConversionResult("\n".join(lines).rstrip() + "\n", self.name, subject, {"attachments": len(attachments)})
