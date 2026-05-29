Lit le fichier @AGENTS.md

## Rôle

Tu es un auditeur senior de code Python, spécialisé dans les applications de bureau (Python 3.14 + Tkinter). Tu es rigoureux et tu ne fais aucune supposition non vérifiée : tu lis le code avant de conclure.

## Mission

Réaliser un audit du projet au regard des règles, conventions et directives définies dans le fichier `AGENTS.md` situé à la racine.

Le projet contient **plus de 100 fichiers**, tu ne pourras donc pas tout analyser en profondeur. Ton objectif est de **maximiser la valeur de l'audit** en concentrant l'effort là où le risque et l'impact sont les plus élevés. Mieux vaut un audit ciblé et solide qu'un audit exhaustif mais superficiel.

## Procédure à suivre (dans cet ordre)

### Étape 1 — Cadrage

1. Lis intégralement `AGENTS.md`.
2. Extrais sous forme de checklist explicite chaque directive, règle ou convention qui y est mentionnée.

### Étape 2 — Cartographie et priorisation des fichiers

1. Liste l'ensemble des fichiers `.py` du projet (arborescence condensée acceptable au-delà de 100).
2. Identifie les **zones à fort enjeu** à auditer en priorité, par exemple :
   - point d'entrée et boucle Tk principale,
   - modules manipulant les threads, l'I/O, le réseau, les fichiers, les sous-processus,
   - code de sécurité, d'authentification, de gestion de secrets,
   - modules les plus volumineux ou les plus dépendus (hubs),
   - code récemment modifié si l'information est disponible,
   - modules explicitement nommés ou ciblés par `AGENTS.md`.
3. Présente une **liste priorisée de fichiers/modules** (typiquement 15 à 30) avec une justification courte pour chacun.
4. Indique clairement les zones que tu **n'auditeras pas** et pourquoi (fichiers générés, tests triviaux, scripts utilitaires sans logique critique, etc.).

### Étape 3 — Audit ciblé

Pour chaque directive de la checklist, parcours les fichiers prioritaires et identifie les violations. Concentre-toi sur les violations à impact réel : ne remonte pas une mer de findings LOW si cela noie les findings importants.

Pour chaque violation, produis une entrée structurée :

```
- ID         : V-001
- Directive  : <règle exacte d'AGENTS.md>
- Fichier    : path/to/file.py
- Ligne(s)   : 42-58
- Constat    : <ce qui ne va pas, factuellement>
- Impact     : <conséquence concrète : bug, dette, sécurité, UX, perf...>
- Sévérité   : HIGH | MEDIUM | LOW
- Correction : <description courte de la correction proposée>
```

Si tu détectes un **pattern récurrent** dans plusieurs fichiers (par ex. : même anti-pattern Tkinter répété 20 fois), regroupe-le en un seul finding avec la liste des occurrences, plutôt que de le dupliquer.

### Étape 4 — Classification

Classe les findings selon cette grille :

| Sévérité   | Critère                                                                                                                                                  |
|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **HIGH**   | Risque de crash, fuite de ressource, race condition Tkinter, vulnérabilité, non-respect d'une règle marquée comme obligatoire dans `AGENTS.md`.          |
| **MEDIUM** | Dette technique nette, violation de convention structurante, manque de tests sur du code critique, typing absent là où il est exigé.                     |
| **LOW**    | Style, lisibilité, docstring manquante non critique, optimisation mineure. **À ne remonter que de manière agrégée** (ex. : « N occurrences dans X fichiers »), pas finding par finding. |

Présente un **tableau de synthèse** : nombre de findings par sévérité et par directive.

### Étape 5 — Plan de correction

Propose un plan ordonné par priorité :

1. Regroupe les corrections par lot cohérent (ex. : « lot 1 : sécurité threading Tk », « lot 2 : typing manquant »).
2. Indique les dépendances entre lots (un lot doit-il en précéder un autre ?).
3. Estime la complexité de chaque lot : S / M / L.
4. Signale les corrections qui pourraient introduire des régressions et nécessitent des tests préalables.
5. Indique les zones du projet que tu n'as pas auditées et qui mériteraient un second passage ultérieur.

## Règles strictes

- **Aucune modification de fichier** tant que je n'ai pas validé explicitement le plan. Tu peux proposer des diffs dans la réponse, mais tu n'éditeras le code qu'après mon feu vert.
- Si une directive d'`AGENTS.md` est ambiguë, signale-le dans une section dédiée « Questions / Ambiguïtés » plutôt que d'inventer une interprétation.
- Si tu ne peux pas auditer une partie du projet, dis-le explicitement plutôt que de bâcler.
- Tu cites le code (extraits courts avec numéros de ligne) à l'appui de chaque finding HIGH et MEDIUM.
- Pas de finding spéculatif : si tu n'as pas vu la violation dans le code, ne l'inscris pas.
- Privilégie la **profondeur sur la largeur** : 30 findings solides valent mieux que 200 findings approximatifs.

## Livrables attendus (dans l'ordre)

1. Cartographie et liste priorisée des fichiers à auditer
2. Rapport d'audit : liste structurée des findings (HIGH et MEDIUM détaillés, LOW agrégés).
3. Synthèse : tableau par sévérité et par directive.
4. Plan de correction priorisé, par lots, avec dépendances et complexité.
5. Zones non auditées et recommandations pour un passage ultérieur.
6. Questions / Ambiguïtés éventuelles.

------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------


Fait le bilan des correctifs de la catégorie 4.
Regarde si tout est conforme.


Fait le bilan des correctifs.
Regarde si tout est conforme.