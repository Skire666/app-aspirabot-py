# Documentation Fonctionnelle

## 1. Présentation du projet
Ce projet est un outil de Web Scraping disposant d'une Interface Homme-Machine (IHM). Il permet à un utilisateur de configurer et d'exécuter des tâches d'extraction de données ou d'automatisation web sans avoir besoin de manipuler le code source. L'outil repose sur la simulation d'un véritable navigateur de manière suffisamment réaliste pour contourner les détections antibots standards.

## 2. Fonctionnalités principales

### 2.1. Interface Utilisateur (IHM)
L'application propose une interface graphique simple permettant à l'utilisateur de :
- **Définir le provider cible :** Un champ de texte permet de renseigner l'adresse web vers laquelle le robot doit se diriger.
- **Lancer le Scraping :** Un bouton d'action principal déclenche la procédure. Il se grise pendant l'exécution pour éviter les lancements multiples accidentels.
- **Suivre les journaux (Logs) en temps réel :** Une console de texte intégrée affiche les étapes de la navigation et de l'extraction au fur et à mesure (ex: Initialisation, Navigation, Titre trouvé, etc.).

### 2.2. Navigation et Conservation de Session
L'outil ne repart pas de zéro à chaque lancement. Il gère une "Session Persistante".
- Il conserve le cache, l'historique de navigation et surtout les **cookies**.
- Cela signifie que si l'utilisateur se connecte manuellement ou automatiquement à un site nécessitant une authentification lors d'une session, cette connexion sera conservée pour les exécutions futures.

### 2.3. Contournement des protections anti-robots (Anti-Bot)
Afin de minimiser le risque que le site cible ne bloque l'accès, l'outil déploie automatiquement des stratégies d'évasion :
- Non-déclaration du statut de robot auprès du site web intercepté.
- Simulation d'un contexte de navigateur organique.

## 3. Scénario d'utilisation type
1. L'utilisateur lance le logiciel.
2. Il saisit l'URL `https://mon-site-cible.com` dans le champ dédié.
3. Il clique sur "Lancer le Scraping".
4. L'IHM affiche le démarrage dans les journaux, une page web s'ouvre.
5. Le logiciel navigue, extrait les informations nécessaires (ex: titre de la page) puis termine sa procédure et ferme le navigateur.
6. L'utilisateur lit le résultat dans la zone de texte de l'interface qui confirme la fin du processus.
