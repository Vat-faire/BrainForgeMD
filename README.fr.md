# BrainForgeMD

*Read this in [English / en anglais](README.md).*

**BrainForgeMD transforme des ensembles de fichiers variés en corpus Markdown traçable pour le RAG, le GraphRAG, la recherche, les bases de connaissances et le contexte durable pour l’IA.**

> ## Statut : préversion expérimentale
>
> Le dépôt déclare actuellement la version **0.1.0**, mais il n’existe **aucune release GitHub étiquetée et aucune publication PyPI pour le moment**.
>
> Le noyau a été vérifié dans GitHub Actions sous **Windows, macOS et Linux avec Python 3.11, 3.12 et 3.13**. La suite actuelle couvre le noyau déterministe, les archives, la génération du corpus, le graphe structurel et le comportement de la CLI. Les parcours PDF/Office/OCR/audio/vidéo reposent sur des moteurs optionnels externes et **ne sont pas encore validés de façon exhaustive sur un grand corpus réel**.
>
> Il faut donc considérer BrainForgeMD comme un logiciel expérimental utilisable, mais pas encore comme une plateforme d’ingestion de production finalisée.

## Auteur et maintenance

BrainForgeMD est un projet original de **Sd-tech-Sol**.

- Auteur et mainteneur : **Sd-tech-Sol** — https://github.com/Sd-tech-Sol
- Licence : [MIT](LICENSE) — © 2026 Sd-tech-Sol
- Direction du produit, priorités, approbations et décisions finales : **Sd-tech-Sol**
- Développement : **assisté par IA** — voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md)

Le projet ne prétend pas que chaque ligne a été tapée à la main. OpenAI ChatGPT a été utilisé comme outil de développement pour l’architecture, l’implémentation, les tests, les revues, la documentation et le travail dans le dépôt GitHub, sous la direction de Sd-tech-Sol. Aucun système d’IA n’est propriétaire ou mainteneur de BrainForgeMD, et son utilisation n’implique aucune affiliation avec OpenAI ni approbation de sa part.

## Pourquoi BrainForgeMD existe

Les dossiers de connaissances réels sont rarement propres. Ils contiennent des PDF, des documents Office, du code source, des courriels, des feuilles de calcul, des bases de données, des archives, des images, de l’audio, de la vidéo, des notes, des exports et plusieurs autres formats.

Pour les systèmes de contexte IA, convertir un fichier en texte brut ne règle qu’une partie du problème. Un corpus durable devrait aussi conserver :

- la provenance de l’information;
- la version exacte de la source;
- des identifiants stables de documents et de chunks;
- les métadonnées d’extraction;
- les limites des chunks;
- les relations explicites entre documents;
- assez de structure pour mettre à jour le corpus sans recréer toute son identité à chaque exécution.

BrainForgeMD vise à fournir cette couche d’ingestion et de normalisation avant une base vectorielle, un moteur de recherche, une base de graphe, un framework RAG ou un pipeline GraphRAG.

## Ce que BrainForgeMD produit

À partir d’une arborescence comme :

```text
knowledge/
├── contracts/report.pdf
├── meetings/briefing.mp3
├── photos/whiteboard.jpg
├── data/customers.csv
├── code/parser.py
└── mail/thread.eml
```

BrainForgeMD produit un corpus comme :

```text
context-out/
├── documents/                  # Markdown normalisé qui reflète l’arborescence source
├── INDEX.md                    # index lisible par un humain ou un agent
├── REPORT.md                   # résumé de la conversion
├── manifest.jsonl              # registre de provenance des sources
├── chunks.jsonl                # chunks RAG stables
├── nodes.jsonl                 # nœuds du graphe structurel
├── edges.jsonl                 # relations du graphe structurel
├── errors.jsonl                # erreurs de conversion isolées
└── .brainforgemd/state.json    # état de conversion incrémentale
```

Chaque document Markdown généré commence par un front matter compatible YAML contenant notamment le chemin relatif de la source, des identifiants stables, le SHA-256, le type MIME, la taille du fichier, le parseur utilisé et les métadonnées d’extraction.

## Principes de conception

BrainForgeMD repose sur quelques règles explicites :

1. **Conserver la provenance avant d’optimiser le texte.**
2. **Garder les formats déterministes réellement déterministes lorsque c’est possible.**
3. **Ne jamais inventer silencieusement du contenu manquant.**
4. **Préférer un fichier clairement déclaré non supporté à une extraction fabriquée.**
5. **Garder l’inférence sémantique hors de la couche de conversion.**
6. **Considérer les fichiers sources comme des entrées non fiables.**
7. **Produire des sorties utiles aux humains et aux machines.**
8. **Rendre les ingestions répétées stables et vérifiables.**

## Capacités principales

