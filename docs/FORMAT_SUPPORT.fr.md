# Formats pris en charge

*Read this in [English / en anglais](FORMAT_SUPPORT.md).*

BrainForgeMD possède deux couches de prise en charge des formats : un noyau déterministe léger et des moteurs optionnels pour les documents et médias riches.

## Convertisseurs du noyau

Le noyau vise à rester petit et prévisible. Il traite directement les formats pour lesquels il est possible de produire un Markdown utile sans parseur externe lourd.

| Famille | Extensions / exemples | Comportement |
|---|---|---|
| Texte brut | txt, md, markdown, rst, log | Décodage et normalisation du texte |
| Code/configuration | py, js, ts, java, c/cpp, cs, go, rs, rb, php, swift, kt, sh, ps1, sql, fichiers de type Dockerfile et configurations courantes | Code dans des blocs Markdown avec indication de langage |
| Données structurées | json, jsonl, yaml/yml, toml, ini/cfg/conf, xml | Représentation structurée lisible |
| Tableaux | csv, tsv | Tableaux Markdown avec limites |
| Web | html, htm | Texte et structure visible sans exécuter les scripts |
| Notebooks | ipynb | Cellules Markdown, code et sorties textuelles; les cellules ne sont jamais exécutées |
| Courriel | eml | En-têtes, contenu du message et inventaire des pièces jointes |
| Sous-titres | srt, vtt | Transcription avec horodatage |
| SQLite | sqlite, sqlite3, db | Schéma en lecture seule et échantillons de lignes limités |
| Parquet | parquet | Contenu tabulaire structuré lorsque la dépendance optionnelle est disponible |
| Archives | zip, tar, tgz, tar.gz, tar.bz2, tar.xz | Extraction récursive sécurisée et limitée |

## Moteur optionnel Docling

Installer l’extra Docling :

```bash
pip install "brainforgemd[docling] @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

Selon la version de Docling installée et l’environnement, cela peut étendre le support vers les PDF, Word, PowerPoint, Excel, OpenDocument, images/OCR, HTML/Markdown, certains dialectes XML, VTT, LaTeX, courriel, EPUB et les autres formats pris en charge par cette version de Docling.

Deux capacités annoncées par Docling exigent des extras que `[docling]` seul n’installe pas :

- **OpenDocument** exige `odfdo`, inclus dans `brainforgemd[all]` et `brainforgemd[odf]`.
  Sans lui, `.odt`, `.ods` et `.odp` échouent.
- **La transcription audio et vidéo** exige un modèle de reconnaissance vocale, installé
  par `brainforgemd[asr]`. Il est délibérément exclu de `[all]` car il ajoute plusieurs
  gigaoctets. Sans lui, tout fichier audio ou vidéo est signalé en échec.

## Fallback optionnel MarkItDown

Installer MarkItDown comme solution de repli supplémentaire :

```bash
pip install "brainforgemd[markitdown] @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

Ses capacités dépendent de la version installée et de ses dépendances optionnelles. Il peut fournir des parcours supplémentaires pour des documents Office courants, PDF, images/OCR, audio, HTML, texte structuré, ZIP, EPUB et formats similaires.

## Pile optionnelle complète

```bash
pip install "brainforgemd[all] @ git+https://github.com/Sd-tech-Sol/BrainForgeMD.git"
```

Comme les capacités des moteurs optionnels évoluent indépendamment de BrainForgeMD, le projet ne prétend pas que toutes leurs versions supportent exactement les mêmes formats.

La référence pratique sur une machine cible est :

```bash
brainforgemd formats
brainforgemd doctor
```

`brainforgemd formats` préfixe un convertisseur d’un `!` lorsque son moteur n’est pas
installé sur la machine courante : une extension listée se distingue ainsi d’une
extension réellement utilisable.

## Niveau actuel de validation

Le noyau déterministe est couvert par la suite de tests automatisés et la matrice CI multiplateforme du projet.

Un audit indépendant a converti des fixtures générées pour PDF (multipage, Unicode,
tableaux, images, numérisé/OCR, 300 pages), DOCX, XLSX, PPTX, ODT, ODS, ODP, `.xls`
hérité, EPUB, Parquet, Outlook `.msg` et l’OCR JPEG/WEBP/BMP, en vérifiant que le
contenu attendu survivait jusqu’au Markdown. Voir [VALIDATION.fr.md](../VALIDATION.fr.md).

Lacunes connues des versions de moteurs testées :

- **L’OCR PNG et TIFF renvoie un Markdown vide**, alors que le même texte est
  correctement reconnu en JPEG, WEBP et BMP. Ces cas sont signalés en échec, jamais
  fabriqués.
- **Les formats hérités `.doc` et `.ppt`** passent par LibreOffice, qui doit être dans le
  PATH.
- L’audio et la vidéo exigent l’extra `[asr]` décrit plus haut.

Le fait qu’un moteur optionnel installé expose un format ne garantit pas une qualité
d’extraction identique pour tous les fichiers.

## Fichiers qui ne deviennent pas utilement du Markdown

Tous les formats binaires ou propres à une application ne possèdent pas forcément une représentation textuelle utile. BrainForgeMD n’en fabrique pas simplement pour prétendre les prendre en charge.

Lorsqu’aucun convertisseur ne peut produire un contenu utile, la source est signalée plutôt qu’ignorée silencieusement. L’enregistrement d’erreur conserve assez d’information pour identifier le fichier et ajouter plus tard un convertisseur spécialisé.

**Un format déclaré non supporté vaut mieux qu’un contenu inventé.**
