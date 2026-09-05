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
| PNG | Image générée contenant du texte | **Caduc** : l’audit indépendant n’a pas pu le reproduire. L’OCR PNG a renvoyé un Markdown vide; voir plus bas. |
| EPUB | Conteneur EPUB valide généré avec chapitre XHTML | La conversion EPUB réussit |
| Parquet | Table Arrow générée | Le convertisseur Parquet natif réussit |
| WAV | Parole synthétisée localement avec `espeak-ng` | **Caduc** : valable uniquement dans un job CI doté d’outils natifs supplémentaires. `brainforgemd[all]` seul ne transcrit pas l’audio; l’extra `[asr]` est requis. |
| MP4 | Vidéo générée avec FFmpeg et audio vocal synthétique | **Caduc** : identique au WAV — la piste audio exige l’extra `[asr]`. |

La suite des formats riches sépare les contrôles document/OCR des outils média :
l’absence d’un synthétiseur vocal ne peut donc plus masquer les assertions PDF, Office,
EPUB, Parquet et image. Elle effectue aussi un deuxième passage documentaire sans
modification et vérifie la stabilité octet pour octet du manifest, des chunks, des nœuds
et des arêtes. Le média est vérifié séparément : un backend ASR fonctionnel doit préserver
la parole synthétisée, tandis que `[all]` sans `[asr]` doit signaler explicitement le
backend de transcription manquant.

Au moment de cette validation, `brainforgemd doctor` confirmait que Docling, MarkItDown, la prise en charge Outlook MSG, Parquet, FFmpeg et les outils OCR étaient disponibles dans l’environnement de test riche.

## Tests d’archives hostiles

La suite tente des traversées de répertoire dans des archives ZIP et TAR avec notamment :

- `../escape.txt`;
- `..\\escape.txt` au format Windows;
- des chemins absolus;
- des chemins Windows qualifiés par un lecteur.

Elle teste également les limites de nombre de fichiers et de taille décompressée. Les tests exigent le rejet de ces entrées et vérifient qu’aucun fichier d’évasion n’est créé hors du dossier d’extraction.

## Audit indépendant, 4 septembre 2026

Un audit indépendant a re-testé chaque affirmation de cette page contre des fixtures
générées plutôt que contre la suite existante. Sa méthode, ses constats et ses mesures
sont dans [INDEPENDENT_AUDIT_REPORT.md](INDEPENDENT_AUDIT_REPORT.md). Les résultats
ci-dessous remplacent le résumé antérieur lorsque les deux divergent.

### Formats prouvés de bout en bout, contenu vérifié

Chacun a été généré localement, converti par le pipeline ordinaire, puis contrôlé pour
une chaîne témoin devant survivre jusqu’au Markdown. « Converti sans lever d’exception »
n’a pas été accepté comme preuve.

PDF (multipage, Unicode, tableaux, image intégrée, numérisé/OCR, 300 pages), DOCX
(titres, listes, tableau, image, en-tête/pied de page, Unicode), XLSX (plusieurs
feuilles, formules, cellules vides, grille 500x10), PPTX (plusieurs diapositives, notes
du présentateur, tableau, image), ODT, ODS, ODP, `.xls` binaire hérité (un vrai classeur
BIFF8, via MarkItDown), EPUB, Parquet, Outlook `.msg` (conteneur CFB construit à la
main), et OCR de JPEG, WEBP et BMP.

### Formats qui ne fonctionnent pas, et pourquoi

