
--------------------------------------------------------------------

Tu peux me faire un prompt agentique pour claude pour qu'il supprime et réécrive ce composant entieèrement ?

# OBJECTIF
# CONTEXTE
## PROBLÈMES IDENTIFIÉS À CORRIGER

### 1. Architecture et séparation des responsabilités
- **État actuel** : Une seule classe gère rendu, logique métier, événements, et optimisations
- **Objectif** : Découper en modules cohérents (StateManager, RenderEngine, DragController, LayoutCalculator)

### 2. Gestion d'état complexe et fragile
- **État actuel** : 30+ variables d'instance avec dépendances implicites
- **Objectif** : État centralisé et immuable (dataclasses) avec transitions claires

### 3. Logique de redraw inefficace
- **État actuel** : Redraws complets fréquents, calculs de visibilité répétés
- **Objectif** : Dirty rectangles, invalidation intelligente, rendu différé

### 4. Manque de typage et documentation
- **État actuel** : Typage partiel, documentation éparse
- **Objectif** : Typage exhaustif (basedpyright strict), docstrings complètes, invariants explicites

### 5. Performances problématiques
- **État actuel** : Calculs redondants (`_item_y`, `_btn_rects` appelés trop souvent)
- **Objectif** : Mise en cache intelligente, calculs paresseux, lazy evaluation

### 6. Couplage fort avec tkinter
- **État actuel** : Logique métier mélangée avec les appels tkinter
- **Objectif** : Abstractions propres, faciliter les tests unitaires

## NOUVELLE ARCHITECTURE REQUISE

# Structure de fichiers proposée

- Nouvelles exigences non-fonctionnelles
- Testabilité : Chaque module doit être testable sans tkinter
- Performances :
- Maintenabilité :
- Extensibilité :

# IMPLÉMENTATION À FOURNIR
# EXIGENCES DE QUALITÉ
# LIVRABLES ATTENDUS
# CONTRAINTES DE RENDERING
# CODE ORIGINAL À RÉÉCRIRE
# CRITÈRES DE VALIDATION

Analyse d'abord le code original pour comprendre les cas limites, puis propose ton architecture en commentaire avant d'implémenter. Je souhaite voir ton raisonnement avant le code final.
Le code doit être fonctionnel et prêt pour la production.