- Conversion récursive par lot avec chemins de sortie reflétant les sources.
- Identifiants stables de source, version et chunk.
- Provenance SHA-256.
- Front matter Markdown compatible YAML.
- `manifest.jsonl` comme registre des sources.
- `chunks.jsonl` pour l’ingestion RAG.
- `nodes.jsonl` et `edges.jsonl` pour un graphe structurel factuel.
- État incrémental de conversion.
- Extraction d’archives sécurisée et limitée.
- Inspection SQLite en lecture seule.
- Isolation des erreurs pour les fichiers brisés ou non supportés.
- Exclusion des dossiers courants de contrôle de version, build, cache et environnements.
- Liens symboliques ignorés par défaut.
- Verrouillage du répertoire de sortie : un seul écrivain à la fois.
- Publication transactionnelle et restauration des artefacts du corpus en cas d’échec.
- Registre de convertisseurs extensible.
- Moteurs optionnels Docling et MarkItDown pour les documents et médias riches.

## Installation

### Noyau directement depuis GitHub

Le noyau n’a aucune dépendance tierce obligatoire à l’exécution.

```bash
pip install "brainforgemd @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

### Pile optionnelle complète documents/médias

```bash
pip install "brainforgemd[all] @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

`[all]` couvre PDF, Office, OpenDocument, EPUB, images/OCR, Outlook `.msg` et Parquet.

**L’audio et la vidéo ne sont pas inclus dans `[all]`.** La transcription exige un modèle
de reconnaissance vocale de plusieurs gigaoctets, fourni par un extra distinct :

