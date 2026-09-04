from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import ConversionResult
from ..utils import fenced
from .base import Converter


class NotebookConverter(Converter):
    name = "jupyter"
    extensions = frozenset({".ipynb"})

    def convert(self, path: Path) -> ConversionResult:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells: list[dict[str, Any]] = notebook.get("cells", [])
        lines = [f"# {path.stem}", ""]
        code_cells = 0
        markdown_cells = 0
        for index, cell in enumerate(cells, start=1):
            cell_type = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", []))
            if cell_type == "markdown":
                markdown_cells += 1
                lines.extend([source.rstrip(), ""])
            elif cell_type == "code":
                code_cells += 1
                lines.extend([f"## Code cell {index}", "", fenced(source, "python").rstrip(), ""])
                outputs = cell.get("outputs", [])
                rendered: list[str] = []
                for output in outputs:
                    if "text" in output:
                        rendered.append("".join(output["text"]))
                    data = output.get("data", {})
                    if "text/plain" in data:
                        rendered.append("".join(data["text/plain"]))
                if rendered:
                    lines.extend(["### Saved output", "", fenced("\n".join(rendered), "text").rstrip(), ""])
            elif source.strip():
                lines.extend([f"## Cell {index} ({cell_type})", "", source.rstrip(), ""])
        return ConversionResult(
            "\n".join(lines).rstrip() + "\n",
            self.name,
            path.stem,
            {"cells": len(cells), "code_cells": code_cells, "markdown_cells": markdown_cells},
        )
