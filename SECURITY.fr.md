# Politique de sécurité

*Read this in [English / en anglais](SECURITY.md).*

## Versions prises en charge

Les correctifs de sécurité sont appliqués à la dernière version mineure publiée de BrainForgeMD.

## Modèle de menace des fichiers d’entrée

BrainForgeMD part du principe qu’un fichier source peut être malformé, inattendu ou hostile.

Les convertisseurs du noyau sont conçus pour :

- ne jamais exécuter les cellules de notebook, macros, commandes shell, code source ou scripts intégrés;
- ouvrir les bases SQLite en lecture seule;
- refuser les éléments d’archive qui tentent de sortir du dossier d’extraction;
- limiter la profondeur des archives, le nombre de fichiers et la taille totale décompressée;
- limiter la taille des fichiers sources avant conversion;
- nettoyer les noms de fichiers de sortie;
- conserver le contenu généré sous le dossier de sortie choisi;
- isoler les erreurs de conversion lorsque c’est raisonnablement possible.

Les moteurs de conversion optionnels possèdent leurs propres parseurs, modèles, bibliothèques natives et chaînes de dépendances. Ils doivent être maintenus à jour. Les fichiers réellement hostiles ou inconnus devraient être traités dans un bac à sable, un conteneur, une machine virtuelle jetable ou un autre environnement isolé.

## Secrets et données privées

Le corpus généré peut contenir l’intégralité du contenu textuel et des métadonnées des fichiers d’origine.

Les sorties de BrainForgeMD doivent donc être traitées avec le même niveau de confidentialité que les sources. BrainForgeMD lui-même ne téléverse pas volontairement les fichiers sources ni les corpus générés.

Avant de publier du Markdown généré, des manifestes, des chunks, des rapports ou des fichiers de graphe, il faut les vérifier pour repérer les renseignements privés, identifiants, clés API, données personnelles, contenu propriétaire et métadonnées sensibles.

## Signaler une vulnérabilité

Merci de ne pas publier les détails exploitables d’une vulnérabilité dans une issue publique.

Lorsque c’est possible, ouvrez un private security advisory dans le dépôt GitHub. Incluez :

- la version ou le commit touché;
- une reproduction minimale;
- le comportement attendu et observé;
- l’impact de sécurité;
- une mitigation proposée, si elle est connue.

La divulgation responsable est privilégiée afin qu’un problème puisse être reproduit et corrigé sans exposer inutilement les utilisateurs avant qu’un correctif soit disponible.

## Développement assisté par IA et sécurité

L’assistance IA ne réduit pas le niveau d’exigence de sécurité du projet. Les changements assistés par IA doivent être vérifiables au moyen du code, des tests, de la CI et de la documentation, comme n’importe quelle autre contribution.

Voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md) pour la déclaration du projet.