| Format | Statut |
|---|---|
| Audio (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`) | Échoue avec `brainforgemd[all]`. Exige `brainforgemd[asr]`, qui installe un modèle vocal. |
| Vidéo (`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`) | Idem : la piste audio est transcrite, donc le même extra est requis. |
| OCR PNG et TIFF | Le même texte rendu, correctement reconnu en JPEG, WEBP et BMP, a produit un Markdown vide en PNG et TIFF avec les versions de Docling et MarkItDown testées. Signalé en échec, jamais fabriqué. |
| `.doc` et `.ppt` hérités | Non vérifiés. Docling les route via LibreOffice, indisponible ici. Non revendiqués. |
| PDF chiffré | Signalé en échec, ce qui est le comportement attendu. |

L’affirmation antérieure selon laquelle WAV et MP4 étaient « exercés de bout en bout »
n’était vraie que dans un job CI installant des outils natifs supplémentaires; un simple
`pip install brainforgemd[all]` ne les a jamais pris en charge. OpenDocument était listé
mais son lecteur manquait jusqu’à l’ajout d’`odfdo` à l’extra `all`.

### Comportement face aux entrées hostiles et malformées

43 fixtures générées, plus une batterie d’entrées malformées, tronquées, trompeuses et
adverses, n’ont produit **aucun plantage du pipeline ni aucun contenu fabriqué**. DOCX,
PNG et PDF corrompus, PDF chiffré, image sans texte, image à faible contraste et PDF
quasi vide sont tous signalés dans `errors.jsonl` plutôt que convertis.

La traversée d’archive a été re-testée avec 21 formes de charge utile, dont les variantes
Windows à point ou espace final, les chemins avec lettre de lecteur et UNC, la traversée
encodée en pourcentage, ainsi que les membres tar de type lien symbolique et lien
physique. **Aucune charge utile n’est sortie du répertoire d’extraction.**

### Performances mesurées

Windows 11, i9-9900K, Python 3.11, corpus synthétique mixte :

| Fichiers | Sources | À froid | Débit | 2e exécution (inchangée) | Pic RSS | Taille du corpus |
|---|---|---|---|---|---|---|
| 100 | 0,16 Mo | 0,74 s | 136 fich./s | 0,76 s | 29 Mo | 0,6 Mo |
| 1 000 | 1,59 Mo | 5,8 s | 173 fich./s | 6,9 s | 41 Mo | 6,0 Mo |
| 10 000 | 15,9 Mo | 59 s | 170 fich./s | 72 s | 147 Mo | 59,9 Mo |

Trois propriétés mesurées à prendre en compte :

- **Une seconde exécution sans changement n’est pas plus rapide que la première.** Elle
  relit depuis le disque chaque document converti pour reconstruire les chunks et le
  graphe; le profilage attribue environ 70 % de son temps à cette relecture.
  L’incrémental apporte aujourd’hui la stabilité, pas la vitesse.
- **Le pic mémoire suit la taille totale du corpus, pas celle du plus gros fichier**, car
  le Markdown de chaque document et le texte de chaque chunk sont conservés pendant
  toute l’exécution. Un fichier texte de 100 Mo a culminé à 609 Mo de RSS. Prévoir
  environ 6x la taille des sources.
- La sortie pèse environ **2,4x** les sources pour de gros fichiers texte, et jusqu’à
  **3,8x** pour de nombreux petits fichiers, car `chunks.jsonl` duplique le texte à côté
  de `documents/`.

La conversion des formats riches est bien plus lente que le noyau : un PDF de 300 pages
a pris 311 s (environ 1 s/page) et chaque image OCR 3 à 7 s.

## Ce qui n’est toujours pas prouvé

- `.doc` et `.ppt` hérités, qui exigent LibreOffice dans le PATH;
- la qualité de la transcription audio et vidéo, seulement sa disponibilité avec `[asr]`;
- la précision de l’OCR en général, et l’OCR PNG/TIFF ne fonctionne pas du tout;
- chaque codec d’image, codec audio, conteneur vidéo et extension listée par un moteur;
- les documents riches protégés par mot de passe et adverses au-delà des cas ci-dessus;
- le comportement sur des corpus de plus de 10 000 fichiers ou des fichiers de plus de
  100 Mo;
- macOS et Linux pour les constats de l’audit précisément : l’audit s’est déroulé sous
  Windows 11, tandis que la matrice CI continue de couvrir les trois plateformes pour la
  suite du noyau.

Je préfère que ces limites restent explicites plutôt que de transformer des listes de
capacités de moteurs en promesses non tenues.

## Reproduire les preuves

Les tests se trouvent dans [`tests/integration/`](tests/integration/) et le workflow GitHub Actions dans [`.github/workflows/deep-validation.yml`](.github/workflows/deep-validation.yml).

Les fichiers principaux sont :

- `tests/integration/test_core_deep.py` — tests de bout en bout du noyau, incrémental, provenance, graphe et archives hostiles;
- `tests/integration/smoke_wheel.py` — installation propre du wheel et smoke test de la CLI installée;
- `tests/integration/test_rich_formats.py` — validation des PDF/Office/image/EPUB/Parquet/audio/vidéo générés.

Une future release ne devrait jamais affaiblir ces tests simplement pour obtenir une coche verte. Si une capacité cesse d’être reproductible, il faut corriger l’implémentation ou corriger l’affirmation publique.
