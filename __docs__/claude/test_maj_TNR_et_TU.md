Je viens de modifier le code et la variable 'wait_state: str' a été remplacée par 'wait_until: WaitUntilEnum'. 

Corrige les tests, et regarde si le code possède une erreur.

- Tests dans `__tests__/regression_testing/`.
- Framework : **pytest** + **pytest-cov**.
- Commande de référence : pytest __tests__/regression_testing/ --cov=__src__ --cov-report=term-missing

- Tests dans `__tests__/unit_testing/`.
- Framework : **pytest** + **pytest-cov**.
- Commande de référence :  pytest __tests__/unit_testing/ --cov=__src__ --cov-report=term-missing
