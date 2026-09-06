# Vision du projet BrainForgeMD

*Read this in [English / en anglais](PROJECT_VISION.md).*

## Objectif

BrainForgeMD existe pour faciliter la transformation d’informations locales hétérogènes en contexte durable et vérifiable pour les systèmes d’IA et de recherche.

Le projet part d’un constat simple : un bon système RAG, GraphRAG, second cerveau ou de long contexte a besoin de plus que du texte extrait. Il lui faut de la provenance, des identifiants stables, des mises à jour répétables, de la structure et des erreurs clairement signalées.

## Direction du produit

La direction à long terme est de faire de BrainForgeMD une **couche d’ingestion** fiable entre les fichiers réels et les systèmes de connaissances en aval.

Le projet devrait pouvoir prendre un corpus mélangé et produire un ensemble normalisé qui soit :

- lisible en Markdown;
- traçable jusqu’aux sources originales;
- adapté à l’indexation pour la recherche;
- adapté à l’ingestion dans un graphe structurel;
- répétable d’une exécution à l’autre;
- explicite sur les fichiers non supportés ou en erreur;
- local-first par défaut;
- extensible sans transformer le noyau en collection ingérable de cas spéciaux.

## Ce que BrainForgeMD devrait devenir

La direction visée comprend notamment :

- une prise en charge plus large des formats par des convertisseurs déterministes et des moteurs spécialisés optionnels;
- davantage de tests sur des fixtures réalistes pour PDF, Office, OCR, image, audio et vidéo;
- des benchmarks reproductibles de qualité d’extraction;
- un versionnement documenté du schéma du corpus;
- des tests de compatibilité plus solides entre versions des moteurs optionnels;
- de meilleures interfaces de plugins pour les formats spécialisés;
- des artefacts de release faciles à installer et à vérifier;
- des exemples pour des piles RAG et GraphRAG courantes;
- une vérification multiplateforme continue.

## Ce que BrainForgeMD ne devrait pas devenir

BrainForgeMD ne devrait pas absorber silencieusement toutes les responsabilités d’une pile IA en aval.

La couche de conversion ne devrait pas devenir un moteur caché d’inférence sémantique. L’extraction d’entités, les embeddings, les relations sémantiques, la détection de communautés, les résumés propres à un modèle, le classement de recherche et l’orchestration applicative appartiennent aux couches en aval, sauf si une future fonction est explicitement optionnelle et clairement séparée de la conversion déterministe.

Le projet ne devrait pas non plus prétendre prendre en charge un format simplement parce qu’un parseur peut techniquement l’ouvrir. Le support doit signifier qu’un contenu utile peut être produit et que ses limites peuvent être expliquées.

## Principes de qualité

Le projet devrait privilégier :

1. un comportement vérifiable plutôt que des affirmations impressionnantes;
2. des limites explicites plutôt qu’une incertitude cachée;
3. une extraction déterministe plutôt qu’une inférence inutile;
4. la provenance des sources plutôt qu’un texte détaché de son origine;
5. des résultats partiels mais clairement signalés plutôt qu’une complétude fabriquée;
6. des tests et preuves reproductibles plutôt que la confiance dans la méthode d’implémentation;
7. un noyau petit et compréhensible plutôt que des dépendances lourdes par défaut.

## Direction sur la confidentialité

BrainForgeMD est destiné à des corpus pouvant contenir des renseignements privés, professionnels ou sensibles. La conception par défaut devrait donc rester local-first et ne pas exiger un service hébergé ou un compte pour la conversion de base.

Les dépendances optionnelles peuvent avoir leurs propres besoins de téléchargement de modèles ou d’exécution, mais BrainForgeMD lui-même ne devrait pas introduire de télémétrie cachée ni de téléversement silencieux des sources.

Voir [PRIVACY.fr.md](PRIVACY.fr.md).

## Modèle de développement

Le projet est dirigé et maintenu par **Sd-tech-Sol** et son développement a été assisté par IA.

L’idée, les priorités, les approbations, le périmètre et les décisions finales sont attribués à Sd-tech-Sol. OpenAI ChatGPT a été utilisé comme outil de développement pour l’architecture, l’implémentation, les tests, le débogage, les revues, la documentation et le travail dans le dépôt.

La méthode de développement ne remplace pas la vérification. Le projet devrait être jugé sur son code, ses tests, ses résultats CI, ses limites documentées et son comportement.

Voir [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

## Stade actuel

BrainForgeMD est actuellement un projet en préversion. Le noyau déterministe est testé sur toute la matrice CI, mais une validation large et réaliste des moteurs optionnels pour documents et médias riches reste à faire.

Aucune release GitHub étiquetée et aucun package PyPI n’ont encore été publiés.
