Je suis développeur python.
J'ai besoin d'un WYSIWYG pour la feature suivante :
Permettre à l'utilisateur de saisir différentes actions, de haut en bas, comme un workflow, pour ensuite les dérouler automatiquement dans playwright (qui se charge d'appliquer les étapes, une par une).
Dans un 1er temps, gère des actions simples (chercher un élément dans le html, faire un clique, télécharger la plus grand image, etc...)


Fait moi un prompt pour copilot pro agentique.


-------------------------------
-------------------------------

# prérequis

Dont le formulaire WYSIWYG existant :
Ajoute à droite une seconde colonne (50% d'occupation).

Dans cette nouvelle colonne :
Le but est de concevoir et implémenter un éditeur WYSIWYG permettant à des utilisateurs non techniques de créer des workflows d’automatisation navigateur, qui seront exécutés avec Playwright en Python.

# Contrainte architecturale :
Respecte le pattern architecturale repository, model, controller, viewmodel, et view pour le code.
- La partie lecture/écriture est géré par le repository
- La partie donnée est géré par le model.
- Le controller sert de passe plat.
- Le viewmodel sert à d'intermédiaire entre la view et le controller (ainsi que le mapping des données)
- La view utilise le controller.

# Contrainte playwright :
Le workflow sera exécuté par le code présent 'web_browser_util.py'.
Fait le refactoring nécessaire pour gérer le workflows et l'applications de ses actions.

# Exigences principales

### 1. Éditeur de workflow (WYSIWYG)

- Interface visuelle verticale
- Chaque étape est un “bloc” représentant une action
- L’utilisateur peut :
  - Ajouter une étape
  - Supprimer une étape
  - Réorganiser les étapes
  - Configurer chaque étape
  - Un exemple montre l'usage.

### 2. Actions supportées

Implémenter les actions suivantes :

1. "Trouver un élément"
   - Entrée : sélecteur CSS ou XPath
   - Sortie : référence d’élément (interne)

2. "Cliquer sur un élément"
   - Nécessite un sélecteur

3. "Télécharger la plus grande image"
   - Récupérer toutes les balises `<img>`
   - Identifier l’image avec la plus grande résolution ou taille
   - La télécharger localement

4. "Attendre"
   - Attendre X secondes OU jusqu’à apparition d’un sélecteur

5. "Extraire du texte"
   - Extraire le texte d’un sélecteur
   - Stocker dans une variable

6. Fermeture de tous les onglets qui ne sont pas dans le domaine fournit dans l'URL de départ.

### 3. Modèle de données

Adapter le JSON du fournisseur pour sauvegarder le nouveau workflow :

```json
{
  "steps": [
    {
      "type": "click",
      "selector": "#login-button"
    },
    {
      "type": "wait",
      "timeout": 2000
    }
  ]
}
```

### 4. Vérification

Au moment de sauvegarder, vérifie la cohérence du JSON et des actions.
Au moment de charger, vérifie la cohérence du JSON et des actions.
Lorsque le workflow est exécuté, chaque action doit être disponible dans playwright.


