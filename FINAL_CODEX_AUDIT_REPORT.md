# Audit technique adversarial final — BrainForgeMD v0.1.0

**Verdict proposé : `READY_WITH_KNOWN_LIMITATIONS`**, uniquement pour le candidat
contenant les correctifs de `audit/codex-final-validation`. Le `main` audité seul n'est
pas prêt, et `engineering/incremental-fastpath` ne doit pas être fusionnée en l'état.

Cet audit a traité le README, `VALIDATION.md`, `INDEPENDENT_AUDIT_REPORT.md`, les tests
et les résultats CI comme des affirmations à reproduire. Les tests adversariaux ont été
écrits contre le comportement observé, exécutés en échec sur la version fautive, puis
réexécutés après correction.

## 1. Périmètre et état Git réel

| Élément | Valeur vérifiée |
|---|---|
| Date | 2026-09-04 |
| Dépôt | `Vat-faire/BrainForgeMD` |
| OS local | Windows 11, x86-64 |
| Python locaux | CPython 3.11.9 et 3.12 |
| `main` local et distant au départ | `6f7d51d727380a695a07222b3c680a9aa7d99215` |
| Branche d'audit | `audit/codex-final-validation` |
| Dernier commit de code audité/corrigé | `a9207b5` |
| Fast-path séparé | `engineering/incremental-fastpath`, `2512cd9fa4dc3a2d8e6551d388eb953e739e70df` |

Le `git status` initial était propre. `git fetch --all --prune` a été exécuté avant
l'analyse des branches. Aucun merge, tag ou release n'a été créé.

État GitHub observé au début de l'audit :

- le workflow CI de `main` au SHA ci-dessus était vert (run `33921666278`) ;
- les trois derniers runs de `engineering/incremental-fastpath` étaient rouges, dont
  `33922189436` au SHA `2512cd9` ;
- dans ce dernier run, les 105 tests passaient mais Ruff échouait sur trois imports mal
  triés. Une CI rouge n'était donc pas à elle seule la raison de rejeter cette branche :
  ses défauts d'intégrité reproductibles le sont.

## 2. Résumé des findings de ce dernier audit

