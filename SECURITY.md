# Security policy

## Supported versions

Security fixes are applied to the latest released minor version.

## Input threat model

BrainForgeMD assumes source files may be malformed or hostile.

The core converters:

- never execute notebook cells, macros, shell commands, source code, or embedded scripts;
- open SQLite databases in read-only mode;
- reject archive members that escape the extraction root;
- enforce archive nesting, file-count, and expanded-byte limits;
- cap source file size before conversion;
- sanitize output filenames and keep converted output under the selected output root.

Optional conversion backends have their own parsers and dependencies. Keep them updated and process truly hostile files inside a sandbox or container.

## Secrets and private data

Conversion output can contain the complete textual content and metadata of the input. Treat the generated corpus with the same confidentiality as the original files. BrainForgeMD does not upload data by itself.

## Reporting a vulnerability

Open a private security advisory on the GitHub repository rather than a public issue when possible. Include the affected version, minimal reproduction, impact, and suggested mitigation if known.
