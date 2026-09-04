# BrainForgeMD

**Turn mixed files into a clean, traceable Markdown corpus for RAG, GraphRAG, search, knowledge bases, and long-lived AI context.**

[English](#english) · [Français](#français)

---

# English

## Why I built BrainForgeMD

I built BrainForgeMD for a simple reason: AI knowledge systems are only as useful as the context they can ingest reliably.

Real-world folders are messy. They contain PDFs, Office documents, source code, email, spreadsheets, databases, archives, images, audio, video, notes, exports, and many other formats. Converting those files to plain text is not enough. For RAG, GraphRAG, second-brain systems, search, and durable AI memory, I also want to preserve **where the information came from, which version it belongs to, how it was split, and how the pieces relate to each other**.

BrainForgeMD is my attempt to make that ingestion layer practical, auditable, local-first, and extensible.

It is not just a file-to-Markdown converter. It builds a reusable corpus with stable identities, source hashes, normalized Markdown, RAG chunks, a structural graph, manifests, indexes, reports, and incremental state.

## What it produces

Given a folder like this:

```text
knowledge/
├── contracts/report.pdf
├── meetings/briefing.mp3
├── photos/whiteboard.jpg
├── data/customers.csv
├── code/parser.py
└── mail/thread.eml
```

BrainForgeMD creates a corpus like this:

```text
context-out/
├── documents/                  # Markdown mirroring the source tree
├── INDEX.md                    # human/agent-friendly corpus index
├── REPORT.md                   # conversion summary
├── manifest.jsonl              # provenance record for every source
├── chunks.jsonl                # stable RAG chunks
├── nodes.jsonl                 # structural graph nodes
├── edges.jsonl                 # structural graph edges
├── errors.jsonl                # isolated conversion failures
└── .brainforgemd/state.json    # incremental conversion state
```

Every converted Markdown document starts with YAML-compatible front matter containing provenance such as the stable source ID, source-relative path, SHA-256 hash, MIME type, file size, parser/backend, and extraction metadata.

## Main goals

I designed BrainForgeMD around a few rules:

- **Preserve provenance first.** A useful corpus should always be traceable back to its source.
- **Stay local-first.** BrainForgeMD itself does not upload files or send telemetry.
- **Keep deterministic formats deterministic.** Text, code, structured data, email, SQLite, archives, and similar formats use built-in converters where possible.
- **Use specialized backends for rich media.** Docling is the primary optional backend, with MarkItDown available as a fallback.
- **Generate RAG-ready outputs.** Stable chunks include source identity, section placement, approximate token counts, hashes, and overlap.
- **Generate a factual GraphRAG base.** The structural graph records explicit relationships without inventing semantic entities.
- **Make repeated runs efficient.** Unchanged sources can be skipped through incremental state.
- **Isolate failures.** One damaged or unsupported file should not destroy an entire batch unless strict mode is explicitly requested.
- **Treat input as untrusted.** Archives, databases, scripts, notebooks, and embedded content are handled conservatively.
- **Stay extensible.** New converters can be added without rebuilding the entire pipeline.

## Installation

### Core install from GitHub

The core package has no mandatory third-party runtime dependency and is useful for text, code, structured data, email, notebooks, SQLite, archives, and other built-in formats.

```bash
pip install "brainforgemd @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

### Full document and media stack

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

### Development install

```bash
git clone https://github.com/Vat-faire/BrainForgeMD.git
cd BrainForgeMD
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[all,dev]"
```

Some OCR and transcription paths may require models or native libraries used by the selected optional backend. The installed machine is always the source of truth:

```bash
brainforgemd doctor
brainforgemd formats
```

## Quick start

Convert one file:

```bash
brainforgemd convert report.pdf -o context-out
```

Convert an entire folder recursively:

```bash
brainforgemd convert ./knowledge -o ./context-out
```

Use smaller RAG chunks:

```bash
brainforgemd convert ./knowledge -o ./context-out --chunk-chars 3500 --overlap-chars 400
```

Force a complete rebuild instead of using incremental state:

```bash
brainforgemd convert ./knowledge -o ./context-out --no-incremental
```

## Corpus contract

### Markdown front matter

A converted document begins with fields similar to:

```yaml
---
brainforgemd: "0.1.0"
source_id: "src_..."
source_path: "contracts/report.pdf"
source_version_id: "ver_..."
source_name: "report.pdf"
source_extension: ".pdf"
mime_type: "application/pdf"
size_bytes: 482193
sha256: "..."
parser: "docling"
title: "report"
---
```

### `manifest.jsonl`

One JSON object per source. I use this as the provenance ledger and as the simplest document-level ingestion point for systems that support upserts.

### `chunks.jsonl`

One JSON object per chunk, including:

- `chunk_id`
- `source_id`
- `source_path`
- `ordinal`
- `section_path`
- `text`
- `char_count`
- `approx_tokens`
- `sha256`

Chunk IDs remain stable while the source identity, section placement, ordinal, and chunk text remain unchanged.

### `nodes.jsonl` and `edges.jsonl`

The graph is intentionally structural rather than speculative. It can contain document, chunk, and URL nodes with relationships such as:

- `contains`
- `next`
- `links_to`
- `references_url`

I deliberately leave semantic entity extraction, community detection, embeddings, inferred relations, and model-generated summaries to downstream GraphRAG systems. The conversion layer should not invent facts.

## Built-in format families

The dependency-light core directly handles formats such as:

- **Text:** `.txt`, `.md`, `.markdown`, `.rst`, `.log`
- **Source code and scripts:** Python, JavaScript/TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, shell, PowerShell, SQL, infrastructure and configuration files
- **Structured text:** `.json`, `.jsonl`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.xml`
- **Tables:** `.csv`, `.tsv`
- **Web:** `.html`, `.htm`
- **Notebooks:** `.ipynb`
- **Email:** `.eml`
- **Subtitles:** `.srt`, `.vtt`
- **SQLite:** `.sqlite`, `.sqlite3`, `.db`
- **Archives:** `.zip`, `.tar`, `.tgz`, `.tar.gz`, `.tar.bz2`, `.tar.xz`

Optional backends extend this to rich document and media families such as PDF, Word, Excel, PowerPoint, OpenDocument, images/OCR, audio/video transcription, EPUB, LaTeX, and additional formats supported by the installed backend versions.

See [docs/FORMAT_SUPPORT.md](docs/FORMAT_SUPPORT.md) for details.

## RAG and GraphRAG

BrainForgeMD is designed to sit **before** the vector database, search engine, graph database, or AI framework.

A typical ingestion flow is:

1. read `manifest.jsonl` for source-level provenance and upserts;
2. embed or index `chunks.jsonl` for retrieval;
3. load `nodes.jsonl` and `edges.jsonl` when a graph is useful;
4. keep `documents/**/*.md` as the readable normalized corpus.

More details are in [docs/RAG_OUTPUTS.md](docs/RAG_OUTPUTS.md).

## Security model

I treat every input file as potentially malformed or hostile.

BrainForgeMD does not intentionally execute source code, shell commands, notebook cells, macros, or embedded scripts. SQLite databases are opened read-only. Archive extraction is bounded and path-safe. Source size, archive depth, file count, and expanded size are limited.

Optional parsers have their own dependency and security surfaces, so hostile corpora should still be processed in an isolated environment.

See [SECURITY.md](SECURITY.md).

## Project philosophy

1. Preserve provenance before optimizing text.
2. Keep conversion deterministic whenever possible.
3. Never silently invent missing content.
4. Prefer partial, clearly identified extraction over opaque failure.
5. Keep semantic inference out of the conversion layer.
6. Produce outputs that are useful to humans and machines at the same time.
7. Keep the project understandable enough that other people can extend it safely.

## Contributing

Contributions are welcome. I prefer focused changes, tests for new behavior, clear documentation, and backwards-compatible output contracts whenever possible.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

BrainForgeMD is released under the **MIT License**.

Copyright (c) 2026 **Vat-faire**.

See [LICENSE](LICENSE).

---

# Français

## Pourquoi j’ai créé BrainForgeMD

J’ai créé BrainForgeMD pour une raison simple : un système de connaissances pour l’IA n’est réellement utile que s’il peut ingérer son contexte de façon fiable.

Dans la vraie vie, les dossiers sont rarement propres. On y retrouve des PDF, des documents Office, du code source, des courriels, des feuilles de calcul, des bases de données, des archives, des images, de l’audio, de la vidéo, des notes, des exports et plusieurs autres formats. Transformer tout ça en texte brut ne suffit pas. Pour du RAG, du GraphRAG, un second cerveau, de la recherche ou une mémoire durable pour l’IA, je veux aussi conserver **la provenance, la version du fichier, la façon dont le contenu a été découpé et les relations entre les éléments**.

BrainForgeMD est ma façon de construire cette couche d’ingestion de manière pratique, vérifiable, locale et extensible.

Ce n’est donc pas seulement un convertisseur de fichiers vers Markdown. Le programme construit un corpus réutilisable avec des identifiants stables, des empreintes des sources, du Markdown normalisé, des chunks pour le RAG, un graphe structurel, des manifestes, des index, des rapports et un état incrémental.

## Ce que BrainForgeMD produit

À partir d’un dossier comme celui-ci :

```text
knowledge/
├── contracts/report.pdf
├── meetings/briefing.mp3
├── photos/whiteboard.jpg
├── data/customers.csv
├── code/parser.py
└── mail/thread.eml
```

BrainForgeMD crée un corpus de ce type :

```text
context-out/
├── documents/                  # Markdown qui reflète l’arborescence source
├── INDEX.md                    # index lisible par un humain ou un agent
├── REPORT.md                   # résumé de la conversion
├── manifest.jsonl              # provenance de chaque source
├── chunks.jsonl                # chunks RAG stables
├── nodes.jsonl                 # nœuds du graphe structurel
├── edges.jsonl                 # relations du graphe structurel
├── errors.jsonl                # erreurs de conversion isolées
└── .brainforgemd/state.json    # état de conversion incrémentale
```

Chaque document Markdown converti commence par un front matter compatible YAML qui contient notamment l’identifiant stable de la source, son chemin relatif, son SHA-256, son type MIME, sa taille, le parseur utilisé et les métadonnées d’extraction.

## Mes objectifs principaux

J’ai conçu BrainForgeMD autour de quelques règles :

- **Conserver la provenance avant tout.** Un corpus utile doit toujours pouvoir être retracé jusqu’à sa source.
- **Rester local-first.** BrainForgeMD n’envoie pas les fichiers ailleurs et n’ajoute pas de télémétrie de son côté.
- **Garder les formats déterministes réellement déterministes.** Le texte, le code, les données structurées, les courriels, SQLite, les archives et les formats semblables utilisent des convertisseurs intégrés lorsque c’est possible.
- **Utiliser des moteurs spécialisés pour les médias riches.** Docling est le moteur optionnel principal et MarkItDown peut servir de solution de repli.
- **Produire directement des sorties adaptées au RAG.** Les chunks conservent l’identité de la source, la section, un compte approximatif de jetons, les empreintes et le chevauchement.
- **Donner une base factuelle au GraphRAG.** Le graphe structurel décrit des relations explicites sans inventer d’entités sémantiques.
- **Rendre les passages répétés efficaces.** Les fichiers inchangés peuvent être ignorés grâce à l’état incrémental.
- **Isoler les erreurs.** Un fichier brisé ou non supporté ne devrait pas faire échouer tout un lot, sauf si le mode strict est demandé.
- **Considérer les entrées comme non fiables.** Les archives, bases de données, scripts, notebooks et contenus intégrés sont traités de façon conservatrice.
- **Rester extensible.** On peut ajouter de nouveaux convertisseurs sans réécrire tout le pipeline.

## Installation

### Installation du noyau depuis GitHub

Le noyau n’a aucune dépendance tierce obligatoire à l’exécution. Il couvre notamment le texte, le code, les données structurées, les courriels, les notebooks, SQLite et les archives.

```bash
pip install "brainforgemd @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

### Installation complète documents et médias

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

### Installation pour le développement

```bash
git clone https://github.com/Vat-faire/BrainForgeMD.git
cd BrainForgeMD
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[all,dev]"
```

Certains chemins OCR ou de transcription peuvent demander des modèles ou des bibliothèques natives utilisés par les moteurs optionnels. La machine installée reste toujours la référence :

```bash
brainforgemd doctor
brainforgemd formats
```

## Démarrage rapide

Convertir un seul fichier :

```bash
brainforgemd convert report.pdf -o context-out
```

Convertir récursivement tout un dossier :

```bash
brainforgemd convert ./knowledge -o ./context-out
```

Utiliser de plus petits chunks RAG :

```bash
brainforgemd convert ./knowledge -o ./context-out --chunk-chars 3500 --overlap-chars 400
```

Forcer une reconstruction complète sans utiliser l’état incrémental :

```bash
brainforgemd convert ./knowledge -o ./context-out --no-incremental
```

## Contrat du corpus

### Front matter Markdown

Un document converti commence avec des champs semblables à ceux-ci :

```yaml
---
brainforgemd: "0.1.0"
source_id: "src_..."
source_path: "contracts/report.pdf"
source_version_id: "ver_..."
source_name: "report.pdf"
source_extension: ".pdf"
mime_type: "application/pdf"
size_bytes: 482193
sha256: "..."
parser: "docling"
title: "report"
---
```

### `manifest.jsonl`

Un objet JSON par source. Je l’utilise comme registre de provenance et comme point d’entrée simple pour les systèmes capables de faire des upserts au niveau document.

### `chunks.jsonl`

Un objet JSON par chunk, incluant notamment :

- `chunk_id`
- `source_id`
- `source_path`
- `ordinal`
- `section_path`
- `text`
- `char_count`
- `approx_tokens`
- `sha256`

Les identifiants de chunks demeurent stables tant que l’identité de la source, la position dans les sections, l’ordre et le texte du chunk restent les mêmes.

### `nodes.jsonl` et `edges.jsonl`

Le graphe est volontairement structurel plutôt que spéculatif. Il peut contenir des nœuds de type document, chunk et URL avec des relations comme :

- `contains`
- `next`
- `links_to`
- `references_url`

Je laisse volontairement l’extraction d’entités sémantiques, la détection de communautés, les embeddings, les relations inférées et les résumés générés aux systèmes GraphRAG en aval. La couche de conversion ne devrait pas inventer de faits.

## Familles de formats intégrées

Le noyau léger prend directement en charge des formats comme :

- **Texte :** `.txt`, `.md`, `.markdown`, `.rst`, `.log`
- **Code source et scripts :** Python, JavaScript/TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, shell, PowerShell, SQL, infrastructure et fichiers de configuration
- **Texte structuré :** `.json`, `.jsonl`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.xml`
- **Tableaux :** `.csv`, `.tsv`
- **Web :** `.html`, `.htm`
- **Notebooks :** `.ipynb`
- **Courriel :** `.eml`
- **Sous-titres :** `.srt`, `.vtt`
- **SQLite :** `.sqlite`, `.sqlite3`, `.db`
- **Archives :** `.zip`, `.tar`, `.tgz`, `.tar.gz`, `.tar.bz2`, `.tar.xz`

Les moteurs optionnels ajoutent les familles de documents et de médias riches comme PDF, Word, Excel, PowerPoint, OpenDocument, images/OCR, transcription audio/vidéo, EPUB, LaTeX et les autres formats pris en charge par les versions installées des moteurs.

Voir [docs/FORMAT_SUPPORT.md](docs/FORMAT_SUPPORT.md) pour les détails.

## RAG et GraphRAG

BrainForgeMD est conçu pour se placer **avant** la base vectorielle, le moteur de recherche, la base de graphe ou le framework d’IA.

Un flux d’ingestion typique :

1. lire `manifest.jsonl` pour la provenance et les mises à jour au niveau source;
2. indexer ou créer les embeddings de `chunks.jsonl` pour la recherche;
3. charger `nodes.jsonl` et `edges.jsonl` lorsqu’un graphe est utile;
4. conserver `documents/**/*.md` comme corpus normalisé et lisible.

Plus de détails dans [docs/RAG_OUTPUTS.md](docs/RAG_OUTPUTS.md).

## Modèle de sécurité

Je considère chaque fichier d’entrée comme potentiellement malformé ou hostile.

BrainForgeMD n’exécute volontairement ni code source, ni commandes shell, ni cellules de notebook, ni macros, ni scripts intégrés. Les bases SQLite sont ouvertes en lecture seule. L’extraction des archives est limitée et protégée contre la sortie du répertoire prévu. La taille des sources, la profondeur des archives, le nombre de fichiers et la taille décompressée sont limités.

Les parseurs optionnels ont leurs propres dépendances et leur propre surface de sécurité. Un corpus réellement hostile devrait donc malgré tout être traité dans un environnement isolé.

Voir [SECURITY.md](SECURITY.md).

## Philosophie du projet

1. Conserver la provenance avant d’optimiser le texte.
2. Garder la conversion déterministe lorsque c’est possible.
3. Ne jamais inventer silencieusement du contenu manquant.
4. Préférer une extraction partielle clairement identifiée à un échec opaque.
5. Garder l’inférence sémantique hors de la couche de conversion.
6. Produire des sorties utiles autant aux humains qu’aux machines.
7. Garder le projet assez compréhensible pour que d’autres puissent l’étendre de façon sécuritaire.

## Contribuer

Les contributions sont les bienvenues. Je préfère les changements ciblés, des tests pour les nouveaux comportements, une documentation claire et des contrats de sortie rétrocompatibles lorsque c’est possible.

Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

BrainForgeMD est publié sous **licence MIT**.

Copyright (c) 2026 **Vat-faire**.

Voir [LICENSE](LICENSE).
