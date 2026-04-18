# Journalisation (Logging)

L'application intègre un système de journalisation complet, robuste et prêt pour la production, basé sur le module standard `logging` de Python. 

Ce système permet de suivre en temps réel l'exécution du programme, le bon déroulement du scraping, ainsi que les éventuelles erreurs rencontrées, et ce, à travers différents canaux.

## 1. Destinations des Logs (Handlers)

Le système de logs diffuse les messages vers trois destinations simultanées :

1. **La Console (Terminal) :** Pratique pour le développeur lors de l'exécution du script en ligne de commande.
2. **Le Fichier avec Rotation (`app.log`) :** Sauvegardé à la racine du projet. 
   - **Rotation :** Pour éviter que le fichier ne s'alourdisse indéfiniment, il est limité à **5 Mo**. Lorsqu'il atteint cette taille, il est archivé (ex: `app.log.1`), et un nouveau `.log` vierge est créé. Le système conserve jusqu'à 3 archives récentes.
3. **L'Interface Graphique (IHM) :** Les logs sont envoyés dynamiquement et de manière sécurisée (Thread-Safe) dans l'onglet **"Journal"** de l'application grâce au gestionnaire personnalisé `GUILoggingHandler`.

## 2. Niveaux de journalisation

Les niveaux suivants sont utilisés dans le code pour catégoriser l'importance de chaque événement :
- **DEBUG** : Détails très techniques et étapes intermédiaires (ex: *Ouverture d'un nouvel onglet*). Uniquement utile pour le débogage.
- **INFO** : Informations générales du bon déroulement (ex: *Démarrage du moteur*, *Titre trouvé*).
- **WARNING** : Avertissements sur des comportements inattendus qui ne bloquent pas le programme (non utilisé par défaut, mais disponible).
- **ERROR / EXCEPTION** : Erreurs bloquantes ou crash (ex: *Playwright n'a pas pu trouver l'élément*, *Problème réseau*). L'utilisation de `logger.exception()` ajoute automatiquement la trace de l'erreur (Stacktrace).

### Changer le niveau de journalisation
Par défaut, le niveau est réglé sur **INFO** (les messages `DEBUG` sont donc masqués).
Pour faire apparaître les logs de débogage, vous pouvez lancer l'application en définissant la variable d'environnement `APP_LOG_LEVEL` :

**Sur Windows (PowerShell) :**
```powershell
$env:APP_LOG_LEVEL="DEBUG"; python main.py
```

**Sur macOS / Linux :**
```bash
APP_LOG_LEVEL=DEBUG python main.py
```

## 3. Architecture Technique

### 3.1. `core/logger.py`
Ce fichier contient la fonction `setup_logger(name, level)` qui configure le format unifié : `Date/Heure | Niveau | Nom du logger | Message`. Il s'assure qu'aucun gestionnaire (handler) n'est dupliqué si la fonction est appelée plusieurs fois, évitant ainsi l'affichage en double des messages.

### 3.2. Intégration IHM (`gui/app.py`)
La classe `GUILoggingHandler` hérite de la classe native `logging.Handler`. Elle intercepte les messages, les formate pour l'utilisateur (`Heure | Niveau | Message`) et les injecte dans le widget de texte de l'onglet "Journal". L'utilisation de la méthode `.after(0, ...)` permet de garantir la sécurité des appels inter-threads entre la boucle événementielle de `tkinter` et `playwright`.

### 3.3. Bonne pratique de modularité
Le moteur de scraping (`scraper/engine.py`) n'a plus besoin qu'on lui passe une fonction de retour (`callback`) de l'IHM. Il déclare de manière complètement autonome son propre logger en début de fichier :
```python
import logging
logger = logging.getLogger(__name__)

# Utilisation :
# logger.info("Message...")
```
Cela permet de découpler totalement la logique métier de l'interface graphique : le moteur envoie des logs dans le "vide", et l'application décide de brancher (ou non) un écouteur pour les afficher.