```bash
pip install "brainforgemd[all,asr] @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

Sans cet extra, chaque fichier `.wav`, `.mp3`, `.mp4` et assimilé est signalé en échec
plutôt que converti.

### Environnement de développement

```bash
git clone https://github.com/Sd-tech-Sol/BrainForgeMD.git
cd BrainForgeMD
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[all,dev]"
pytest
ruff check .
```

Les moteurs optionnels OCR et transcription peuvent demander leurs propres modèles ou bibliothèques natives.

Vérifiez la machine cible avec :

```bash
brainforgemd doctor
brainforgemd formats
```

## Démarrage rapide

Convertir un fichier :

```bash
brainforgemd convert report.pdf -o context-out
```

Une exécution mono-fichier peut créer ou rafraîchir un corpus qui ne contient que ce
fichier (ou cette archive). Pour empêcher le manifeste global, les chunks, le graphe et
l’état de devenir une vue partielle, BrainForgeMD refuse une exécution mono-fichier vers
un corpus existant contenant d’autres sources; relancez plutôt le dossier source parent.

Convertir récursivement tout un dossier :

```bash
brainforgemd convert ./knowledge -o ./context-out
```

Utiliser de plus petits chunks RAG :

```bash
brainforgemd convert ./knowledge -o ./context-out --chunk-chars 3500 --overlap-chars 400
```

Forcer une reconstruction complète :

```bash
brainforgemd convert ./knowledge -o ./context-out --no-incremental
```

## Contrat du corpus

### Front matter Markdown

Un document converti commence avec des champs semblables à :

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

Un objet JSON par source. C’est le registre de provenance au niveau source et un point d’entrée pratique pour les systèmes capables de faire des mises à jour documentaires.

### `chunks.jsonl`

Un objet JSON par chunk de recherche, incluant :

- `chunk_id`
- `source_id`
- `source_path`
- `ordinal`
- `section_path`
- `text`
- `char_count`
- `approx_tokens`
- `sha256`

Les identifiants de chunks restent stables tant que l’identité de la source, la section, l’ordre et le texte du chunk restent les mêmes.

### `nodes.jsonl` et `edges.jsonl`

Le graphe est volontairement structurel plutôt que spéculatif. Il représente des relations explicites comme :

- `contains`
- `next`
- `links_to`
- `references_url`

L’extraction d’entités sémantiques, les embeddings, la détection de communautés, les relations inférées et les résumés générés appartiennent aux systèmes en aval.

## Familles de formats prises en charge

Le noyau léger traite directement le texte, Markdown, plusieurs fichiers de code/configuration, JSON/JSONL, YAML, TOML, INI, CSV/TSV, XML, HTML, les notebooks Jupyter, les courriels EML, les sous-titres SRT/VTT, SQLite et plusieurs familles d’archives ZIP/TAR.

Les moteurs optionnels étendent la prise en charge vers les PDF, documents Office, OpenDocument, images/OCR, EPUB, LaTeX et les autres formats supportés par les versions installées des moteurs. La transcription audio/vidéo exige l’extra distinct `[asr]`.

`brainforgemd formats` marque tout convertisseur dont le moteur est absent de la machine courante.

Voir [docs/FORMAT_SUPPORT.fr.md](docs/FORMAT_SUPPORT.fr.md).

## Intégration RAG et GraphRAG

Un flux d’ingestion typique :

1. lire `manifest.jsonl` pour la provenance et les mises à jour au niveau source;
2. indexer ou créer les embeddings de `chunks.jsonl` pour la recherche;
3. charger `nodes.jsonl` et `edges.jsonl` lorsqu’un graphe est utile;
4. conserver `documents/**/*.md` comme corpus normalisé lisible.

Voir [docs/RAG_OUTPUTS.fr.md](docs/RAG_OUTPUTS.fr.md).

## Sécurité et confidentialité

BrainForgeMD considère chaque source comme potentiellement malformée ou hostile.

Le noyau n’exécute volontairement ni code source, ni commandes shell, ni macros, ni cellules de notebook, ni scripts intégrés. SQLite est ouvert en lecture seule. L’extraction d’archives est limitée et refuse les tentatives de traversée de chemin. Les parseurs optionnels ajoutent leurs propres dépendances et surfaces de sécurité.

Les corpus générés peuvent contenir l’ensemble du contenu textuel et des métadonnées présents dans les fichiers sources. Ils doivent être protégés avec le même soin que les originaux.

Voir [SECURITY.fr.md](SECURITY.fr.md) et [PRIVACY.fr.md](PRIVACY.fr.md).

## Limites connues de la version actuelle

| Domaine | Limite actuelle |
|---|---|
| Statut de publication | Aucune release GitHub étiquetée et aucun package PyPI pour le moment. |
| Validation des médias riches | Les moteurs optionnels PDF/Office/OCR sont vérifiés sur des fixtures générées (voir VALIDATION.fr.md), mais pas encore exhaustivement benchmarkés sur un vaste corpus réel. |
| Graphe sémantique | BrainForgeMD produit uniquement des relations structurelles; il ne fait pas d’inférence d’entités ni de génération de relations sémantiques. |
| Comptage de jetons | `approx_tokens` est une estimation heuristique, pas le résultat d’un tokenizer propre à un modèle. |
| Vitesse de l’incrémental | L’incrémental apporte la stabilité et l’auditabilité, pas la vitesse. Une seconde exécution sans changement relit chaque document converti pour reconstruire les chunks et le graphe : elle n’est pas plus rapide que la première. |
| Mémoire | Le pic mémoire suit la taille totale du corpus, pas celle du plus gros fichier. Prévoir environ 6x la taille des sources. |
| Taille de sortie | Un corpus pèse environ 2,4x à 3,8x ses sources, car `chunks.jsonl` duplique le texte à côté de `documents/`. |
| Concurrence | Un seul écrivain par répertoire de sortie. Une seconde exécution simultanée est refusée plutôt que d’altérer la première. |
| Audio et vidéo | Non couverts par `[all]`; ils exigent l’extra `[asr]`. |
| OCR PNG et TIFF | Ne fonctionne pas avec les moteurs testés, alors que JPEG, WEBP et BMP fonctionnent. |
| OCR/transcription | La disponibilité et la qualité dépendent des moteurs optionnels, modèles, bibliothèques natives, du matériel et des sources. |
| Binaires non supportés | BrainForgeMD les signale au lieu de fabriquer du texte. |
| Sécurité | Les fichiers hostiles devraient malgré tout être traités dans un environnement isolé, particulièrement avec les parseurs optionnels. |

Ces limites sont publiées volontairement plutôt que cachées derrière des affirmations de complétude.

## Documentation publique

- [Vision du projet](PROJECT_VISION.fr.md)
- [Transparence sur l’assistance IA](AI_ASSISTANCE.md)
- [Architecture](docs/ARCHITECTURE.fr.md)
- [Formats pris en charge](docs/FORMAT_SUPPORT.fr.md)
- [Sorties RAG / GraphRAG](docs/RAG_OUTPUTS.fr.md)
- [Politique de sécurité](SECURITY.fr.md)
- [Confidentialité](PRIVACY.fr.md)
- [Contribuer](CONTRIBUTING.fr.md)
- [Journal des changements](CHANGELOG.fr.md)

L’anglais est la langue principale de la documentation publique. Des traductions françaises sont fournies à côté de la documentation anglaise.

## Contribuer

Les contributions sont les bienvenues. Les changements devraient rester ciblés, inclure des tests lorsqu’ils modifient le comportement et documenter les changements de formats ou de contrat de sortie.

Voir [CONTRIBUTING.fr.md](CONTRIBUTING.fr.md).

## Développement assisté par IA

BrainForgeMD est un projet original de **Sd-tech-Sol**. L’idée, la direction du produit, les exigences, les priorités, les approbations et les décisions finales sont attribuées à Sd-tech-Sol.

Le développement a été **assisté par IA**. OpenAI ChatGPT a servi pour l’architecture, l’implémentation, les tests, les audits, la documentation et le travail dans le dépôt GitHub, sous la direction de Sd-tech-Sol.

Cela ne signifie pas que chaque ligne a été tapée manuellement. Cela ne signifie pas non plus qu’un système d’IA possède ou maintient le projet. La responsabilité finale du projet et sa maintenance reviennent à **Sd-tech-Sol**.

Voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md) pour la déclaration complète.

## Licence

MIT. Voir [LICENSE](LICENSE).

Copyright (c) 2026 **Sd-tech-Sol**.
