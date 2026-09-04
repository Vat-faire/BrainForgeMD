# Architecture

BrainForgeMD separates **extraction**, **normalization**, **provenance**, **chunking**, and **graph packaging**.

```text
input discovery
    ↓
security limits
    ↓
converter registry ──→ builtin converter
    │                 docling backend
    │                 markitdown fallback
    ↓
normalized Markdown + extraction metadata
    ↓
provenance front matter
    ↓
mirrored .md output
    ↓
chunker ──→ chunks.jsonl
    ↓
structural graph ──→ nodes.jsonl / edges.jsonl
    ↓
manifest / index / report / incremental state
```

## Stable identities

Document identity is derived from the source-relative path; a separate version ID is derived from path plus content hash. Chunk identity is derived from document identity, section path, ordinal, and chunk text. This makes ingestion idempotent and supports downstream upserts.

## Converter order

1. Exact built-in converters for deterministic formats.
2. Docling for rich documents/media when installed.
3. MarkItDown fallback when installed.
4. Unsupported-file record if no converter accepts the source.

## Why a structural graph

Document conversion can reliably know containment, sequence, explicit file links, and URLs. It cannot reliably infer semantic entities or relationships without a separate model or domain-specific extractor. BrainForgeMD therefore emits a factual structural graph and leaves semantic enrichment to the downstream GraphRAG system.
