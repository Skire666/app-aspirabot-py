L'objectif est de corriger les erreurs remontées par des logiciels de qualimétrie.

Pour cela, lit le fichier @AGENTS.md et respecte ses directives sans exception pour corriger dans les normes.

1ère étape de qualimétrie :
Lance la commande 'ruff check ./__src__/' avec l'environnement 'venv' d'activé.
Corrige toutes les erreurs.

2ème étape de qualimétrie :
Lance la commande 'python .\__tools__\furripe.py' avec l'environnement 'venv' d'activé.
Corrige toutes les erreurs.

------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------

Fait le bilan des modifications.
Regarde si tout est conforme.
