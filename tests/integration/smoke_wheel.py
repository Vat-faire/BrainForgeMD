from __future__ import annotations

import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def _python(env: Path) -> Path:
    if os.name == "nt":
        return env / "Scripts" / "python.exe"
    return env / "bin" / "python"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    wheels = sorted((root / "dist").glob("brainforgemd-*.whl"))
    if not wheels:
        raise SystemExit("No BrainForgeMD wheel found in dist/")
    wheel = wheels[-1]

    with tempfile.TemporaryDirectory(prefix="bfmd-wheel-smoke-") as tmp:
        temp = Path(tmp)
        env = temp / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(env)
        python = _python(env)
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel)],
            check=True,
        )
        version = subprocess.run(
            [str(python), "-m", "brainforgemd.cli", "version"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if version != "0.1.0":
            raise SystemExit(f"Unexpected installed version: {version}")

        source = temp / "source"
        output = temp / "out"
        source.mkdir()
        (source / "hello.txt").write_text("BrainForgeMD clean wheel smoke test.\n", encoding="utf-8")
        subprocess.run(
            [
                str(python),
                "-m",
                "brainforgemd.cli",
                "convert",
                str(source),
                "-o",
                str(output),
                "--strict",
            ],
            check=True,
        )

        manifest = [
            json.loads(line)
            for line in (output / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        if len(manifest) != 1:
            raise SystemExit(f"Expected one manifest record, got {len(manifest)}")
        record = manifest[0]
        if record["source_path"] != "hello.txt" or record["parser"] != "text":
            raise SystemExit(f"Unexpected manifest record: {record}")
        markdown = (output / record["output_path"]).read_text(encoding="utf-8")
        if "BrainForgeMD clean wheel smoke test" not in markdown:
            raise SystemExit("Converted Markdown did not preserve fixture content")
        state = json.loads((output / ".brainforgemd" / "state.json").read_text(encoding="utf-8"))
        if state["version"] != 1:
            raise SystemExit("Incremental state file is invalid")

    print(f"Clean-wheel smoke test passed with {wheel.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
