# Journalisation (Logging)

L'application intègre un système de journalisation complet, robuste et prêt pour la production, basé sur le module standard `logging` de Python. 

Ce système permet de suivre en temps réel l'exécution du programme, le bon déroulement du scraping, ainsi que les éventuelles erreurs rencontrées, et ce, à travers différents canaux.

## 1. Destinations des Logs (Handlers)

Le système de logs diffuse les messages vers trois destinations simultanées :

1. **La Console (Terminal) :** Pratique pour le développeur lors de l'exécution du script en ligne de commande.
2. **Le Fichier avec Rotation (`app_aspirabot.log`) :** Sauvegardé automatiquement dans le répertoire racine (et/ou `tmp_logs`).
   - **Rotation :** Pour éviter que le fichier ne s'alourdisse indéfiniment, il est limité en taille. Lorsqu'il l'atteint, il est archivé, et un nouveau `.log` vierge est créé.
3. **L'Interface Graphique (IHM) :** Les logs sont envoyés dynamiquement et de manière sécurisée (Thread-Safe) dans l'onglet **"Journal"** (`LogsPanelView`) de l'application grâce au module `QueueHandler` interceptant les évènements pour Tkinter.

## 2. Niveaux de journalisation

Les niveaux suivants sont utilisés dans le code pour catégoriser l'importance de chaque événement :
- **DEBUG** : Détails très techniques et étapes intermédiaires (ex: *Lancement du bouton*, *Affichage Modale*). Utile pour le débogage de la couche Vue (`views`).
- **INFO** : Informations générales du bon déroulement (ex: *Démarrage du moteur*, *URL Chargée*).
- **WARNING** : Avertissements sur des comportements inattendus qui ne bloquent pas techniquement le programme.
- **ERROR / EXCEPTION** : Erreurs bloquantes ou crash (ex: *Timeout Playwright de 30s introuvable*, *Problème de sélection CSS*). L'utilisation de `logger.exception()` ou `logger.error("...", exc_info=True)` ajoute automatiquement la trace de l'erreur (Stacktrace).

### Changer le niveau de journalisation
Dans le fichier de paramétrage `config-aspirabot.json`, ou via une variable d'environnement si l'application est repensée pour la CI/CD. Actuellement, le niveau par défaut d'affichage écran (console) et IHM est conditionné dans le service `utils/logging_util.py`.

## 3. Architecture Technique

### 3.1. `utils/logging_util.py`
Ce fichier (utilitaire) contient la fonction `setup_logger(log_queue)` qui configure le format unifié : `Date/Heure - Nom du logger - Niveau - Message`. Il s'assure de lier le gestionnaire (handler) de flux système, de fichier tournant, et d'une file d'attente asynchrone sans doublon.

### 3.2. Intégration IHM (`views/logs_panel_view.py`)
La classe `LogsPanelView` hérite de la classe `ttk.Frame`. Elle gère une `queue.Queue` qui reçoit tous les messages de l'application (même depuis un Thread détaché de Playwright). 
L'utilisation de la méthode `.after(50, self._process_log_queue)` permet de scruter toutes les 50 millisecondes si un message est en attente dans la file et de l'insérer proprement dans le composant visuel de Tkinter (qui est par défaut monotâche), en lui injectant une couleur selon le niveau de criticité.

### 3.3. Bonne pratique de modularité
Chaque fichier métier (que ce soit une `view`, un `controller` ou le `scraping_service.py`) n'a plus besoin qu'on lui passe une fonction de retour spécifique pour les erreurs globales. Ils déclarent de manière complètement autonome leur propre logger en début de fichier :
```python
import logging
logger = logging.getLogger(__name__)

# Utilisation :
# logger.info("Message...")
# logger.error("Zut !", exc_info=True)
```
Cela permet de découpler totalement la logique métier de l'interface graphique. Le système capte nativement l'appel `logger.info()` n'importe où dans `app-aspirabot-py` et le redirigera avec succès dans l'IHM `Tkinter`.
