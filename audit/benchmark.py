"""Reproducible BrainForgeMD benchmark on generated corpora of growing size.

Everything is generated locally and deleted afterwards unless --keep is passed.
Measures wall time, throughput, peak process memory, output size, and the cost of a
second (incremental) pass.

Usage: python audit/benchmark.py <work-dir> [--sizes 100,1000,10000] [--keep]
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brainforgemd.pipeline import Pipeline, PipelineSettings

WORDS = ["provenance", "corpus", "ingestion", "markdown", "retrieval", "chunk", "graph", "manifest", "deterministic", "conversion", "pipeline", "document", "knowledge", "extraction", "identity", "hash", "section", "ordinal"]


def _peak_memory_mb() -> float:
    """Peak resident memory of this process, best effort across platforms."""
    try:
        import psutil

        info = psutil.Process().memory_info()
        return getattr(info, "peak_wset", info.rss) / 1e6
    except Exception:
        pass
    try:
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except Exception:
        return float("nan")


def _cpu_seconds() -> float:
    times = os.times()
    return times.user + times.system


def build_corpus(root: Path, count: int) -> int:
    """Generate a mixed corpus: text, markdown, code, json, csv, html, yaml."""
    root.mkdir(parents=True, exist_ok=True)
    total = 0
    for i in range(count):
        bucket = root / f"dir{i // 100:03d}"
        bucket.mkdir(exist_ok=True)
        kind = i % 7
        if kind == 0:
            body = " ".join(WORDS[(i + j) % len(WORDS)] for j in range(400))
            path = bucket / f"note{i}.txt"
        elif kind == 1:
            body = f"# Doc {i}\n\n" + " ".join(WORDS[(i + j) % len(WORDS)] for j in range(300))
            body += f"\n\n## Section\n\nSee [peer](note{max(i - 1, 0)}.txt) and https://example.test/{i}\n"
            path = bucket / f"doc{i}.md"
        elif kind == 2:
            body = "\n".join(f"def f{j}():\n    return {j}" for j in range(40))
            path = bucket / f"mod{i}.py"
        elif kind == 3:
            body = json.dumps({"id": i, "items": [{"n": j, "v": WORDS[j % len(WORDS)]} for j in range(40)]})
            path = bucket / f"data{i}.json"
        elif kind == 4:
            body = "name,value,note\n" + "\n".join(f"row{j},{j},{WORDS[j % len(WORDS)]}" for j in range(60))
            path = bucket / f"table{i}.csv"
        elif kind == 5:
            body = f"<html><head><title>Page {i}</title></head><body><h1>Page {i}</h1>" + "".join(
                f"<p>{WORDS[j % len(WORDS)]} paragraph {j}</p>" for j in range(30)
            ) + "</body></html>"
            path = bucket / f"page{i}.html"
        else:
            body = "\n".join(f"key{j}: {WORDS[j % len(WORDS)]}" for j in range(40))
            path = bucket / f"conf{i}.yaml"
        path.write_text(body, encoding="utf-8")
        total += len(body.encode("utf-8"))
    return total


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def run_case(work: Path, count: int, keep: bool) -> dict:
    source = work / f"corpus_{count}"
    out = work / f"out_{count}"
    for target in (source, out):
        if target.exists():
            shutil.rmtree(target)

    source_bytes = build_corpus(source, count)
    settings = PipelineSettings(chunk_chars=5000, overlap_chars=500)

    gc.collect()
    cpu0, t0 = _cpu_seconds(), time.perf_counter()
    first = Pipeline().run(source, out, settings)
    cold = time.perf_counter() - t0
    cold_cpu = _cpu_seconds() - cpu0
    peak = _peak_memory_mb()

    cpu1, t1 = _cpu_seconds(), time.perf_counter()
    second = Pipeline().run(source, out, settings)
    warm = time.perf_counter() - t1
    warm_cpu = _cpu_seconds() - cpu1

    result = {
        "files": count,
        "source_mb": round(source_bytes / 1e6, 2),
        "cold_sec": round(cold, 2),
        "cold_files_per_sec": round(count / cold, 1) if cold else 0,
        "cold_cpu_sec": round(cold_cpu, 2),
        "warm_sec": round(warm, 2),
        "warm_files_per_sec": round(count / warm, 1) if warm else 0,
        "warm_cpu_sec": round(warm_cpu, 2),
        "speedup": round(cold / warm, 2) if warm else 0,
        "peak_rss_mb": round(peak, 1),
        "out_mb": round(dir_size(out) / 1e6, 2),
        "chunks": first.chunks,
        "converted_cold": first.converted,
        "skipped_warm": second.skipped,
        "converted_warm": second.converted,
        "failed": first.failed,
    }
    if not keep:
        shutil.rmtree(source, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
    return result


def run_large_files(work: Path, keep: bool) -> list[dict]:
    """A few individually large files rather than many small ones."""
    results = []
    for mb in (5, 25, 100):
        source = work / f"big_{mb}"
        out = work / f"bigout_{mb}"
        for target in (source, out):
            if target.exists():
                shutil.rmtree(target)
        source.mkdir(parents=True)
        block = (" ".join(WORDS) + "\n") * 400
        target_bytes = mb * 1024 * 1024
        with (source / f"large_{mb}mb.txt").open("w", encoding="utf-8") as handle:
            written = 0
            while written < target_bytes:
                handle.write(block)
                written += len(block)
        gc.collect()
        t0 = time.perf_counter()
        stats = Pipeline().run(source, out, PipelineSettings(chunk_chars=5000, overlap_chars=500))
        elapsed = time.perf_counter() - t0
        results.append({
            "file_mb": mb,
            "sec": round(elapsed, 2),
            "mb_per_sec": round(mb / elapsed, 1) if elapsed else 0,
            "chunks": stats.chunks,
            "peak_rss_mb": round(_peak_memory_mb(), 1),
            "out_mb": round(dir_size(out) / 1e6, 2),
        })
        if not keep:
            shutil.rmtree(source, ignore_errors=True)
            shutil.rmtree(out, ignore_errors=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("work")
    parser.add_argument("--sizes", default="100,1000,10000")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]

    scaling = [run_case(work, count, args.keep) for count in sizes]
    large = run_large_files(work, args.keep)

    lines = ["## Scaling (mixed synthetic corpus)", ""]
    header = ["files", "source_mb", "cold_sec", "cold_files_per_sec", "warm_sec",
              "warm_files_per_sec", "speedup", "peak_rss_mb", "out_mb", "chunks"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in scaling:
        lines.append("| " + " | ".join(str(row[h]) for h in header) + " |")
    lines += ["", "## Single large files", ""]
    header2 = ["file_mb", "sec", "mb_per_sec", "chunks", "peak_rss_mb", "out_mb"]
    lines.append("| " + " | ".join(header2) + " |")
    lines.append("| " + " | ".join("---" for _ in header2) + " |")
    for row in large:
        lines.append("| " + " | ".join(str(row[h]) for h in header2) + " |")

    report = "\n".join(lines) + "\n"
    (work / "BENCHMARK.md").write_text(report, encoding="utf-8")
    (work / "benchmark.json").write_text(
        json.dumps({"scaling": scaling, "large_files": large}, indent=2), encoding="utf-8"
    )
    print(report)


if __name__ == "__main__":
    main()
