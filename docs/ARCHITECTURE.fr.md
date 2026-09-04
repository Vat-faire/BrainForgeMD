# Architecture

*Read this in [English / en anglais](ARCHITECTURE.md).*

BrainForgeMD sépare **la découverte**, **les limites de sécurité**, **l’extraction**, **la normalisation**, **la provenance**, **le découpage en chunks** et **la création du graphe** afin que chaque étape puisse être inspectée indépendamment.

```text
découverte des entrées
    ↓
limites de sécurité
    ↓
registre des convertisseurs ──→ convertisseur intégré
    │                          moteur Docling
    │                          fallback MarkItDown
    ↓
Markdown normalisé + métadonnées d’extraction
    ↓
front matter de provenance
    ↓
sortie .md reflétant l’arborescence source
    ↓
chunker ──→ chunks.jsonl
    ↓
graphe structurel ──→ nodes.jsonl / edges.jsonl
    ↓
manifest / index / rapport / état incrémental
```

## Identifiants stables

L’identité d’un document est dérivée de son chemin relatif à la source. Un identifiant de version distinct est dérivé du chemin et de l’empreinte du contenu. L’identité d’un chunk dépend de l’identité du document, du chemin de section, de sa position ordinale et du texte du chunk.

Cette séparation vise à garder les ingestions répétées idempotentes et à permettre aux systèmes en aval de mettre à jour seulement ce qui a changé sans considérer chaque exécution comme un corpus complètement nouveau.

## Ordre des convertisseurs

Le registre par défaut suit cet ordre :

1. convertisseurs intégrés précis pour les formats déterministes;
2. Docling pour les documents et médias riches pris en charge lorsqu’il est installé;
3. MarkItDown comme solution de repli optionnelle lorsqu’il est installé;
4. enregistrement du fichier comme non pris en charge lorsqu’aucun convertisseur ne l’accepte.

L’objectif est d’utiliser le parseur déterministe le plus simple capable de représenter correctement la source avant de passer à des parseurs généraux plus lourds.

## Graphe structurel par conception

Un convertisseur peut observer de façon fiable la structure explicite : contenance, ordre des chunks, liens locaux et URL. Il ne peut pas déduire de façon fiable les personnes, organisations, événements, communautés ou relations sémantiques sans modèle séparé ou couche d’extraction spécialisée.

BrainForgeMD produit donc un graphe structurel factuel et laisse l’enrichissement sémantique aux systèmes GraphRAG en aval. Un graphe factuel incomplet est préférable à un graphe plus riche qui invente silencieusement des relations.

## Limite du système

BrainForgeMD est une **couche d’ingestion et de normalisation**. Il n’a pas pour objectif de remplacer :

- une base vectorielle;
- un modèle d’embeddings;
- une base de graphe;
- l’extraction d’entités;
- la détection de communautés;
- un reranker;
- un framework d’orchestration LLM.

Il crée plutôt un corpus stable et traçable que ces systèmes peuvent consommer.

## Frontière de confiance

Les fichiers sources sont considérés comme non fiables. Le pipeline ne devrait pas exécuter le contenu source. La gestion des archives, l’accès aux bases de données, les chemins de sortie et l’intégration de parseurs optionnels sont des frontières sensibles à la sécurité qui doivent rester testables indépendamment.

Voir [../SECURITY.fr.md](../SECURITY.fr.md).

## Transparence du développement

L’architecture et l’implémentation ont été développées avec assistance IA sous la direction de Vat-faire. La déclaration correspondante se trouve dans [../AI_ASSISTANCE.md](../AI_ASSISTANCE.md). Les affirmations techniques de ce document sont destinées à être vérifiables dans le code et les tests, indépendamment de la méthode de développement utilisée.
