# Journal des changements

*Read this in [English / en anglais](CHANGELOG.md).*

Tous les changements importants de BrainForgeMD sont documentés ici.

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
- Documentation publique anglaise avec traductions françaises.
- Déclaration explicite du développement assisté par IA.

### Correctifs avant la première release publique

- Validation des chemins d’archives corrigée pour les alias de chemins courts Windows et la résolution `/var` → `/private/var` de macOS.
- Problèmes Ruff détectés par la première exécution CI corrigés.
- Actions GitHub mises à jour vers des versions compatibles Node 24.
- Documentation d’installation corrigée pour utiliser directement le dépôt GitHub tant qu’aucune publication dans un registre de packages n’existe.

### Statut actuel de publication

La version `0.1.0` est présente dans les métadonnées du package source, mais aucune release GitHub étiquetée et aucun package PyPI n’ont encore été publiés.
