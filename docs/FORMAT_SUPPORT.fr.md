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
pip install "brainforgemd[docling] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Selon la version de Docling installée et l’environnement, cela peut étendre le support vers les PDF, Word, PowerPoint, Excel, OpenDocument, images/OCR, HTML/Markdown, certains dialectes XML, des parcours de transcription audio/vidéo, VTT, LaTeX, courriel, EPUB et les autres formats pris en charge par cette version de Docling.

## Fallback optionnel MarkItDown

Installer MarkItDown comme solution de repli supplémentaire :

```bash
pip install "brainforgemd[markitdown] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Ses capacités dépendent de la version installée et de ses dépendances optionnelles. Il peut fournir des parcours supplémentaires pour des documents Office courants, PDF, images/OCR, audio, HTML, texte structuré, ZIP, EPUB et formats similaires.

## Pile optionnelle complète

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Comme les capacités des moteurs optionnels évoluent indépendamment de BrainForgeMD, le projet ne prétend pas que toutes leurs versions supportent exactement les mêmes formats.

La référence pratique sur une machine cible est :

```bash
brainforgemd formats
brainforgemd doctor
```

## Niveau actuel de validation

Le noyau déterministe est couvert par la suite de tests automatisés et la matrice CI multiplateforme du projet.

Les parcours optionnels PDF, Office, OCR, image, audio et vidéo sont intégrés, mais le projet en préversion **n’a pas encore été benchmarké ou validé de façon exhaustive sur un vaste corpus réel**. Le fait qu’un moteur optionnel installé expose un format ne garantit donc pas une qualité d’extraction identique pour tous les fichiers.

## Fichiers qui ne deviennent pas utilement du Markdown

Tous les formats binaires ou propres à une application ne possèdent pas forcément une représentation textuelle utile. BrainForgeMD n’en fabrique pas simplement pour prétendre les prendre en charge.

Lorsqu’aucun convertisseur ne peut produire un contenu utile, la source est signalée plutôt qu’ignorée silencieusement. L’enregistrement d’erreur conserve assez d’information pour identifier le fichier et ajouter plus tard un convertisseur spécialisé.

**Un format déclaré non supporté vaut mieux qu’un contenu inventé.**
