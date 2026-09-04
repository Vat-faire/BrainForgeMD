# Sorties RAG et GraphRAG

*Read this in [English / en anglais](RAG_OUTPUTS.md).*

BrainForgeMD est conçu pour se placer avant un système de recherche ou de graphe. Il normalise les sources et prépare la provenance, les chunks et la structure explicite; il ne cherche pas à remplacer la pile RAG ou GraphRAG en aval.

## Ordre d’ingestion recommandé

1. Lire `manifest.jsonl` pour les métadonnées, la provenance et les mises à jour au niveau source.
2. Indexer ou créer les embeddings de `chunks.jsonl` pour la recherche.
3. Charger `nodes.jsonl` et `edges.jsonl` lorsque le système en aval accepte un graphe.
4. Conserver `documents/**/*.md` comme corpus normalisé lisible par un humain.

## Découpage en chunks

Le chunker privilégie les limites de titres et de paragraphes. Les sections trop longues sont divisées en fenêtres de caractères avec chevauchement.

Les limites sont exprimées en caractères plutôt qu’avec un tokenizer propre à un modèle afin de garder la sortie déterministe et indépendante du modèle.

`approx_tokens` est une estimation conservatrice basée sur les caractères, pas un comptage exact par tokenizer. Un système en aval lié à un modèle d’embedding ou de génération précis devrait refaire le comptage avant d’imposer des limites strictes de jetons.

## Identité stable des chunks

Les identifiants de chunks sont dérivés de l’identité de la source, de la section, de la position ordinale et du texte du chunk. L’objectif est de permettre des ingestions répétables et des mises à jour en aval sans recréer une nouvelle identité pour du contenu inchangé à chaque exécution.

## Schéma du graphe

Types de nœuds actuels :

- `document`
- `chunk`
- `url`

Types de relations actuels :

- `contains` : document → chunk
- `next` : chunk → chunk
- `links_to` : document/chunk → document lorsqu’un lien local peut être résolu
- `references_url` : document/chunk → URL

## Ce que le graphe ne prétend volontairement pas faire

Le graphe contient uniquement de la structure explicite.

BrainForgeMD ne fait pas actuellement :

- d’extraction sémantique d’entités;
- de génération de relations inférées;
- d’embeddings;
- de détection de communautés;
- de résumés sémantiques;
- de classement basé sur le graphe.

Ces opérations appartiennent à la couche GraphRAG en aval, où le modèle, le domaine et les exigences de qualité sont connus.

Cette frontière est volontaire : la couche de conversion doit préserver les preuves plutôt que fabriquer des faits sémantiques.

## Provenance

Le front matter Markdown et `manifest.jsonl` conservent les chemins relatifs, les empreintes, les identifiants stables, les informations du parseur et d’autres métadonnées d’extraction afin que les résultats de recherche en aval puissent être retracés jusqu’aux sources.

## Niveau actuel de validation

Le packaging des sorties, le comportement du graphe structurel, le chunking et le pipeline du noyau sont couverts par des tests automatisés. La qualité de l’intégration avec une base vectorielle, une base de graphe, un modèle d’embeddings ou un framework GraphRAG précis ne fait pas partie de la matrice de tests actuelle et doit être validée par l’application en aval.
