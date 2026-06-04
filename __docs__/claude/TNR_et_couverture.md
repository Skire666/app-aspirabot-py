# Mission : générer des tests de non-régression (regression_testing)

Tu es un agent chargé d'écrire des **tests de non-régression** (regression_testing) pour un projet Python existant. Ces tests viennent **en complément** des tests unitaires (unit_testing) déjà présents : ils ne les remplacent pas et ne les dupliquent pas.
Un `regression_testing` vérifie qu'une modification du code (ajout de fonctionnalité, correction de bug, refactoring…) n'a pas « cassé » ce qui marchait déjà avant. L'idée centrale est la régression : une évolution qui réintroduit un dysfonctionnement sur du code existant.

## Contexte du projet

- **Python 3.14**, application **tkinter**.
- Code source dans `__src__/`
- Tests dans `__tests__/regression_testing/`.
- Framework : **pytest** + **pytest-cov**.
- `__src__` est déjà sur le `pythonpath`, donc tu importes directement depuis le module source (ex. `from mon_module import MaClasse`) sans préfixer par `__src__`.

Commande de référence :

```
pytest __tests__/regression_testing/ --cov=__src__ --cov-report=term-missing
```

## Distinction essentielle : 'unit_testing' vs 'regression_testing'

Avant d'écrire quoi que ce soit, garde cette distinction en tête, car elle conditionne tout le travail :

- **Test unitaire (unit_testing)** : Sont existants. Sert à vérifir qu'une fonction/classe fait *ce qu'elle est censée faire*, en isolation, selon la spécification.
- **Test de non-régression (regression_testing)** : Ta mission. **fige le comportement actuellement observé du système** pour qu'une évolution future ne le modifie pas sans qu'on s'en aperçoive. Ce sont souvent des tests de *caractérisation* (golden master) et d'*intégration* couvrant :
  - les **flux complets** / workflows réels (enchaînement de plusieurs unités), pas une fonction isolée ;
  - les **cas limites et valeurs de bord** déjà gérés par le code ;
  - les **bugs déjà corrigés** (un `regression_testing` par bug pour qu'il ne réapparaisse pas) ;
  - les **points d'intégration** entre modules ;
  - les **contrats publics** (signatures, formats de retour, structure des données produites).

Règle d'or : un `regression_testing` capture le comportement **tel qu'il est aujourd'hui**, pas tel qu'il devrait être idéalement. Si tu découvres ce qui ressemble à un bug, **ne le « corrige » pas en faisant passer le test sur le comportement attendu** : documente-le (voir « Garde-fous »).

## Méthodologie (boucle à suivre)

1. **Explorer** : lis l'intégralité de `__src__/` puis `__tests__/`. Construis une carte mentale des modules, des classes, des fonctions publiques et de ce qui est déjà couvert par les 'unit_testing'.
2. **Identifier les lacunes** : repère ce que les 'unit_testing' ne couvrent *pas* — workflows de bout en bout, interactions entre modules, comportements émergents. C'est là que les TNR ont de la valeur.
3. **Prioriser** : concentre-toi d'abord sur le code critique, le plus appelé, et le plus susceptible de casser lors d'un refactor.
4. **Caractériser** : pour chaque comportement ciblé, exécute mentalement (ou réellement) le code pour déterminer la sortie *actuelle*, puis écris un test qui la verrouille.
5. **Écrire** les tests (voir conventions).
6. **Relancer** pytest après chaque ajout, lire à nouveau le `term-missing`, et **itérer** jusqu'à ≥ 70 % global.
7. **S'arrêter** uniquement quand tous les tests passent ET que la couverture cible est atteinte. Présenter alors un résumé : couverture obtenue, fichiers ajoutés, zones volontairement non couvertes (avec justification).

## Spécificités tkinter (important)

Les `regression_testing` sur une GUI sont piégeux. Applique ces principes :

- **Sépare la logique de l'affichage.** Teste en priorité la logique métier, la validation, la gestion d'état et les *callbacks* — pas le rendu pixel.
- **Aucun test ne doit exiger un affichage.** Comme il n'y a ni CI ni Xvfb, tout test qui nécessiterait un vrai display est interdit : trouve une stratégie de mock, ou signale dans le rapport final que le comportement n'est pas testable sans affichage.
- **Teste les callbacks directement** : appelle la méthode liée à un événement plutôt que de simuler un vrai clic.
- **Pas de `mainloop()`** dans les tests, jamais de blocage. Si un environnement headless est nécessaire, signale-le explicitement dans le résumé.
- **Déterminisme** : neutralise tout ce qui dépend du temps, de l'aléatoire ou de l'ordre d'exécution (mock de `time`, seed fixe, etc.).

## Conventions à respecter strictement

- **Nommage des fichiers** : tout fichier de tests doit se terminer par `_regression.py` et être placé dans `__tests__/regression_testing/`. Exemple : `__tests__/regression_testing/auth_workflow_regression.py`.
- **Granularité** : un fichier `*_regression.py` par module ou par fonctionnalité cohérente.
- **Nommage des tests** : `test_<comportement>_<condition>_<résultat_attendu>`, explicite.
- **Structure** : pattern **AAA** (Arrange / Act / Assert), un comportement vérifié par test.
- **Factorisation** : utilise les *fixtures* pytest pour le setup/teardown (notamment le cycle de vie du root tkinter) et `@pytest.mark.parametrize` pour les jeux de valeurs.
- **Isolation** : chaque test est indépendant, sans état partagé ni dépendance à l'ordre d'exécution.
- **Imports** : les modules de `__src__` sont importables directement (grâce à `pythonpath`), ne préfixe pas par `__src__`.
- **Couverture minimale : 70 %.** Les **tests de non-régression** doivent maintenir une couverture d'au moins **70 %** sur `__src__`. Vérifie-le avec `--cov-fail-under=70` ; si le seuil n'est pas atteint, identifie les zones non couvertes (`term-missing`) et complète tes tests.
- **Lisibilité** : chaque assertion non triviale est accompagnée d'un message expliquant le comportement figé.

## Garde-fous (non négociables)

- **Ne modifie jamais le code de `__src__`.** Ta mission est de capturer le comportement existant, pas de le changer.
- **Ne touche pas aux tests unitaires existants.** - Les tests dans `__tests__/unit_testing/` sont la norme et les tests de non-régression dans 'regression_testing' sont leurs suites logiques.

- **Si un comportement semble être un bug** : écris quand même les `regression_testing` qui fige le comportement *actuel*, marque-le clairement (commentaire `# COMPORTEMENT SUSPECT À CONFIRMER` et/ou `@pytest.mark.xfail(reason=...)` selon le cas), et remonte-le dans ton rapport final. Tu ne décides pas seul de ce qui est correct.
- **Tests rapides et déterministes** : pas d'appels réseau, pas de fichiers temporaires non nettoyés, pas de dépendance horloge/aléatoire.

## Livrable attendu

1. Un ou plusieurs fichiers `__tests__/regression_testing/*_regression.py` complets et exécutables.
2. Sortie avec `--cov-fail-under=70` confirmant que tout passe et que la couverture de `__src__` est **≥ 70 %**.
3. Un court rapport final : périmètre couvert, lacunes restantes, comportements suspects identifiés.
