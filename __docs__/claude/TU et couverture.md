# Mission : écrire les tests unitaires du projet

Tu es un ingénieur QA Python senior.
Ta mission est d'écrire et de maintenir une suite de tests unitaires pour ce projet, **jusqu'à atteindre une couverture de code ≥ 80 %**.

## Contexte technique

- **Python 3.14**, application **tkinter**.
- Code source dans `__src__/`, tests dans `__tests__/unit_testing/`.
- Framework : **pytest** + **pytest-cov**.
- `__src__` est déjà sur le `pythonpath`, donc tu importes directement depuis le module source (ex. `from mon_module import MaClasse`) sans préfixer par `__src__`.

Commande de référence (déjà configurée) :

```
pytest __tests__/unit_testing/ --cov=__src__ --cov-report=term-missing
```

## Déroulé attendu (boucle agentique)

1. **Explorer** : liste l'arborescence de `__src__/`, lis chaque module et repère les classes, fonctions publiques, branches conditionnelles et cas limites.
2. **Lancer la couverture initiale** : exécute `pytest` avec la commande `pytest __tests__/unit_testing --cov=__src__ --cov-report=term-missing` et lis le rapport `term-missing` pour identifier précisément les lignes non couvertes (colonne *Missing*).
3. **Écrire/compléter les tests** dans `__tests__/unit_testing/`, en priorisant les modules les moins couverts et la logique métier (pas le boilerplate tkinter).
4. **Relancer** pytest après chaque ajout, lire à nouveau le `term-missing`, et **itérer** jusqu'à ≥ 80 % global.
5. **S'arrêter** uniquement quand tous les tests passent ET que la couverture cible est atteinte. Présenter alors un résumé : couverture obtenue, fichiers ajoutés, zones volontairement non couvertes (avec justification).

## Règles d'écriture des tests

- **Nommage** : fichiers `test_<module>.py`, fonctions `test_<comportement_attendu>`. et être placé dans `__tests__/unit_testing/`. Exemple : `__tests__/unit_testing/test_workflow.py`.
- **Structure AAA** : Arrange / Act / Assert, un comportement testé par test, assertions explicites.
- **Paramétrage** : utilise `@pytest.mark.parametrize` pour couvrir plusieurs cas d'un même comportement plutôt que de dupliquer.
- **Fixtures** : factorise la mise en place commune dans des fixtures (`conftest.py` si partagé entre fichiers).
- **Isolation** : chaque test est indépendant et déterministe. Mocke les I/O, le réseau, les fichiers, l'horloge et toute dépendance externe (`unittest.mock` / `monkeypatch`).
- **Cas limites** : teste les chemins d'erreur, les exceptions attendues (`pytest.raises`), les valeurs aux frontières, les entrées vides/nulles, pas seulement le chemin nominal.

## Spécificités tkinter (important)

L'UI tkinter est difficile et coûteuse à tester directement. Applique ces principes :

- **Sépare logique et présentation** : teste en priorité la logique métier. Si elle est couplée à l'UI, signale-le et propose un refactoring léger plutôt que de tester l'UI brute.
- **Aucun test ne doit exiger un affichage.** Comme il n'y a ni CI ni Xvfb, tout test qui nécessiterait un vrai display est interdit : trouve une stratégie de mock, ou signale dans le rapport final que le comportement n'est pas testable sans affichage.
- **Callbacks/commandes** : invoque directement la méthode liée à un widget (le `command=`) et vérifie son effet, sans passer par la boucle d'événements.
- **Pas de `mainloop()`** dans les tests, jamais de blocage. Si un environnement headless est nécessaire, signale-le explicitement dans le résumé.

## Contraintes

- N'introduis aucune nouvelle dépendance sans le justifier.
- Les fichiers qui se terminent par '*_regression.py' sont des tests de non-régression et ne concerne pas les tests unitaires.
- Ne modifie pas le code source pour faire passer un test, sauf bug réel identifié — dans ce cas, signale-le séparément.
- Si 80 % est inatteignable sans tester du code mort ou du pur boilerplate tkinter, explique pourquoi et propose des marqueurs `# pragma: no cover` ciblés et justifiés.
