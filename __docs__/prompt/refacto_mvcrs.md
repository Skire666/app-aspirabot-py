Conformément au pattern architecturale model, controller, view, et repository, je souhaite refactoriser cette fonction.

Découpe cette fonction :
- Déplace la partie lecture/écriture dans la partie repository
- La partie donnée et valeur par défaut est géré par le model.
- Le controller sert de passe plat.
- La view utilise le controller.