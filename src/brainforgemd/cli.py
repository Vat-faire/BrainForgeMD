from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path

from . import __version__
from .pipeline import Pipeline, PipelineSettings
from .registry import build_default_registry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brainforgemd",
        description="Forge mixed files into provenance-preserving Markdown corpora for RAG and GraphRAG.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="Convert a file or directory into a complete corpus")
    convert.add_argument("source", type=Path, help="Source file or directory")
    convert.add_argument("-o", "--output", type=Path, default=Path("context-out"), help="Output corpus directory")
    convert.add_argument("--chunk-chars", type=int, default=5000, help="Target chunk size in characters")
    convert.add_argument("--overlap-chars", type=int, default=500, help="Chunk overlap in characters")
    convert.add_argument("--max-file-mb", type=int, default=512, help="Reject individual files larger than this size")
    convert.add_argument("--no-incremental", action="store_true", help="Rebuild unchanged files")
    convert.add_argument("--strict", action="store_true", help="Stop on the first conversion error")
    convert.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any source failed to convert")
    convert.add_argument("--include-hidden", action="store_true", help="Include hidden path segments")

    sub.add_parser("formats", help="List registered format handlers")
    sub.add_parser("doctor", help="Show optional backend availability")
    sub.add_parser("version", help="Print version")
    return parser


def _cmd_convert(args: argparse.Namespace) -> int:
    source: Path = args.source
    if not source.exists():
        print(f"error: source does not exist: {source}", file=sys.stderr)
        return 2
    settings = PipelineSettings(
        chunk_chars=args.chunk_chars,
        overlap_chars=args.overlap_chars,
        max_file_mb=args.max_file_mb,
        incremental=not args.no_incremental,
        strict=args.strict,
        include_hidden=args.include_hidden,
    )
    try:
        stats = Pipeline().run(source, args.output, settings)
    except Exception as exc:
        print(f"error: conversion failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Done. converted={stats.converted} skipped={stats.skipped} "
        f"unsupported={stats.unsupported} failed={stats.failed} chunks={stats.chunks}"
    )
    print(f"Corpus: {args.output.resolve()}")
    if args.fail_on_error and (stats.failed or stats.unsupported):
        print(
            f"error: {stats.failed} failed and {stats.unsupported} unsupported source(s); "
            f"see {args.output / 'errors.jsonl'}",
            file=sys.stderr,
        )
        return 3
    return 0


def _cmd_formats() -> int:
    rows = build_default_registry().format_rows()
    width = max(len(name) for name, _, _ in rows)
    print("BrainForgeMD converters")
    for name, extensions, available in rows:
        marker = "  " if available else "! "
        print(f"{marker}{name:<{width}}  {extensions or 'dynamic'}")
    if any(not available for _, _, available in rows):
        print()
        print("! backend not installed on this machine; these extensions will be reported as failures")
    if not _module("whisper"):
        print()
        print("! audio/video require the [asr] extra; the transcription backend is not installed")
    return 0


def _module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _cmd_doctor() -> int:
    checks = [
        ("Docling rich documents/OCR", _module("docling")),
        ("ASR transcription (audio/video)", _module("whisper")),
        ("MarkItDown fallback", _module("markitdown")),
        ("Outlook MSG", _module("extract_msg")),
        ("Parquet", _module("pyarrow")),
        ("ffmpeg", shutil.which("ffmpeg") is not None),
        ("tesseract", shutil.which("tesseract") is not None),
    ]
    print(f"BrainForgeMD {__version__} — environment")
    width = max(len(name) for name, _ in checks)
    for name, available in checks:
        print(f"{name:<{width}}  {'available' if available else 'not found'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "convert":
        return _cmd_convert(args)
    if args.command == "formats":
        return _cmd_formats()
    if args.command == "doctor":
        return _cmd_doctor()
    if args.command == "version":
        print(__version__)
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
