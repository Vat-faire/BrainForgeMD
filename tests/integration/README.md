# Deep validation suite

This directory contains the reproducible integration tests used to verify BrainForgeMD beyond unit tests.

All fixtures are generated synthetically during the test run. No private user data, personal documents, client data, or copied real-world corpus belongs in this suite.

The validation suite is deliberately strict: a claimed capability should fail loudly when it cannot be reproduced. It exercises:

- end-to-end mixed-corpus conversion;
- provenance metadata and SHA-256 hashes;
- stable RAG chunks and structural GraphRAG exports;
- incremental/idempotent second runs;
- self-output exclusion;
- ZIP/TAR traversal refusal and archive resource limits;
- clean installation from a built wheel on Windows, macOS, and Linux;
- optional rich-format conversion using the full local backend stack.

The rich-format job generates real synthetic containers for PDF, DOCX, PPTX, XLSX, PNG/OCR, EPUB, Parquet, WAV audio, and MP4 video before sending them through the normal BrainForgeMD pipeline.

The public evidence and current limits are summarized in [`../../VALIDATION.md`](../../VALIDATION.md).
