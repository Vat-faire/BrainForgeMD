# Security Policy

*Read this in [French / en français](SECURITY.fr.md).*

## Supported versions

Security fixes are applied to the latest released minor version of BrainForgeMD.

## Input threat model

BrainForgeMD assumes that source files may be malformed, unexpected, or hostile.

The core converters are designed to:

- never execute notebook cells, macros, shell commands, source code, or embedded scripts;
- open SQLite databases in read-only mode;
- reject archive members that attempt to escape the extraction root;
- enforce archive nesting, file-count, and expanded-size limits;
- cap source file size before conversion;
- sanitize output filenames;
- keep generated content under the selected output root;
- isolate conversion failures whenever practical.

Optional conversion backends have their own parsers, models, native libraries, and dependency chains. Keep those components updated. Truly hostile or unknown files should be processed inside a sandbox, container, disposable virtual machine, or another isolated environment.

## Secrets and private data

The generated corpus can contain the complete textual content and metadata of the original files.

Treat BrainForgeMD output with the same confidentiality as the source material. BrainForgeMD itself does not intentionally upload source content or generated corpora.

Before sharing generated Markdown, manifests, chunks, reports, or graph files publicly, review them for private information, credentials, API keys, personal data, proprietary content, and sensitive metadata.

## Reporting a vulnerability

Please do not publish exploitable security details in a public issue.

When possible, open a private security advisory on the GitHub repository. Include:

- the affected version or commit;
- a minimal reproduction;
- the expected and actual behavior;
- the security impact;
- a suggested mitigation, if known.

Responsible disclosure is preferred so an issue can be reproduced and corrected without unnecessarily exposing users before a fix is available.

## AI-assisted development and security

AI assistance does not reduce the security standard applied to the project. AI-assisted changes are expected to be reviewed through the same code, test, CI, and documentation evidence as any other contribution.

See [AI_ASSISTANCE.md](AI_ASSISTANCE.md) for the project disclosure.
