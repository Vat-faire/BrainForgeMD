# Privacy

*Read this in [French / en français](PRIVACY.fr.md).*

## Local-first design

BrainForgeMD is designed as a local-first conversion tool.

The core application does not intentionally upload source files, generated Markdown, manifests, chunks, graphs, or reports to a hosted BrainForgeMD service. There is no BrainForgeMD account system and no built-in telemetry service in the current project.

## Important distinction: BrainForgeMD vs optional dependencies

Optional parsers, OCR engines, transcription stacks, model runtimes, package managers, or model-download mechanisms may have their own network behavior.

Installing or using an optional dependency can therefore involve network access even though BrainForgeMD itself does not intentionally transmit source content.

Users processing sensitive material should review the behavior and configuration of every optional backend they enable.

## Generated output may be sensitive

A BrainForgeMD corpus can contain:

- the full extracted text of source documents;
- email headers and body content;
- table and database content;
- source-relative paths;
- filenames;
- hashes;
- timestamps and metadata;
- links and URLs found in documents;
- transcription or OCR output.

Generated output should be protected with the same care as the source material.

Do not assume that Markdown is less sensitive than the original file merely because it is easier to read.

## Public repositories and examples

Real personal, client, customer, confidential, or proprietary corpora should not be committed to this public repository.

Tests and examples should use synthetic, generated, or otherwise redistributable data.

## RAG and downstream systems

BrainForgeMD prepares data for downstream systems but does not control what those systems do with it.

If generated chunks, Markdown, or graph data are sent to a hosted vector database, embedding API, LLM provider, analytics system, or other service, that transfer is governed by the downstream system's privacy and retention policies.

Users are responsible for deciding whether a downstream service is appropriate for their data.

## Deletion

BrainForgeMD writes its generated corpus to the output directory selected by the user. Removing that directory removes the generated BrainForgeMD corpus, subject to normal operating-system behavior, backups, snapshots, synchronization software, and downstream copies.

BrainForgeMD cannot delete copies that have already been imported into external systems.

## Security

Privacy depends on the security of the local machine, output location, optional dependencies, and downstream systems.

See [SECURITY.md](SECURITY.md) for the project threat model and reporting guidance.

## AI-assisted development disclosure

The use of AI during software development does not mean user files are sent to an AI service by BrainForgeMD at runtime.

Development assistance and runtime data flow are separate concerns. See [AI_ASSISTANCE.md](AI_ASSISTANCE.md) for the development disclosure.