| ID | Sévérité | État | Finding | Preuve / régression | Correction |
|---|---|---|---|---|---|
| CX-01 | HIGH | Corrigé | Le cache acceptait un Markdown généré modifié et republiait ses faux chunks sous la provenance du source inchangé. | `test_tampered_cached_document_is_reconverted` échouait sur `main`. | Hash du document généré dans state v2 et revalidation avant replay (`994abca`). |
| CX-02 | MEDIUM | Corrigé | Une entrée hostile/non-mapping dans `state.json` faisait crasher le pipeline par `AttributeError`. | `test_malformed_cache_entry_is_invalidated_instead_of_crashing`. | Validation bornée et typée du state (`994abca`). |
| CX-03 | HIGH | Corrigé | Une modification du source entre le hash initial et la conversion, avec taille et mtime conservés, produisait une attribution SHA/contenu fausse. | `test_source_change_between_hash_and_conversion_is_rejected`. | Second hash après lecture/conversion, échec isolé si mutation (`994abca`). |
| CX-04 | MEDIUM | Corrigé | Des chemins distincts sous Linux pouvaient viser le même output sous Windows/macOS : casse seule, NFC/NFD, espace ou point final. | Tests de collision de sources et d'archives. | Clé de portabilité normalisée, collision refusée avant publication (`994abca`). |
| CX-05 | HIGH | Corrigé | Convertir un seul fichier dans un corpus multi-source remplaçait manifest/chunks/graph/state par une vue partielle tout en laissant les autres documents sur disque. | `test_single_file_run_cannot_corrupt_a_multi_source_corpus`. | Refus explicite ; l'utilisateur doit relancer le répertoire source (`8d0bed9`). |
| CX-06 | HIGH | Corrigé | Les artefacts globaux étaient atomiques individuellement, mais pas comme génération : une panne entre manifest et chunks publiait un corpus mixte. | Injection d'une panne entre deux publications, comparaison octet par octet. | Staging, backups et rollback de toute la génération (`8d0bed9`). |
| CX-07 | MEDIUM | Corrigé | Le fallback texte ne testait que les premiers 64 KiB et lisait malgré tout tout le fichier ; un préfixe texte pouvait masquer une charge binaire. | `test_text_fallback_detects_binary_payload_after_the_first_64k`. | Scan borné en mémoire de tout le flux avec décodeur incrémental (`2549875`). |
| CX-08 | MEDIUM | Mitigé | La mémoire croît avec le corpus global, surtout lors de la sérialisation JSONL. | Benchmark 5/25/100 MB, RSS avant/après. | Écriture JSONL streamée (`28180cb`) ; l'architecture conserve encore documents et chunks en mémoire. |
| CX-09 | LOW | Corrigé | `doctor` et `formats` donnaient une impression de support média avec `[all]` alors que l'ASR était absent. | Capture CLI avec Docling présent et Whisper absent. | Diagnostic ASR séparé et avertissement explicite (`1973386`). |
| CX-10 | HIGH | Rejeté hors release | Le fast-path non fusionné accepte un document caché altéré, un `chunks.jsonl` altéré, une entrée state hostile et un `chunk_count` forgé. | Quatre tests adversariaux jetables, quatre échecs sur `2512cd9` patché par ses propres scripts. | Ne pas fusionner cette branche ; réimplémenter avec validation cryptographique de tous les artefacts dérivés. |
| CX-11 | MEDIUM | Ouvert/documenté | Sur le pipeline sûr, un second run inchangé n'est pas sensiblement plus rapide et peut être plus lent. | Benchmarks 100/1 000/10 000, comparés au `main` exact. | Pas de redesign risqué pour v0.1.0. |
| CX-12 | LOW | Ouvert | Le build émet les dépréciations setuptools pour `license={file=...}` et le classifier de licence. | `python -m build`. | Migrer ultérieurement vers une expression SPDX ; échéance annoncée par setuptools en 2027. |
| CX-13 | HIGH | Corrigé | Le premier rollback transactionnel ajouté pendant cet audit aurait pu supprimer ses backups si le rollback échouait lui-même. | Panne persistante simulée ; contrôle de la présence des fichiers de récupération. | Conservation du dossier de recovery et erreur indiquant son chemin (`72dbd30`, `a9207b5`). |
| CX-14 | MEDIUM | Corrigé | Le test riche unique sautait PDF/Office/EPUB/Parquet/OCR dès que `espeak` manquait ; certains formats n'avaient pas de marqueur propre. | Exécution locale sans `espeak` : documents et image s'exécutent désormais. | Trois tests indépendants et assertions de marqueurs par format (`a3c0d00`). |

**Comptage : 0 CRITICAL, 6 HIGH, 6 MEDIUM, 2 LOW.** Tous les findings HIGH affectant
le candidat de release sont corrigés et retestés. CX-10 concerne uniquement une branche
non fusionnée ; CX-08, CX-11 et CX-12 restent des limitations documentées.

## 3. Correctness, intégrité et reproductibilité

Les contrôles ont couvert ajouts, modifications, suppressions, cache, state hostile,
collision de noms, mutation pendant lecture, génération interrompue et déterminisme.

- Un replay incrémental n'est accepté que si le source, la configuration et le hash du
  Markdown dérivé correspondent au state. Modifier le cache force maintenant une
  reconversion.
- Le hash du source est revérifié après le convertisseur. Une mutation concurrente ne
  peut plus être publiée sous le digest initial.
- `manifest.jsonl`, `chunks.jsonl`, `nodes.jsonl`, `edges.jsonl`, `errors.jsonl`,
  `INDEX.md`, `REPORT.md`, `state.json` et les documents touchés sont publiés comme une
  génération transactionnelle. Une panne de remplacement restaure les octets initiaux.
- Si cette restauration échoue aussi, les backups ne sont pas effacés et l'exception
  indique leur emplacement de récupération.
