# Security Policy / Politique de sécurité

[English](#english) · [Français](#français)

---

# English

## Supported versions

I apply security fixes to the latest released minor version of BrainForgeMD.

## Input threat model

I designed BrainForgeMD with the assumption that source files may be malformed, unexpected, or hostile.

The core converters are built to:

- never execute notebook cells, macros, shell commands, source code, or embedded scripts;
- open SQLite databases in read-only mode;
- reject archive members that attempt to escape the extraction root;
- enforce archive nesting, file-count, and expanded-size limits;
- cap source file size before conversion;
- sanitize output filenames;
- keep generated content under the selected output root;
- isolate conversion failures instead of crashing an entire batch whenever possible.

Optional conversion backends have their own parsers, models, native libraries, and dependency chains. Those components must be kept updated. Truly hostile or unknown files should be processed inside a sandbox, container, disposable virtual machine, or another isolated environment.

## Secrets and private data

The generated corpus can contain the complete textual content and metadata of the original files.

Treat BrainForgeMD output with the same confidentiality as the source material. BrainForgeMD itself does not intentionally upload source content or generated corpora.

Before sharing generated Markdown, manifests, chunks, reports, or graph files publicly, review them for private information, credentials, API keys, personal data, proprietary content, and sensitive metadata.

## Reporting a vulnerability

Please do not publish exploitable security details in a public issue.

When possible, open a **private security advisory** on the GitHub repository. Include:

- the affected version or commit;
- a minimal reproduction;
- the expected and actual behavior;
- the security impact;
- a suggested mitigation, if known.

I prefer responsible disclosure that gives enough information to reproduce and correct the issue without unnecessarily exposing users before a fix is available.

---

# Français

## Versions prises en charge

J’applique les correctifs de sécurité à la dernière version mineure publiée de BrainForgeMD.

## Modèle de menace des fichiers d’entrée

J’ai conçu BrainForgeMD en partant du principe qu’un fichier source peut être malformé, inattendu ou hostile.

Les convertisseurs du noyau sont conçus pour :

- ne jamais exécuter les cellules de notebook, macros, commandes shell, code source ou scripts intégrés;
- ouvrir les bases SQLite en lecture seule;
- refuser les éléments d’archive qui tentent de sortir du dossier d’extraction;
- limiter la profondeur des archives, le nombre de fichiers et la taille totale décompressée;
- limiter la taille des fichiers sources avant conversion;
- nettoyer les noms de fichiers de sortie;
- conserver le contenu généré sous le dossier de sortie choisi;
- isoler les erreurs de conversion plutôt que faire échouer tout un lot lorsque c’est possible.

Les moteurs de conversion optionnels possèdent leurs propres parseurs, modèles, bibliothèques natives et chaînes de dépendances. Ils doivent être maintenus à jour. Les fichiers réellement hostiles ou inconnus devraient être traités dans un bac à sable, un conteneur, une machine virtuelle jetable ou un autre environnement isolé.

## Secrets et données privées

Le corpus généré peut contenir l’intégralité du contenu textuel et des métadonnées des fichiers d’origine.

Il faut donc traiter les sorties de BrainForgeMD avec le même niveau de confidentialité que les sources. BrainForgeMD lui-même ne téléverse pas volontairement les fichiers sources ni les corpus générés.

Avant de publier du Markdown généré, des manifestes, des chunks, des rapports ou des fichiers de graphe, il faut les vérifier pour repérer les renseignements privés, identifiants, clés API, données personnelles, contenu propriétaire et métadonnées sensibles.

## Signaler une vulnérabilité

Merci de ne pas publier les détails exploitables d’une vulnérabilité dans une issue publique.

Lorsque c’est possible, ouvrez un **private security advisory** dans le dépôt GitHub. Incluez :

- la version ou le commit touché;
- une reproduction minimale;
- le comportement attendu et le comportement observé;
- l’impact de sécurité;
- une mitigation proposée, si elle est connue.

Je privilégie une divulgation responsable qui donne assez d’information pour reproduire et corriger le problème sans exposer inutilement les utilisateurs avant qu’un correctif soit disponible.
