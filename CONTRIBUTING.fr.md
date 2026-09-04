# Contribuer à BrainForgeMD

*Read this in [English / en anglais](CONTRIBUTING.md).*

Les contributions sont les bienvenues.

BrainForgeMD est encore un projet en préversion. Merci de lire les limites actuelles dans [README.fr.md](README.fr.md) et [CHANGELOG.fr.md](CHANGELOG.fr.md) avant de considérer qu’un comportement manquant devrait déjà être stable.

Les issues et pull requests peuvent être rédigées en anglais ou en français.

## Environnement de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

Avant d’ouvrir une pull request, vérifiez que les tests et Ruff passent tous les deux.

## Ajouter un convertisseur

Un nouveau convertisseur devrait respecter les mêmes règles que le pipeline existant :

1. implémenter `Converter` depuis `brainforgemd.converters.base`;
2. utiliser un `name` stable et des `extensions` explicites;
3. ne jamais exécuter le contenu d’entrée;
4. retourner du Markdown normalisé avec des métadonnées structurées;
5. ajouter des tests avec des fixtures synthétiques lorsque c’est raisonnablement possible;
6. enregistrer le convertisseur dans `build_default_registry()`;
7. mettre à jour la documentation des formats lorsque le support change.

Les convertisseurs devraient échouer de façon claire et précise lorsqu’ils ne peuvent pas analyser une source. Le pipeline décide ensuite si le reste du lot continue.

## Données de test

Utilisez uniquement des fixtures synthétiques, générées ou autrement redistribuables.

Ne publiez pas :

- de documents personnels;
- d’identifiants ou de clés API;
- de données de clients;
- de courriels privés;
- de fichiers propriétaires sans droit de redistribution;
- de captures ou métadonnées contenant des renseignements privés.

## Compatibilité des sorties

Le corpus généré fait partie du contrat public de BrainForgeMD.

Les changements au front matter, aux schémas JSONL, aux identifiants stables, aux relations du graphe ou aux chemins de sortie devraient rester rétrocompatibles lorsque c’est raisonnablement possible. Les changements incompatibles doivent être volontaires, documentés et versionnés.

## Changements sensibles à la sécurité

Les changements touchant l’extraction d’archives, la gestion des chemins, l’accès SQLite, la découverte des fichiers, les chemins de sortie ou l’intégration de parseurs optionnels devraient inclure des tests de refus ou d’erreur lorsque c’est pertinent.

Les vulnérabilités de sécurité ne devraient pas être publiées dans une issue publique. Voir [SECURITY.fr.md](SECURITY.fr.md).

## Contributions assistées par IA

BrainForgeMD assume ouvertement un développement assisté par IA. Les contributeurs ne sont pas obligés d’éviter les outils d’IA, mais ils restent responsables de ce qu’ils soumettent.

Le code généré ou assisté par IA doit respecter les mêmes exigences que du code écrit manuellement : changements compréhensibles, tests appropriés, licence valide, aucune donnée privée et comportement vérifiable.

Voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

## Pull requests

Gardez les pull requests ciblées. Expliquez pourquoi le changement est nécessaire, ajoutez des tests pour les nouveaux comportements et documentez toute modification aux formats pris en charge ou au contrat de sortie.
