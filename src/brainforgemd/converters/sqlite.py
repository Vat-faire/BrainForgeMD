from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote

from ..models import ConversionResult
from .base import Converter


class SqliteConverter(Converter):
    name = "sqlite"
    extensions = frozenset({".sqlite", ".sqlite3", ".db"})
    max_rows_per_table = 200
    max_cell_chars = 500

    @staticmethod
    def _cell(value: object) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bytes):
            return f"<BLOB {len(value)} bytes>"
        text = str(value).replace("\r", " ").replace("\n", " ")
        return text[: SqliteConverter.max_cell_chars].replace("|", "\\|")

    def convert(self, path: Path) -> ConversionResult:
        uri = f"file:{quote(str(path.resolve()))}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            lines = [f"# {path.name}", "", f"Tables: {len(tables)}", ""]
            for table in tables:
                safe_table = table.replace('"', '""')
                lines.extend([f"## Table `{table}`", ""])
                schema = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if schema and schema[0]:
                    lines.extend(["### Schema", "", "```sql", str(schema[0]), "```", ""])
                cursor = conn.execute(f'SELECT * FROM "{safe_table}" LIMIT ?', (self.max_rows_per_table + 1,))
                columns = [description[0] for description in cursor.description or []]
                rows = cursor.fetchall()
                truncated = len(rows) > self.max_rows_per_table
                rows = rows[: self.max_rows_per_table]
                if columns:
                    lines.append("| " + " | ".join(self._cell(c) for c in columns) + " |")
                    lines.append("| " + " | ".join("---" for _ in columns) + " |")
                    for row in rows:
                        lines.append("| " + " | ".join(self._cell(v) for v in row) + " |")
                if truncated:
                    lines.extend(["", f"> Rows truncated at {self.max_rows_per_table} for this table."])
                lines.append("")
            return ConversionResult("\n".join(lines).rstrip() + "\n", self.name, path.stem, {"tables": len(tables), "row_limit": self.max_rows_per_table})
        finally:
            conn.close()