- Les sorties d'un rebuild incrémental inchangé restent déterministes octet par octet.
- Le vérificateur indépendant `audit/check_corpus.py` n'a détecté aucune référence,
  identité, digest, chunk, node ou edge incohérent dans les corpus publiés par le
  harness de formats.

Limite assumée : la transaction est un protocole de remplacement avec rollback, pas
une transaction filesystem atomique multi-fichiers visible comme un seul instant par
des lecteurs concurrents. Le verrou empêche deux écrivains BrainForgeMD, mais un lecteur
externe sans coordination peut observer la courte phase de commit. Pour v0.1.0, les
consommateurs doivent lire après la fin réussie de la commande.

## 4. Sécurité et entrées hostiles

Les suites existantes et les nouvelles régressions ont exercé : traversal ZIP/TAR,
chemins absolus/UNC/drive, variantes Unicode/casse/point/espace, bombes par nombre et
taille expandée, archives imbriquées, membres TAR symlink/hardlink, liens Markdown
malformés, XML hostile, SQLite hostile, HTML script/style, binaires trompeurs, fichiers
malformés, limites de taille, writers concurrents et TOCTOU.

Résultats :

- aucune extraction hors du répertoire temporaire ; les liens TAR ne sont jamais
  matérialisés ; les limites de nombre et de taille sont appliquées récursivement ;
- XML est traité par un parseur qui n'expanse pas les entités externes ; aucun XXE ou
  entity expansion n'a été observé ;
- SQLite est ouvert en lecture seule, les noms de tables proviennent de
  `sqlite_master`, sont échappés, et les échantillons sont bornés. Bandit signale B608
  avec confiance moyenne sur la construction du nom de table ; revue manuelle : faux
  positif dans ce contexte, pas de suppression `nosec` ajoutée ;
- les cellules notebook ne sont jamais exécutées ; aucun document n'est importé comme
  code Python ni passé à un shell par le core ;
- HTML enlève les corps `script`/`style` dans le convertisseur déterministe ;
- `pip-audit` dans l'installation `[all]` propre, après mise à niveau de l'outil `pip`,
  ne trouve aucune vulnérabilité connue parmi les dépendances installées. Le paquet
  local `brainforgemd 0.1.0`, non publié sur PyPI, ne peut naturellement pas être
  interrogé dans la base par son nom.

Limites : les parseurs riches Docling/MarkItDown et leurs dépendances ont une surface
d'attaque importante. Aucun sandbox processus/OS n'isole ces backends ; v0.1.0 ne doit
pas être présentée comme une passerelle d'upload hostile multi-tenant.

## 5. Formats : contenu réellement préservé

Chaque statut « vérifié » signifie qu'un fixture réel ou généré contenait un marqueur
unique, qu'il est passé par `Pipeline.run`/la CLI normale, et que le marqueur a été lu
dans le Markdown final. Un simple code retour zéro n'a pas été accepté.

| Famille / format | Résultat indépendant |
|---|---|
| TXT, MD, RST, source et config | Marqueurs vérifiés |
| JSON, JSONL, YAML, TOML, INI, XML | Marqueurs vérifiés |
| CSV, TSV | Marqueurs vérifiés |
| HTML | Marqueur visible vérifié ; script/style exclus |
| IPYNB | Marqueurs markdown/code/sortie texte vérifiés ; aucune exécution |
| EML | Sujet/corps vérifiés |
| SQLite | Schéma et marqueur de ligne vérifiés en lecture seule |
| ZIP, TAR et archive imbriquée | Marqueurs vérifiés ; liens/traversal refusés |
| Parquet | Marqueur vérifié avec PyArrow |
| PDF texte | Multi-page, Unicode, table, image incorporée et 300 pages vérifiés |
| PDF OCR | Fixture image-only scannée, marqueur vérifié avec RapidOCR |
| DOCX, XLSX, PPTX | Marqueurs vérifiés dans de vrais conteneurs Office |
| ODT, ODS, ODP | Marqueurs vérifiés avec `odfdo` installé par `[all]` |
| XLS legacy | Vrai BIFF8, marqueur vérifié via MarkItDown |
| MSG | Vrai conteneur CFB/OLE2 synthétique, sujet et corps vérifiés via `extract-msg` |
| EPUB | Vrai conteneur EPUB, marqueur vérifié |
| Images JPEG, WEBP, BMP | OCR et marqueur vérifiés |
| PNG, TIFF | Échec reproductible : Markdown vide avec les backends testés |
| PNG tourné / texte minuscule | Conversion sans marqueur récupéré ; non revendiqué |
| WAV, MP3, FLAC, OGG, M4A | Échec explicite sous `[all]` : Whisper/ASR absent |
| AVI, MKV, MOV, MP4, WEBM | Même blocage ASR, explicitement signalé |
| DOC et PPT legacy | Non testés : LibreOffice absent de l'hôte |
| PDF chiffré/corrompu, DOCX/PNG corrompus | Échec isolé dans `errors.jsonl`, aucune fabrication |

