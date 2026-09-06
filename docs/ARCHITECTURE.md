# Architecture

*Read this in [French / en français](ARCHITECTURE.fr.md).*

BrainForgeMD separates **discovery**, **security limits**, **extraction**, **normalization**, **provenance**, **chunking**, and **graph packaging** so each stage can be inspected independently.

```text
input discovery
    ↓
security limits
    ↓
converter registry ──→ built-in converter
    │                 Docling backend
    │                 MarkItDown fallback
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

Document identity is derived from the source-relative path. A separate version ID is derived from the path plus the content hash. Chunk identity is derived from the document identity, section path, ordinal position, and chunk text.

This separation is intended to keep repeated ingestion idempotent and allow downstream systems to upsert changed material without treating every run as an entirely new corpus.

## Converter order

The default registry follows this order:

1. exact built-in converters for deterministic formats;
2. Docling for supported rich documents and media when installed;
3. MarkItDown as an optional fallback when installed;
4. an unsupported-file record when no converter accepts the source.

The goal is to use the simplest deterministic parser that can correctly represent the source before falling back to heavier general-purpose parsers.

## Structural graph by design

A converter can reliably observe explicit structure such as containment, chunk order, local links, and URLs. It cannot reliably infer people, organizations, events, communities, or semantic relationships without a separate model or domain-specific extraction layer.

BrainForgeMD therefore emits a factual structural graph and leaves semantic enrichment to downstream GraphRAG systems. An incomplete factual graph is preferable to a richer graph that silently invents relationships.

## System boundary

BrainForgeMD is an **ingestion and normalization layer**. It is not intended to replace:

- a vector database;
- an embedding model;
- a graph database;
- entity extraction;
- community detection;
- a reranker;
- an LLM orchestration framework.

It creates a stable, traceable corpus those systems can consume.

## Trust boundary

Source files are treated as untrusted. The pipeline should not execute source content. Archive handling, database access, output paths, and optional parser integration are security-sensitive boundaries and should remain independently testable.

See [../SECURITY.md](../SECURITY.md).

## Development transparency

The architecture and implementation were developed with AI assistance under Sd-tech-Sol's direction. The relevant disclosure is in [../AI_ASSISTANCE.md](../AI_ASSISTANCE.md). The technical claims in this document are intended to be verifiable from the code and tests rather than from the development method.
