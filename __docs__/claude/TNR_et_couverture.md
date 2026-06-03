# Mission : générer des tests de non-régression (TNR)

Tu es un agent chargé d'écrire des **tests de non-régression** pour un projet Python existant. Ces tests viennent **en complément** des tests unitaires déjà présents : ils ne les remplacent pas et ne les dupliquent pas.

## Contexte du projet

- **Python 3.14**, application **tkinter**.
- Code source dans `__src__/`.
- Tests dans `__tests__/`.
- Lancement via **pytest** avec couverture. Configuration existante (`pyproject.toml`) :
  - `testpaths = ["__tests__"]`
  - `addopts = "-v --cov=__src__ --cov-report=term-missing"`
  - `pythonpath = ["__src__"]`

## Distinction essentielle : TU vs TNR

Avant d'écrire quoi que ce soit, garde cette distinction en tête, car elle conditionne tout le travail :

- **Test unitaire (existant)** : vérifie qu'une fonction/classe fait *ce qu'elle est censée faire*, en isolation, selon la spécification.
- **Test de non-régression (ta mission)** : **fige le comportement actuellement observé du système** pour qu'une évolution future ne le modifie pas sans qu'on s'en aperçoive. Ce sont souvent des tests de *caractérisation* (golden master) et d'*intégration* couvrant :
  - les **flux complets** / workflows réels (enchaînement de plusieurs unités), pas une fonction isolée ;
  - les **cas limites et valeurs de bord** déjà gérés par le code ;
  - les **bugs déjà corrigés** (un TNR par bug pour qu'il ne réapparaisse pas) ;
  - les **points d'intégration** entre modules ;
  - les **contrats publics** (signatures, formats de retour, structure des données produites).

Règle d'or : un TNR capture le comportement **tel qu'il est aujourd'hui**, pas tel qu'il devrait être idéalement. Si tu découvres ce qui ressemble à un bug, **ne le « corrige » pas en faisant passer le test sur le comportement attendu** : documente-le (voir « Garde-fous »).

## Méthodologie (boucle à suivre)

1. **Explorer** : lis l'intégralité de `__src__/` puis `__tests__/`. Construis une carte mentale des modules, des classes, des fonctions publiques et de ce qui est déjà couvert par les TU.
2. **Identifier les lacunes** : repère ce que les TU ne couvrent *pas* — workflows de bout en bout, interactions entre modules, comportements émergents. C'est là que les TNR ont de la valeur.
3. **Prioriser** : concentre-toi d'abord sur le code critique, le plus appelé, et le plus susceptible de casser lors d'un refactor.
4. **Caractériser** : pour chaque comportement ciblé, exécute mentalement (ou réellement) le code pour déterminer la sortie *actuelle*, puis écris un test qui la verrouille.
5. **Écrire** les tests (voir conventions).
6. **Relancer** pytest après chaque ajout, lire à nouveau le `term-missing`, et **itérer** jusqu'à ≥ 90 % global.
7. **S'arrêter** uniquement quand tous les tests passent ET que la couverture cible est atteinte. Présenter alors un résumé : couverture obtenue, fichiers ajoutés, zones volontairement non couvertes (avec justification).

## Spécificités tkinter (important)

Les TNR sur une GUI sont piégeux. Applique ces principes :

- **Sépare la logique de l'affichage.** Teste en priorité la logique métier, la validation, la gestion d'état et les *callbacks* — pas le rendu pixel.
- **Privilégie le mock par défaut.** Il n'y a **ni CI ni display virtuel (Xvfb)** : un test ne doit jamais dépendre de la disponibilité d'un affichage. Mocke (`unittest.mock`) les widgets et le root tkinter dès que la logique peut être testée sans boucle d'événements. N'instancie un vrai `tk.Tk()` (puis `root.destroy()` via *fixture*) qu'en dernier recours, et uniquement si le comportement testé l'exige réellement.
- **Teste les callbacks directement** : appelle la méthode liée à un événement plutôt que de simuler un vrai clic.
- **Aucun test ne doit exiger un affichage.** Comme il n'y a ni CI ni Xvfb, tout test qui nécessiterait un vrai display est interdit : trouve une stratégie de mock, ou signale dans le rapport final que le comportement n'est pas testable sans affichage.
- **Déterminisme** : neutralise tout ce qui dépend du temps, de l'aléatoire ou de l'ordre d'exécution (mock de `time`, seed fixe, etc.).

## Conventions à respecter strictement

- **Nommage des fichiers** : tout fichier de TNR doit se terminer par `_regression.py` et être placé dans `__tests__/`. Exemple : `__tests__/auth_workflow_regression.py`.
- **Granularité** : un fichier `*_regression.py` par module ou par fonctionnalité cohérente.
- **Nommage des tests** : `test_<comportement>_<condition>_<résultat_attendu>`, explicite.
- **Structure** : pattern **AAA** (Arrange / Act / Assert), un comportement vérifié par test.
- **Factorisation** : utilise les *fixtures* pytest pour le setup/teardown (notamment le cycle de vie du root tkinter) et `@pytest.mark.parametrize` pour les jeux de valeurs.
- **Isolation** : chaque test est indépendant, sans état partagé ni dépendance à l'ordre d'exécution.
- **Imports** : les modules de `__src__` sont importables directement (grâce à `pythonpath`), ne préfixe pas par `__src__.`.
- **Couverture minimale : 90 %.** Tes TNR, combinés aux TU existants, doivent maintenir une couverture d'au moins **90 %** sur `__src__`. Vérifie-le en lançant `pytest --cov-fail-under=90` ; si le seuil n'est pas atteint, identifie les zones non couvertes (`term-missing`) et complète tes tests.
- **Lisibilité** : chaque assertion non triviale est accompagnée d'un message expliquant le comportement figé.

## Garde-fous (non négociables)

- **Ne modifie jamais le code de `__src__`.** Ta mission est de capturer le comportement existant, pas de le changer.
- **Ne touche pas aux tests unitaires existants.**
- **Si un comportement semble être un bug** : écris quand même le TNR qui fige le comportement *actuel*, marque-le clairement (commentaire `# COMPORTEMENT SUSPECT À CONFIRMER` et/ou `@pytest.mark.xfail(reason=...)` selon le cas), et remonte-le dans ton rapport final. Tu ne décides pas seul de ce qui est correct.
- **Tests rapides et déterministes** : pas d'appels réseau, pas de fichiers temporaires non nettoyés, pas de dépendance horloge/aléatoire.

## Livrable attendu

1. Un ou plusieurs fichiers `__tests__/*_regression.py` complets et exécutables.
2. Sortie de `pytest --cov-fail-under=90` confirmant que tout passe et que la couverture de `__src__` est **≥ 90 %**.
3. Un court rapport final : périmètre couvert, lacunes restantes, comportements suspects identifiés.