Le harness a traité 44 fixtures, dont MSG séparément : 18 formats riches ont conservé
leur marqueur dans le batch, deux images ont converti sans marqueur récupérable, 23
entrées ont produit un échec explicite, et aucune n'a fait crasher le pipeline. Les
formats core sont en plus vérifiés dans un test paramétré dédié.

## 6. Cross-platform et versions Python

Localement, la suite a été exécutée sous Python 3.11 et 3.12. Le workflow
`deep-validation.yml` définit une matrice Ubuntu/Windows/macOS × Python 3.11/3.12/3.13
pour le core et l'installation wheel propre. Les collisions portables sont testées par
normalisation déterministe, même lorsque le filesystem Windows ne permet pas de créer
toutes les variantes simultanément.

La preuve directe des correctifs Codex sur Linux/macOS/Python 3.13 dépend des checks de
la pull request de cette branche ; elle est un gate de release, pas une inférence depuis
le run vert de `main` antérieur aux correctifs.

## 7. Performance et mémoire

Mesures sur le même poste Windows/Python 3.11, corpus synthétique mixte :

| Candidat | Fichiers | Cold | Incrémental inchangé | Gain | RSS pic | Corpus |
|---|---:|---:|---:|---:|---:|---:|
| `main` exact | 100 | 0,46 s | 0,63 s | 0,73× | 28,8 MB | 0,60 MB |
| corrigé | 100 | 0,69 s | 0,66 s | 1,05× | 29,3 MB | 0,61 MB |
| fast-path | 100 | 0,63 s | 0,14 s | 4,66× | 28,9 MB | 0,60 MB |
| `main` exact | 1 000 | 4,40 s | 5,67 s | 0,78× | 43,5 MB | 5,97 MB |
| corrigé | 1 000 | 5,61 s | 5,95 s | 0,94× | 42,4 MB | 6,06 MB |
| fast-path | 1 000 | 4,80 s | 1,25 s | 3,85× | 42,9 MB | 6,00 MB |
| `main` exact | 10 000 | 45,01 s | 60,29 s | 0,75× | 157,7 MB | 59,90 MB |
| corrigé | 10 000 | 56,56 s | 63,23 s | 0,89× | 159,3 MB | 60,82 MB |
| fast-path | 10 000 | 48,64 s | 12,72 s | 3,82× | 154,8 MB | 60,15 MB |

Le second hash de protection TOCTOU explique l'essentiel du surcoût cold sur les gros
fichiers. Ce coût est accepté : enlever cette preuve recréerait une fausse attribution
de provenance.

| Source texte unique | `main` RSS | Corrigé RSS | Corrigé temps | Corpus généré |
|---:|---:|---:|---:|---:|
| 5 MB | 164,7 MB | 159,3 MB | 0,42 s | 12,07 MB |
| 25 MB | 250,2 MB | 195,2 MB | 1,94 s | 60,35 MB |
| 100 MB | 774,5 MB | 605,2 MB | 7,09 s | 241,34 MB |

