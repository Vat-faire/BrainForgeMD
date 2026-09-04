# AI assistance disclosure

*Lire en français ci-dessous / French version below.*

## English

BrainForgeMD is an original project directed and maintained by **Vat-faire**.

The project idea, intended use, product direction, priorities, approvals, and final decisions are attributed to Vat-faire. The development itself has been **AI-assisted**, and this document states that openly.

### Tools used

- **OpenAI ChatGPT** was used as a development assistant and orchestrator.
- It assisted with architecture, implementation, tests, debugging, audits, documentation, repository structure, and GitHub changes.
- GitHub Actions was used to verify the resulting code across supported operating systems and Python versions.

This means BrainForgeMD does **not** claim that every line was manually typed by a human.

It also means the reverse: no AI system is the owner, maintainer, or decision-maker for the project. The use of OpenAI ChatGPT does not imply affiliation with, sponsorship by, or endorsement from OpenAI.

**Final project responsibility and maintenance rest with Vat-faire.**

### How the work is judged

The repository is intended to make the result auditable through normal software-engineering evidence:

- source code under `src/`;
- automated tests under `tests/`;
- GitHub Actions workflows under `.github/workflows/`;
- commit history;
- public architecture and format documentation;
- published limitations and security notes.

The goal is not to ask users to trust how the code was produced. The goal is to let them inspect what was produced, what was tested, what is still limited, and how the project behaves.

### What is not published

This repository does not publish private conversation history, internal reasoning, chain-of-thought, private prompts, account information, or unrelated working notes.

Public transparency is provided through the resulting code, tests, documentation, commit history, CI results, and explicit disclosure of AI assistance.

---

## Français

BrainForgeMD est un projet original dirigé et maintenu par **Vat-faire**.

L’idée du projet, son usage visé, sa direction, ses priorités, les approbations et les décisions finales sont attribuées à Vat-faire. Le développement lui-même a été **assisté par IA**, et ce document le dit ouvertement.

### Outils utilisés

- **OpenAI ChatGPT** a été utilisé comme assistant de développement et orchestrateur.
- Il a servi à l’architecture, à l’implémentation, aux tests, au débogage, aux audits, à la documentation, à la structure du dépôt et aux modifications GitHub.
- GitHub Actions a servi à vérifier le code obtenu sur les systèmes d’exploitation et versions de Python pris en charge par la matrice CI.

Cela signifie que BrainForgeMD ne prétend **pas** que chaque ligne a été tapée manuellement par un humain.

Cela signifie aussi l’inverse : aucun système d’IA n’est propriétaire, mainteneur ou décideur du projet. L’utilisation d’OpenAI ChatGPT n’implique aucune affiliation avec OpenAI, aucun commanditaire et aucune approbation de leur part.

**La responsabilité finale du projet et sa maintenance reviennent à Vat-faire.**

### Comment le travail peut être évalué

Le dépôt vise à rendre le résultat vérifiable avec des preuves normales de développement logiciel :

- le code source sous `src/`;
- les tests automatisés sous `tests/`;
- les workflows GitHub Actions sous `.github/workflows/`;
- l’historique des commits;
- la documentation publique sur l’architecture et les formats;
- les limites et notes de sécurité publiées explicitement.

L’objectif n’est pas de demander aux utilisateurs de faire confiance à la façon dont le code a été produit. L’objectif est de leur permettre d’inspecter ce qui a été produit, ce qui a été testé, ce qui reste limité et comment le projet se comporte.

### Ce qui n’est pas publié

Ce dépôt ne publie pas les conversations privées, le raisonnement interne, les chaînes de pensée, les prompts privés, les informations de compte ni les notes de travail sans rapport avec le produit public.

La transparence publique repose plutôt sur le code obtenu, les tests, la documentation, l’historique des commits, les résultats CI et la déclaration explicite de l’assistance IA.
