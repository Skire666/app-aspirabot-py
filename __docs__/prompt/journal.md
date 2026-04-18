Tu es un architecte logiciel senior spécialisé en Python.

Fait un logger propre et prêt pour la production avec les contraintes et l’architecture suivantes :

## Architecture

* Pattern MVC :
  * View : interface utilisateur Tkinter
  * Controller : gère les actions utilisateur et les erreurs
  * Service : contient la logique métier
  * Repository : gère l’accès aux données

## Exigences de logging

* Utiliser le module standard `logging` de Python
* Créer un `logging.Handler` personnalisé qui envoie les logs dans une `Queue`
* L’interface doit afficher les logs dans un panneau "Journal" (widget Tkinter Text)
* Le handler NE DOIT PAS interagir directement avec Tkinter (aucun couplage UI)
* L’interface doit lire la queue via `after()` (thread-safe)

## Règles de conception du logging

* Le Controller log les actions utilisateur et gère les exceptions
* Le Service log les décisions métier (couche principale de logging)
* Le Repository log uniquement les aspects techniques/debug
* Une exception ne doit être loggée qu’une seule fois (pas de duplication entre couches)
* Utiliser un logging structuré via `extra` lorsque pertinent

## Exigences UI

* Utilise Tkinter
* Fenêtre principale contenant :
  * Champ de saisie
  * Bouton
  * Panneau de logs (scrollable)
* Le panneau de logs doit auto-scroller
* (Bonus optionnel) Colorer les logs selon leur niveau (INFO, WARNING, ERROR)

## Qualité du code

* Respect strict de la séparation des responsabilités
* Aucune logique métier dans l’UI
* Aucun code UI dans le logging handler
* Structure modulaire claire
* Code lisible, maintenable et extensible

## Livrable attendu

* Fournir un code complet et fonctionnel
* Usage de logger hiérarchiques, des niveaux appropriés, et de la rotation des logs pour éviter des fichiers trop volumineux.

## Contraintes :

- Utilise le module `logging` de la bibliothèque standard.
- Supporte au minimum :
  - sortie console.
  - sortie fichier avec rotation.
  - niveau configurable via argument ou variable d’environnement.
- Le format doit inclure :
  - date/heure.
  - niveau.
  - nom du logger.
  - message.
- Évite les doubles handlers si `setup_logger()` est appelée plusieurs fois.
- Prévois un logger modulaire avec `__name__`.
- Ajoute un exemple d’utilisation.
- Ajoute des annotations de type.
- Écris du code PEP 8.
- Documentation du code source est des docstring en respectant le style google.
