# RAG and GraphRAG Outputs

*Read this in [French / en français](RAG_OUTPUTS.fr.md).*

BrainForgeMD is intended to sit before a retrieval or graph system. It normalizes source material and packages provenance, chunks, and explicit structure; it does not try to replace the downstream RAG or GraphRAG stack.

## Recommended ingestion order

1. Read `manifest.jsonl` for source-level metadata, provenance, and upserts.
2. Embed or index `chunks.jsonl` for retrieval.
3. Load `nodes.jsonl` and `edges.jsonl` when the downstream system accepts a graph.
4. Keep `documents/**/*.md` as the normalized human-readable corpus.

## Chunking

The chunker prefers heading boundaries and paragraphs. Oversized sections are split into overlapping character windows.

Character limits are used rather than a model-specific tokenizer so the output remains deterministic and model-independent.

`approx_tokens` is a conservative character-based heuristic, not an exact tokenizer count. A downstream system tied to a specific embedding or generation model should re-tokenize before enforcing hard token limits.

## Stable chunk identity

Chunk IDs are derived from source identity, section placement, ordinal position, and chunk text. This is intended to support repeatable ingestion and downstream upserts while avoiding a new identity for unchanged content on every run.

## Graph schema

Current node types:

- `document`
- `chunk`
- `url`

Current edge types:

- `contains`: document → chunk
- `next`: chunk → chunk
- `links_to`: document/chunk → document when a local link can be resolved
- `references_url`: document/chunk → URL

## What the graph deliberately does not claim

The graph contains explicit structure only.

BrainForgeMD does not currently perform:

- semantic entity extraction;
- inferred relationship generation;
- embeddings;
- community detection;
- semantic summarization;
- graph-based ranking.

Those operations belong to the downstream GraphRAG layer, where the model, domain, and quality requirements are known.

This boundary is deliberate: the conversion layer should preserve evidence rather than manufacture semantic facts.

## Provenance

The Markdown front matter and `manifest.jsonl` preserve source-relative paths, hashes, stable identities, parser information, and other extraction metadata so downstream retrieval results can be traced back to the source material.

## Current validation level

The output packaging, structural graph behavior, chunking, and core pipeline are covered by automated tests. Integration quality with a specific vector database, graph database, embedding model, or GraphRAG framework is outside the current test matrix and should be validated by the downstream application.
