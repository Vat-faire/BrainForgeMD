# Contributing / Contribuer

[English](#english) · [Français](#français)

---

# English

Contributions are welcome.

I want BrainForgeMD to stay useful, predictable, secure, and easy to extend. Focused pull requests are much easier to review and maintain than large unrelated changes.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

Before opening a pull request, please make sure the test suite and Ruff both pass.

## Adding a converter

When adding a new converter, I expect it to follow the same rules as the existing pipeline:

1. Implement `Converter` from `brainforgemd.converters.base`.
2. Give the converter a stable `name` and explicit `extensions`.
3. Never execute input content.
4. Return normalized Markdown plus structured metadata.
5. Add unit tests using synthetic fixtures whenever possible.
6. Register the converter in `build_default_registry()`.
7. Update format documentation if support changes.

A converter should fail clearly and specifically when it cannot parse a source. The pipeline is responsible for deciding whether the batch continues.

## Output compatibility

The generated corpus is part of BrainForgeMD's public contract. Changes to front matter, JSONL schemas, IDs, graph relations, or output paths should remain backwards-compatible whenever practical. Breaking changes should be intentional, documented, and versioned.

## Pull requests

Please keep changes focused, explain the reason for the change, add tests for new behavior, and document any new format or output-contract behavior.

Security-related issues should not be disclosed in a public issue. See [SECURITY.md](SECURITY.md).

---

# Français

Les contributions sont les bienvenues.

Je veux que BrainForgeMD reste utile, prévisible, sécuritaire et facile à faire évoluer. Les pull requests ciblées sont beaucoup plus simples à réviser et à maintenir que les gros changements qui mélangent plusieurs sujets.

## Environnement de développement

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

Avant d’ouvrir une pull request, merci de vérifier que les tests et Ruff passent tous les deux.

## Ajouter un convertisseur

Pour ajouter un nouveau convertisseur, je veux qu’il respecte les mêmes règles que le pipeline actuel :

1. Implémenter `Converter` depuis `brainforgemd.converters.base`.
2. Donner au convertisseur un `name` stable et des `extensions` explicites.
3. Ne jamais exécuter le contenu d’entrée.
4. Retourner du Markdown normalisé avec des métadonnées structurées.
5. Ajouter des tests unitaires avec des fixtures synthétiques lorsque c’est possible.
6. Enregistrer le convertisseur dans `build_default_registry()`.
7. Mettre à jour la documentation des formats si le support change.

Un convertisseur doit échouer de façon claire et précise lorsqu’il ne peut pas analyser une source. C’est le pipeline qui décide ensuite si le traitement du lot continue.

## Compatibilité des sorties

Le corpus généré fait partie du contrat public de BrainForgeMD. Les changements au front matter, aux schémas JSONL, aux identifiants, aux relations du graphe ou aux chemins de sortie devraient rester rétrocompatibles lorsque c’est raisonnablement possible. Les changements incompatibles doivent être volontaires, documentés et versionnés.

## Pull requests

Merci de garder les changements ciblés, d’expliquer leur raison, d’ajouter des tests pour les nouveaux comportements et de documenter tout nouveau format ou changement au contrat de sortie.

Les problèmes de sécurité ne devraient pas être publiés dans une issue publique. Voir [SECURITY.md](SECURITY.md).
