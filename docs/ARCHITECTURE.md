# Architecture / Architecture

[English](#english) · [Français](#français)

---

# English

I designed BrainForgeMD so the conversion layer stays understandable and auditable. Extraction, normalization, provenance, chunking, and graph packaging are separate concerns.

```text
input discovery
    ↓
security limits
    ↓
converter registry ──→ built-in converter
    │                 Docling backend
    │                 MarkItDown fallback
    ↓
normalized Markdown + extraction metadata
    ↓
provenance front matter
    ↓
mirrored .md output
    ↓
chunker ──→ chunks.jsonl
    ↓
structural graph ──→ nodes.jsonl / edges.jsonl
    ↓
manifest / index / report / incremental state
```

## Stable identities

Document identity is derived from the source-relative path. A separate version ID is derived from the path plus the content hash. Chunk identity is derived from the document identity, section path, ordinal position, and chunk text.

I use this separation so repeated ingestion can remain idempotent and downstream systems can upsert changed material without treating every run as a completely new corpus.

## Converter order

The default registry follows this order:

1. exact built-in converters for deterministic formats;
2. Docling for supported rich documents and media when installed;
3. MarkItDown as an optional fallback when installed;
4. an unsupported-file record when no converter accepts the source.

The goal is to use the simplest deterministic parser that can correctly represent the source before falling back to heavier general-purpose parsers.

## Why I keep the graph structural

A document converter can reliably observe explicit structure such as containment, chunk order, local links, and URLs. It cannot reliably infer people, organizations, events, communities, or semantic relationships without a separate model or domain-specific extraction layer.

For that reason, BrainForgeMD emits a factual structural graph and leaves semantic enrichment to the downstream GraphRAG system. I prefer an incomplete factual graph over a richer graph that silently invents relationships.

## Boundaries

BrainForgeMD is the **ingestion and normalization layer**. It is not intended to replace:

- a vector database;
- an embedding model;
- a graph database;
- an entity extraction pipeline;
- community detection;
- a reranker;
- an LLM orchestration framework.

Instead, it creates a stable, traceable corpus those systems can consume.

---

# Français

J’ai conçu BrainForgeMD pour que la couche de conversion reste compréhensible et vérifiable. L’extraction, la normalisation, la provenance, le découpage en chunks et la création du graphe sont séparés.

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

J’utilise cette séparation pour que les passages répétés restent idempotents et que les systèmes en aval puissent mettre à jour seulement ce qui a changé sans considérer chaque exécution comme un corpus complètement nouveau.

## Ordre des convertisseurs

Le registre par défaut suit cet ordre :

1. convertisseurs intégrés précis pour les formats déterministes;
2. Docling pour les documents et médias riches pris en charge lorsqu’il est installé;
3. MarkItDown comme solution de repli optionnelle lorsqu’il est installé;
4. enregistrement du fichier comme non pris en charge lorsqu’aucun convertisseur ne l’accepte.

L’objectif est d’utiliser le parseur déterministe le plus simple capable de représenter correctement la source avant de passer à des parseurs généraux plus lourds.

## Pourquoi je garde le graphe structurel

Un convertisseur de documents peut observer de façon fiable la structure explicite : contenance, ordre des chunks, liens locaux et URL. Il ne peut pas déduire de façon fiable les personnes, organisations, événements, communautés ou relations sémantiques sans modèle séparé ou couche d’extraction spécialisée.

C’est pourquoi BrainForgeMD produit un graphe structurel factuel et laisse l’enrichissement sémantique au système GraphRAG en aval. Je préfère un graphe factuel incomplet à un graphe plus riche qui invente silencieusement des relations.

## Limites de responsabilité

BrainForgeMD est la **couche d’ingestion et de normalisation**. Il n’a pas pour objectif de remplacer :

- une base vectorielle;
- un modèle d’embeddings;
- une base de graphe;
- un pipeline d’extraction d’entités;
- la détection de communautés;
- un reranker;
- un framework d’orchestration LLM.

Le rôle de BrainForgeMD est plutôt de créer un corpus stable et traçable que ces systèmes peuvent consommer.
