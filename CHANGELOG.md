# Changelog

*Read this in [French / en français](CHANGELOG.fr.md).*

All notable BrainForgeMD changes are documented here.

## 0.1.0 - 2026-09-04

### Added

- Recursive mixed-file to Markdown corpus pipeline.
- Stable document, version, and chunk identities with SHA-256 provenance.
- RAG chunk exports.
- Structural GraphRAG node and edge exports.
- Built-in converters for text, source code, structured data, tables, HTML, notebooks, email, subtitles, SQLite, Parquet, and safe archives.
- Optional Docling and MarkItDown backends for rich documents and media.
- Incremental conversion state for unchanged sources.
- Archive traversal, nesting-depth, file-count, and expanded-size protections.
- Self-output exclusion.
- Common build, cache, VCS, and environment directory exclusions.
- Symlink skipping by default.
- Cross-platform testing on Windows, macOS, and Linux.
- Python 3.11, 3.12, and 3.13 CI coverage.
- Automated package build workflow.
- English-first public documentation with French translations.
- Explicit AI-assisted development disclosure.

### Fixed before first public release

- Cross-platform archive path validation on Windows short-path aliases and macOS `/var` → `/private/var` path resolution.
- Ruff violations found by the first CI run.
- GitHub Actions runtime versions updated to Node 24-compatible actions.
- Installation documentation corrected to use the GitHub repository until a package registry release exists.

### Current release status

Version `0.1.0` is present in the source package metadata, but no tagged GitHub release and no PyPI package have been published yet.
