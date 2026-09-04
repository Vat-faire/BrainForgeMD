from __future__ import annotations

import importlib.util
from pathlib import Path

from ..models import ConversionResult
from .base import ConversionUnavailable, Converter


class ParquetConverter(Converter):
    name = "parquet"
    extensions = frozenset({".parquet", ".pq"})
    max_rows = 200

    def available(self) -> bool:
        return importlib.util.find_spec("pyarrow") is not None

    def convert(self, path: Path) -> ConversionResult:
        try:
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise ConversionUnavailable("Parquet support requires: pip install 'brainforgemd[parquet]'") from exc
        table = pq.read_table(path)
        schema_text = str(table.schema)
        sample = table.slice(0, self.max_rows).to_pylist()
        columns = table.column_names
        lines = [f"# {path.name}", "", "## Schema", "", "```text", schema_text, "```", "", "## Sample", ""]
        if columns:
            lines.append("| " + " | ".join(c.replace("|", "\\|") for c in columns) + " |")
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
            for record in sample:
                values = [str(record.get(c, "")).replace("\n", " ").replace("|", "\\|")[:500] for c in columns]
                lines.append("| " + " | ".join(values) + " |")
        if table.num_rows > self.max_rows:
            lines.extend(["", f"> Sample truncated at {self.max_rows} rows from {table.num_rows} total rows."])
        return ConversionResult("\n".join(lines) + "\n", self.name, path.stem, {"rows": table.num_rows, "columns": len(columns), "sample_rows": min(table.num_rows, self.max_rows)})
