from __future__ import annotations

import json
import re
from typing import Any

# YAML rejects these code points outright, even inside a double-quoted scalar: the C0
# controls, DEL, the C1 block, the Unicode line/paragraph separators and a stray BOM.
# json.dumps escapes everything below 0x20 but leaves the rest raw, so a title carrying
# one of them (an email subject, an HTML <title>, a POSIX filename) produced front
# matter that no YAML parser would read back.
_YAML_FORBIDDEN_CODEPOINTS = [
    *range(0x00, 0x09),
    0x0B,
    0x0C,
    *range(0x0E, 0x20),
    *range(0x7F, 0xA0),
    0x2028,
    0x2029,
    0xFEFF,
]
_YAML_FORBIDDEN_RE = re.compile(
    "[" + "".join(re.escape(chr(code)) for code in _YAML_FORBIDDEN_CODEPOINTS) + "]"
)


def _escape_forbidden(rendered: str) -> str:
    return _YAML_FORBIDDEN_RE.sub(lambda match: f"\\u{ord(match.group(0)):04x}", rendered)


# A bare key that spells a YAML keyword is read back as a boolean or null instead of a
# string. The fields the pipeline emits are all plain identifiers, so this only quotes
# the keys whose meaning would actually change.
_PLAIN_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
_YAML_KEYWORDS = frozenset({"yes", "no", "true", "false", "on", "off", "null"})


def _yaml_key(key: str) -> str:
    if _PLAIN_KEY_RE.match(key) and key.lower() not in _YAML_KEYWORDS:
        return key
    return _escape_forbidden(json.dumps(key, ensure_ascii=False))


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _escape_forbidden(json.dumps(str(value), ensure_ascii=False))


def render_front_matter(fields: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, (dict, list, tuple)):
            # JSON is valid YAML and avoids unsafe/custom serializers.
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
            lines.append(f"{_yaml_key(key)}: {_escape_forbidden(rendered)}")
        else:
            lines.append(f"{_yaml_key(key)}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"
