# BrainForgeMD Project Vision

*Read this in [French / en français](PROJECT_VISION.fr.md).*

## Purpose

BrainForgeMD exists to make heterogeneous local information easier to turn into durable, auditable context for AI and search systems.

The project is based on a simple observation: useful RAG, GraphRAG, second-brain, and long-context systems need more than extracted text. They need provenance, stable identity, updateability, structure, and clear failure reporting.

## Product direction

The long-term direction is to make BrainForgeMD a dependable **ingestion layer** between real-world files and downstream knowledge systems.

The project should be able to take a mixed corpus and produce a normalized package that is:

- readable as Markdown;
- traceable to original sources;
- suitable for retrieval indexing;
- suitable for structural graph ingestion;
- repeatable across runs;
- explicit about unsupported or failed inputs;
- local-first by default;
- extensible without turning the core into an unmaintainable collection of special cases.

## What BrainForgeMD should become

The intended direction includes:

- broader format coverage through deterministic converters and optional specialized backends;
- stronger real-world fixture testing for PDF, Office, OCR, image, audio, and video inputs;
- reproducible extraction-quality benchmarks;
- documented corpus schema versioning;
- stronger compatibility tests across optional backend versions;
- better plugin interfaces for specialized formats;
- release artifacts that are easy to install and verify;
- examples for common RAG and GraphRAG ingestion stacks;
- continued cross-platform verification.

## What BrainForgeMD should not become

BrainForgeMD should not silently absorb every downstream AI responsibility.

The conversion layer should not become a hidden semantic inference engine. Entity extraction, embeddings, semantic relationships, community detection, model-specific summarization, retrieval ranking, and application-specific orchestration belong in downstream layers unless a future feature is explicitly optional and clearly separated from deterministic conversion.

It should also not claim support merely because a parser can technically open a file. Support should mean that useful output can be produced and its limitations can be explained.

## Quality principles

The project should prefer:

1. verifiable behavior over impressive claims;
2. explicit limitations over hidden uncertainty;
3. deterministic extraction over unnecessary inference;
4. source provenance over detached text;
5. partial but clearly reported results over fabricated completeness;
6. tests and reproducible evidence over trust in implementation method;
7. a small understandable core over dependency-heavy defaults.

## Privacy direction

BrainForgeMD is intended for corpora that may contain private, professional, or sensitive information. The default design should therefore remain local-first and avoid requiring a hosted service or account for core conversion.

Optional dependencies may have their own model-download or runtime requirements, but BrainForgeMD itself should not introduce hidden telemetry or silent source uploads.

See [PRIVACY.md](PRIVACY.md).

## Development model

The project is directed and maintained by **Sd-tech-Sol** and has been developed with AI assistance.

The idea, priorities, approvals, scope, and final decisions are attributed to Sd-tech-Sol. OpenAI ChatGPT has been used as a development tool for architecture, implementation, testing, debugging, review, documentation, and repository work.

The development method does not replace verification. The project should be judged through its code, tests, CI results, documented limits, and behavior.

See [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

## Current stage

BrainForgeMD is currently an early pre-release project. The deterministic core is tested across the CI matrix, but broad real-world validation of optional rich-document and media backends remains future work.

No tagged GitHub release or PyPI package has been published yet.
