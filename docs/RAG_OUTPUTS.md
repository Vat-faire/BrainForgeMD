# RAG and GraphRAG outputs

## Recommended ingestion order

1. Read `manifest.jsonl` for source-level metadata and upserts.
2. Embed/index `chunks.jsonl` for retrieval.
3. Load `nodes.jsonl` and `edges.jsonl` if the downstream system accepts a graph.
4. Use `documents/**/*.md` as the human-readable source of truth.

## Chunking

The chunker prefers heading boundaries and paragraphs. Oversized sections are split into overlapping character windows. Character limits are used rather than a model-specific tokenizer so output remains deterministic and model-independent.

`approx_tokens` uses a conservative character heuristic and is not a tokenizer count. Downstream systems with a fixed embedding model should re-tokenize before enforcing hard token limits.

## Graph schema

Node types:

- `document`
- `chunk`
- `url`

Edge types:

- `contains`: document → chunk
- `next`: chunk → chunk
- `links_to`: document/chunk → document where a local link can be resolved
- `references_url`: document/chunk → URL

The graph contains explicit structure only. Entity extraction, community detection, summaries, embeddings and semantic relationships belong to the GraphRAG layer.
