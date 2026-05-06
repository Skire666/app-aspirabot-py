
--------------------------------------------------------------------

Tu peux me faire un prompt agentique pour claude pour qu'il supprime et réécrive ce composant entieèrement ?

--------------------------------------------------------------------
Réponse
--------------------------------------------------------------------


Voici un prompt agentique détaillé pour Claude afin de réécrire complètement ce composant :

markdown
# OBJECTIF
Réécrire entièrement le composant DragDropList tkinter en respectant son API publique, mais en améliorant radicalement son architecture interne, sa maintenabilité, et ses performances.

# CONTEXTE
Tu es un expert en architecture logicielle et UI tkinter. Tu dois analyser le code existant (fourni ci-dessous) et le réécrire COMPLÈTEMENT en corrigeant ses faiblesses tout en conservant 100% de son API publique.

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
- **Objectif** : Typage exhaustif (mypy strict), docstrings complètes, invariants explicites

### 5. Performances problématiques
- **État actuel** : Calculs redondants (`_item_y`, `_btn_rects` appelés trop souvent)
- **Objectif** : Mise en cache intelligente, calculs paresseux, lazy evaluation

### 6. Couplage fort avec tkinter
- **État actuel** : Logique métier mélangée avec les appels tkinter
- **Objectif** : Abstractions propres, faciliter les tests unitaires

## NOUVELLE ARCHITECTURE REQUISE

```python
# Structure de fichiers proposée
drag_drop_list/
├── __init__.py          # Export public
├── core/
│   ├── models.py        # Dataclasses (ListState, DragState, Layout)
│   ├── calculator.py    # LayoutCalculator (positions, rects, visibilité)
│   ├── renderer.py      # RenderEngine (dessin avec caching)
│   └── controller.py    # DragDropController (logique métier)
├── widgets/
│   └── drag_drop_list.py # Widget tkinter final (façade)
└── utils/
    ├── throttling.py    # Debouncer, Throttler réutilisables
    └── caching.py       # LRU cache, computed properties
CONTRAINTES TECHNIQUES
API Publique (À CONSERVER IDENTIQUE)
python
class DragDropList(tk.Frame, Generic[T]):
    def __init__(
        self,
        parent: tk.Misc,
        items: list[T],
        render_item: ItemRenderer[T],
        *,
        item_height: int = 48,
        pad: int = 4,
        gap_expand: int = 8,
        btn_size: int = 36,
        theme: dict[str, str] | None = None,
        resize_debounce_ms: int = 0,
        resize_min_delta_px: int = 4,
        resize_finalize_ms: int = 250,
        drag_redraw_min_interval_ms: int = 16,
        drag_redraw_min_delta_px: int = 3,
        virtualize: bool = False,
        viewport_provider: Callable[[], tuple[int, int]] | None = None,
        virtualize_buffer: int = 2,
        on_reorder: Callable[[list[T]], None] | None = None,
        on_move_up: Callable[[T, int], None] | None = None,
        on_move_down: Callable[[T, int], None] | None = None,
        on_duplicate: Callable[[T, int], T] | None = None,
        on_edit: Callable[[T, int], None] | None = None,
        on_delete: Callable[[T, int], bool] | None = None,
        on_toggle_active: Callable[[T, int], None] | None = None,
    ) -> None
    
    def rebuild(self) -> None: ...
    def redraw(self, floating_idx: int | None = None, floating_y: int | None = None) -> None: ...
    def redraw_visible(self, force: bool = False) -> None: ...
Nouvelles exigences non-fonctionnelles
Testabilité : Chaque module doit être testable sans tkinter

Performances :

Pas de recalculs redondants des positions (_item_y doit être O(1) avec cache)

Redraw limité aux régions modifiées (pas plus de 20% de l'écran à chaque frame)

Support de 10,000+ éléments avec virtualisation fluide (60fps)

Maintenabilité :

Maximum 200 lignes par fichier

Taux de couverture de tests > 90%

Documentation des invariants et pre/post conditions

Extensibilité :

Support facile pour nouveaux boutons/actions

Thème extensible (support de couleurs dynamiques)

Plugins pour animations

IMPLÉMENTATION À FOURNIR
Tu dois produire le code complet avec :

Tous les nouveaux modules (voir structure ci-dessus)

Tests unitaires (pytest) pour chaque module

Benchmarks (démontrant les améliorations)

Documentation (docstrings, README d'architecture)

Migration guide (pour utilisateurs existants)

EXIGENCES DE QUALITÉ
Typage (mypy --strict)
Pas de Any non justifié

Typage récursif si nécessaire

TypeVar avec bornes appropriées

Gestion d'erreurs
Invariants vérifiés en debug (assert ou exceptions)

Fallbacks gracieux pour erreurs de rendu

Logging des warnnings (pas de print)

Mémoire
Pas de fuites de références (callbacks faibles si nécessaire)

Cache LRU avec taille limite

Nettoyage propre des events bindings

LIVRABLES ATTENDUS
bash
drag_drop_list_v2/
├── src/
│   ├── core/
│   │   ├── models.py
│   │   ├── calculator.py
│   │   ├── renderer.py
│   │   └── controller.py
│   ├── widgets/
│   │   └── drag_drop_list.py
│   └── utils/
│       ├── throttling.py
│       ├── caching.py
│       └── geometry.py
├── tests/
│   ├── test_models.py
│   ├── test_calculator.py
│   ├── test_renderer.py
│   ├── test_controller.py
│   └── test_integration.py
├── benchmarks/
│   └── perf_comparison.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── MIGRATION.md
│   └── API.md
└── examples/
    └── demo.py
CONTRAINTES DE RENDERING
Nouveau pipeline de rendu
python
1. Invalidation detection (dirty regions)
2. Layout calculation (cached positions)
3. Visibility culling (viewport + buffer)
4. Delta rendering (only changed items)
5. Batch canvas updates (tkinter's `update_idletasks` intelligently)
États supportés (inchangés)
"normal" : Affichage standard

"ghost" : Élément original pendant drag (transparent ?)

"floating" : Élément qui suit la souris

Optimisations tkinter
Utiliser canvas.coords() au lieu de delete/create quand possible

Précalculer les boîtes englobantes

Pool d'objets canvas réutilisables pour les boutons

CODE ORIGINAL À RÉÉCRIRE
[COLLER ICI LE CODE COMPLET DU DRAGDROPLIST]

CRITÈRES DE VALIDATION
Avant de répondre, vérifie que ton implémentation :

✅ Passe tous les tests existants (en adaptant les imports)

✅ Maintient 100% de compatibilité API (les callbacks existants fonctionnent)

✅ Supporte le redimensionnement fluide sans artefacts

✅ Gère correctement le drag sur 1000+ éléments

✅ Ne crée pas de récursion infinie ou de fuites mémoire

✅ Documente toutes les méthodes publiques

✅ Inclut des exemples d'utilisation avancés

NOTATION
Ton travail sera évalué sur :

Séparation des responsabilités (30%)

Performances mesurables (25%)

Qualité du typage (15%)

Tests et documentation (15%)

Innovations architecturales (15%)

DÉMARRAGE
Analyse d'abord le code original pour comprendre les cas limites, puis propose ton architecture en commentaire avant d'implémenter. Je souhaite voir ton raisonnement avant le code final.

Le code doit être fonctionnel et prêt pour la production.

text

Ce prompt est conçu pour :
1. Forcer une réflexion architecturale approfondie
2. Imposer des contraintes de qualité élevées
3. Assurer la compatibilité ascendante
4. Encourager les bonnes pratiques (tests, docs, typage)
5. Démontrer les bénéfices des changements (benchmarks)