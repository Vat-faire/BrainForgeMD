# Changelog / Journal des changements

[English](#english) · [Français](#français)

---

# English

I document notable BrainForgeMD changes here so users can quickly see what changed between versions.

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

### Fixed before first release

- Cross-platform archive path validation on Windows short-path aliases and macOS `/var` → `/private/var` path resolution.
- Ruff lint violations found by the first CI run.
- GitHub Actions runtime versions updated to current Node 24-compatible actions.
- Installation documentation corrected to use the GitHub repository until a package registry release exists.

---

# Français

Je documente ici les changements importants de BrainForgeMD pour qu’il soit facile de voir ce qui a changé entre les versions.

## 0.1.0 - 2026-09-04

### Ajouts

- Pipeline récursif permettant de transformer des ensembles de fichiers variés en corpus Markdown.
- Identifiants stables pour les documents, versions et chunks avec provenance SHA-256.
- Export des chunks pour le RAG.
- Export des nœuds et relations d’un graphe structurel pour GraphRAG.
- Convertisseurs intégrés pour le texte, le code source, les données structurées, les tableaux, HTML, notebooks, courriels, sous-titres, SQLite, Parquet et les archives sécurisées.
- Moteurs optionnels Docling et MarkItDown pour les documents et médias riches.
- État de conversion incrémentale pour ignorer les sources inchangées.
- Protections contre la traversée de chemins, la profondeur excessive, le nombre de fichiers et la taille décompressée des archives.
- Exclusion automatique du propre dossier de sortie.
- Exclusion des dossiers courants de build, cache, contrôle de version et environnements.
- Liens symboliques ignorés par défaut.
- Tests multiplateformes sous Windows, macOS et Linux.
- Couverture CI pour Python 3.11, 3.12 et 3.13.
- Workflow automatisé de construction du package.

### Correctifs avant la première version

- Validation des chemins d’archives corrigée pour les alias de chemins courts Windows et la résolution `/var` → `/private/var` de macOS.
- Problèmes Ruff détectés par la première exécution CI corrigés.
- Actions GitHub mises à jour vers des versions actuelles compatibles Node 24.
- Documentation d’installation corrigée pour utiliser directement le dépôt GitHub tant qu’aucune publication dans un registre de packages n’existe.
