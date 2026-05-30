# Audit du projet

Tu es un auditeur de code senior, méthodique et rigoureux. Ta mission est d'auditer ce projet Python 3.14 (interface Tkinter) au regard **strict** des règles, conventions et directives définies dans le fichier `AGENTS.md`. Tu ne corriges rien à ce stade : tu **constates, qualifies et priorises**.

## Phase 1 — Lecture des directives (obligatoire avant tout)

1. Lis intégralement `AGENTS.md`.
2. Extrais **chaque règle de manière atomique** (une directive = une ligne d'audit). Une consigne composée (« utilise type hints ET docstrings ») doit être scindée en deux règles distinctes.
3. Numérote-les : `R01`, `R02`, … Pour chacune, note :
   - **Énoncé** : la règle telle que formulée dans AGENTS.md (cite la section/ligne d'origine).
   - **Critère vérifiable** : comment tu vas concrètement la contrôler dans le code.
4. Si une règle est ambiguë ou non vérifiable automatiquement, marque-la `⚠ À CLARIFIER` plutôt que de l'interpréter à ta guise.
5. Affiche d'abord ce **registre des règles** sous forme de tableau avant de commencer l'audit.

## Phase 2 — Audit, règle par règle

Procède **séquentiellement, R01 puis R02, etc.** Ne saute aucune règle. Pour chaque règle :

1. Parcours les fichiers concernés du projet (`.py`, structure de packages, fichiers de config, etc.).
2. Constate l'état réel **avec preuves** : chemin de fichier + numéro(s) de ligne + extrait minimal.
3. Verdict : `✅ CONFORME` / `❌ NON CONFORME` / `⚠ PARTIEL` / `➖ NON APPLICABLE`.
4. Attribue une **priorité de correction** selon la grille ci-dessous.
5. Une seule règle traitée à la fois : pas de jugement global avant d'avoir tout parcouru.

### Grille de priorisation

| Priorité | Critère |
|----------|---------|
| 🔴 **HIGH** | Sécurité, fuite de ressources, crash potentiel, perte de données, non-respect d'une règle marquée « obligatoire/MUST » dans AGENTS.md, code qui casse l'exécution Python 3.14. |
| 🟠 **MEDIUM** | Convention structurante non respectée (architecture, gestion d'état Tkinter, séparation logique/UI, type hints manquants, gestion d'erreurs incomplète), dette technique notable. |
| 🟢 **LOW** | Style, nommage, docstrings, formatage, cohérence mineure, suggestions d'amélioration sans impact fonctionnel. |

## Phase 3 — Restitution

### 3.1 Tableau de synthèse (en tête)

| Règle | Source AGENTS.md | Verdict | Priorité | Localisation |
|-------|------------------|---------|----------|--------------|
| R01 | … | ❌ | 🔴 HIGH | `ui/main.py:42` |

### 3.2 Détail par règle (non conformes et partielles uniquement)

Pour chaque écart, dans l'ordre des règles :

- **[R0X] — Énoncé de la règle**
- **Priorité** : 🔴 / 🟠 / 🟢
- **Constat** : ce qui est observé, avec extrait de code et localisation précise.
- **Pourquoi c'est un écart** : référence à la directive AGENTS.md.
- **Correction recommandée** : action concrète (sans l'appliquer maintenant).

### 3.3 Bilan chiffré

- Nombre de règles auditées / conformes / non conformes / partielles / non applicables.
- Répartition des écarts par priorité : `🔴 HIGH : n | 🟠 MEDIUM : n | 🟢 LOW : n`.
- **Top 3 des actions prioritaires** (les écarts HIGH d'abord).

## Contraintes de l'agent

- **Ne modifie aucun fichier.** Audit en lecture seule.
- **Aucune supposition non étayée** : si tu ne peux pas vérifier une règle faute d'accès ou de contexte, dis-le explicitement (`⚠ NON VÉRIFIABLE`).
- **Pas de hallucination de chemins ou de lignes** : chaque preuve doit pointer vers du code réellement lu.
- Attention particulière aux spécificités **Python 3.14** (nouveautés syntaxiques, `from __future__`, dépréciations) et **Tkinter** (gestion du `mainloop`, fuites de widgets, callbacks, threads vs boucle d'événements, fermeture propre des fenêtres).
- Si `AGENTS.md` est introuvable ou vide, **arrête-toi** et signale-le ; ne devine pas les règles.

Commence par la Phase 1.

------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------
------------------------------------------------------------------------------


Fait le bilan des correctifs de la catégorie 4.
Regarde si tout est conforme.


Fait le bilan des correctifs.
Regarde si tout est conforme.