Le streaming JSONL réduit le pic 100 MB d'environ 21,9 %, mais ne résout pas la cause
architecturale : tous les documents et chunks restent matérialisés pour construire les
artefacts globaux. Le pic demeure environ 6× le source. Un redesign de pipeline n'a pas
été imposé à la dernière minute.

Le fast-path utilise réellement sa voie courte et offre un gain mesurable, mais ses
artefacts peuvent être obsolètes ou forgés. La vitesse ne compense pas CX-10.

## 8. Tests, packaging et installation

- 120 tests collectés après audit ; la suite riche est divisée en documents, image et
  média afin qu'un outil média manquant ne masque plus les autres formats.
- Les tests ajoutés couvrent cache/state, tampering, TOCTOU, collisions portables,
  atomicité/rollback, archives liées, entrées pathologiques, streaming et diagnostic.
- Les 13 propriétés Hypothesis existantes et le corpus core multi-format ont été
  conservés ; aucun `xfail` n'a été ajouté.
- Wheel et sdist se construisent. Le wheel core s'installe dans un environnement vierge
  et fonctionne depuis un CWD neutre. Le wheel `[all]` s'installe avec tous ses extras,
  `pip check` est propre et un PDF multi-page passe par l'installation propre.
- Les deux entry points `brainforgemd` et `bfmd`, `version`, `doctor`, `formats` et
  `convert` sont exercés. Les sources, docs utiles et tests nécessaires sont présents
  dans le sdist.

## 9. Documentation vérifiée et ajustée

README anglais/français documentent maintenant la publication transactionnelle et le
refus du mode fichier unique sur un corpus multi-source. VALIDATION anglais/français
explique la séparation réelle des tests riches. `doctor`/`formats` ne présentent plus
`[all]` comme suffisant pour l'audio/vidéo.

Les limitations déjà honnêtement décrites — PNG/TIFF, DOC/PPT legacy, ASR séparé,
mémoire et incrémental sans accélération — restent visibles. Aucun support n'a été
ajouté à la documentation sans marqueur reproductible.

## 10. Décision release

### `main` à `6f7d51d`

**`NOT_READY_FOR_V0.1.0`** : CX-01, CX-03, CX-05 et CX-06 permettent une provenance
fausse ou un corpus de génération mixte.

### `engineering/incremental-fastpath` à `2512cd9`

**À ne pas fusionner** : le gain est réel, mais les artefacts dérivés et le state sont
insuffisamment authentifiés/validés. La branche contient surtout des scripts qui
patchent le source en CI plutôt qu'un changement source directement reviewable, et son
workflow est rouge.

### `audit/codex-final-validation`

**`READY_WITH_KNOWN_LIMITATIONS`**, sous réserve des checks de PR sur les neuf couples
OS/Python et du job riche. Les problèmes d'intégrité/reproductibilité démontrés sont
corrigés avec régressions. Restent ouverts : performance incrémentale, mémoire globale,
absence de sandbox des parseurs riches, PNG/TIFF, DOC/PPT legacy et média sans `[asr]`.

Ce verdict n'est pas `READY_FOR_V0.1.0` sans qualificatif : ces limites doivent rester
publiques et les checks de la PR doivent être verts avant toute release.

## 11. Reproduction

Commandes principales :

```powershell
py -3.11 -m pytest --cov=brainforgemd --cov-report=term-missing
py -3.12 -m pytest
py -3.11 -m ruff check .
py -3.11 -m build
py -3.11 tests/integration/smoke_wheel.py
py -3.11 audit/gen_fixtures.py audit/fixtures
py -3.11 audit/run_formats.py audit/fixtures audit/work/codex-format-run
py -3.11 audit/check_corpus.py audit/work/codex-format-run
py -3.11 audit/benchmark.py audit/work/benchmark
```

Les régressions spécifiques sont dans
`tests/test_codex_audit_regressions.py` et
`tests/test_codex_format_markers.py`. Le fixture MSG reproductible est généré par
`audit/make_msg.py`.
