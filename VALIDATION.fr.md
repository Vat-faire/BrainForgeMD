# Preuves de validation

*Read this in [English / en anglais](VALIDATION.md).*

BrainForgeMD est testé avec des données synthétiques et reproductibles. Je n’utilise pas de documents privés ni de corpus personnels comme fixtures publiques de test.

Ce document sépare clairement les **capacités réellement exercées de bout en bout** des capacités simplement annoncées par un backend optionnel installé. Voir une extension dans une liste de formats ne veut pas dire que toutes les variantes possibles de ce format ont déjà été prouvées.

## Validation effectuée le 4 septembre 2026

### Pipeline principal multiplateforme

Le workflow de validation profonde exécute le même corpus de bout en bout sur :

- Ubuntu, Windows et macOS;
- Python 3.11, 3.12 et 3.13.

Le corpus synthétique contient du texte simple et Unicode, du Markdown avec liens locaux, du code source, JSON/JSONL, YAML, CSV, HTML, des notebooks Jupyter, du courriel EML, des sous-titres SRT, SQLite et le contenu imbriqué d’une archive ZIP.

Les tests ne vérifient pas seulement le code de sortie. Ils vérifient notamment que :

- la conversion se termine sans échec ni format non pris en charge dans ce corpus;
- `INDEX.md`, `REPORT.md`, `manifest.jsonl`, `chunks.jsonl`, `nodes.jsonl`, `edges.jsonl`, `errors.jsonl` et l’état incrémental sont produits;
- les identifiants de documents et de chunks, les chemins sources, la provenance SHA-256, les parseurs et le front matter sont présents;
- les chunks RAG et les nœuds/arêtes structurels pour GraphRAG sont produits;
- un deuxième passage sans changement ne reconvertit rien et conserve manifest, chunks et graphe identiques octet pour octet;
- un dossier de sortie placé dans l’arborescence source n’est pas réingéré par erreur.

### Installation propre du package

Une deuxième matrice 3 × 3 construit le wheel BrainForgeMD, crée un environnement virtuel vierge, installe ce wheel sans dépendre du checkout du code source, puis exécute la CLI installée sur un fichier synthétique.

Cette preuve est exécutée sur Ubuntu, Windows et macOS avec Python 3.11, 3.12 et 3.13.

Le test vérifie la version installée, la conversion en ligne de commande, le Markdown généré, les métadonnées du manifest, l’identité du parseur et l’état incrémental.

### Documents riches, OCR, audio et vidéo

Un job complet installe BrainForgeMD avec ses backends optionnels ainsi que les outils natifs de média/OCR nécessaires à l’environnement de test. Il génère ensuite de vrais conteneurs de fichiers synthétiques et les envoie dans le pipeline normal.

Les formats suivants ont été exercés de bout en bout :

| Format | Fixture synthétique | Ce que le test prouve |
|---|---|---|
| PDF | PDF avec texte généré par ReportLab | Le backend documentaire le convertit et conserve du texte utile |
| DOCX | Document Word généré avec titre, paragraphe et tableau | La conversion du document Office réussit |
| PPTX | Présentation générée avec titre et texte | La conversion de présentation réussit |
| XLSX | Classeur généré avec cellules structurées | La conversion de feuille de calcul réussit |
| PNG | Image générée contenant du texte | Le chemin image/OCR produit une sortie Markdown |
| EPUB | Conteneur EPUB valide généré avec chapitre XHTML | La conversion EPUB réussit |
| Parquet | Table Arrow générée | Le convertisseur Parquet natif réussit |
| WAV | Parole synthétisée localement avec `espeak-ng` | L’entrée audio est acceptée et convertie par la pile riche installée |
| MP4 | Vidéo générée avec FFmpeg et audio vocal synthétique | L’entrée vidéo/média est acceptée et convertie par la pile riche installée |

Le test des formats riches effectue lui aussi un deuxième passage sans modification et vérifie la stabilité octet pour octet du manifest, des chunks, des nœuds et des arêtes.

Au moment de cette validation, `brainforgemd doctor` confirmait que Docling, MarkItDown, la prise en charge Outlook MSG, Parquet, FFmpeg et les outils OCR étaient disponibles dans l’environnement de test riche.

## Tests d’archives hostiles

La suite tente des traversées de répertoire dans des archives ZIP et TAR avec notamment :

- `../escape.txt`;
- `..\\escape.txt` au format Windows;
- des chemins absolus;
- des chemins Windows qualifiés par un lecteur.

Elle teste également les limites de nombre de fichiers et de taille décompressée. Les tests exigent le rejet de ces entrées et vérifient qu’aucun fichier d’évasion n’est créé hors du dossier d’extraction.

## Ce qui n’est pas encore prouvé

La validation actuelle ne prétend **pas** couvrir exhaustivement tous les formats ni toutes les variantes rencontrées dans le monde réel. En particulier :

- les anciens formats Office binaires comme `.doc`, `.ppt` et `.xls` sont annoncés par les backends optionnels, mais n’ont pas encore de fixtures générées dédiées dans cette suite;
- les formats OpenDocument (`.odt`, `.ods`, `.odp`) n’ont pas encore de fixtures dédiées;
- la prise en charge Outlook `.msg` est installée et détectée, mais aucun conteneur MSG synthétique valide n’est encore généré et validé ici;
- chaque codec d’image, codec audio, conteneur vidéo ou extension annoncée par les backends n’est pas testé individuellement;
- la précision OCR, la qualité de transcription, la reconstruction des tableaux et la fidélité de mise en page dépendent de la qualité de la source et du backend; une conversion réussie ne garantit pas une reconstruction sémantique parfaite;
- les documents riches chiffrés, protégés par mot de passe, corrompus, exceptionnellement gros ou adversariaux demandent un corpus de test plus large;
- les performances sur de très gros corpus ne sont pas encore mesurées ici.

Je préfère garder ces limites explicites plutôt que transformer une liste de capacités de backend en promesses non prouvées.

## Reproduire les preuves

Les tests se trouvent dans [`tests/integration/`](tests/integration/) et le workflow GitHub Actions dans [`.github/workflows/deep-validation.yml`](.github/workflows/deep-validation.yml).

Les fichiers principaux sont :

- `tests/integration/test_core_deep.py` — tests de bout en bout du noyau, incrémental, provenance, graphe et archives hostiles;
- `tests/integration/smoke_wheel.py` — installation propre du wheel et smoke test de la CLI installée;
- `tests/integration/test_rich_formats.py` — validation des PDF/Office/image/EPUB/Parquet/audio/vidéo générés.

Une future release ne devrait jamais affaiblir ces tests simplement pour obtenir une coche verte. Si une capacité cesse d’être reproductible, il faut corriger l’implémentation ou corriger l’affirmation publique.
