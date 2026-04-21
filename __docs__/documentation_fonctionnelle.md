# Documentation Fonctionnelle

## 1. Présentation du projet
Ce projet "Aspirabot" est un outil de Web Scraping disposant d'une Interface Homme-Machine (IHM) basée sur Tkinter. Il permet à un utilisateur de créer, configurer et exécuter des workflows d'extraction de données ou d'automatisation web de façon visuelle, sans recourir au code source. L'outil repose sur Playwright pour simuler un véritable navigateur afin de contourner les détections antibots standards.

## 2. Fonctionnalités principales

### 2.1. Interface Utilisateur (IHM) à onglets
L'application est structurée autour de plusieurs onglets dédiés :
- **Onglet Fournisseurs :** Liste l'intégralité des configurations (fournisseurs) disponibles au format JSON. Permet de trier, de lancer le scraping, de modifier ou de supprimer une configuration, ainsi que d'ouvrir le dossier système les contenant.
- **Onglet Mettre à jour (Création/Édition) :** Éditeur visuel pour paramétrer un fournisseur. L'utilisateur peut définir l'URL, activer/désactiver l'affichage du navigateur ou l'obfuscation anti-bot, et surtout construire un **Workflow** étape par étape (`FIND_ELEMENT`, `CLICK`, `WAIT`, `EXTRACT_TEXT`, etc.).
- **Onglet Scraping :** Suivi en direct du processus d'automatisation pour le fournisseur sélectionné. Affiche les logs en temps réel envoyés par le navigateur et propose des commandes pour Stoper ou Relancer le processus en toute sécurité.
- **Onglet Journal :** Affiche les logs globaux du logiciel (informations de debug, erreurs, informations système) dans une console scrollable, avec coloration syntaxique par niveau de sévérité.

### 2.2. Navigation et Workflow paramétrable
L'outil s'appuie sur un système de "Fournisseurs" (fichiers JSON) contenant toutes les instructions. 
L'utilisateur peut orchestrer des actions :
- Extraction de texte ciblée (Sélecteurs CSS/XPath).
- Clics et interactions sur la page.
- Attente explicite (Timeout) ou conditionnelle (Apparition d'un sélecteur).
L'exécution est asynchrone, permettant à l'interface de rester totalement réactive pendant les requêtes web.

### 2.3. Contournement des protections anti-robots (Anti-Bot)
L'interface propose des options intégrées pour maximiser la réussite du scraping :
- **Browser affiché VS Headless :** Permet de masquer ou d'afficher le processus visuel de Chromium.
- **Automatisation obfusquée :** Injection automatique de scripts désactivant les drapeaux révélateurs (`navigator.webdriver`, etc.) via Playwright.

## 3. Scénario d'utilisation type
1. L'utilisateur lance le logiciel.
2. Dans l'onglet *Fournisseurs*, il clique sur "Créer un fournisseur" (ou choisit d'en modifier un existant).
3. Via l'éditeur, il saisit un *Nom*, une *URL*, et ajoute quelques étapes dans la zone *Workflow* (ex: `WAIT` suivi d'un `EXTRACT_TEXT`). Il sauvegarde le fournisseur.
4. L'utilisateur retourne dans *Fournisseurs*, et clique sur "Lancer" sur sa nouvelle configuration.
5. L'application bascule sur l'onglet *Scrapping*. L'utilisateur observe l'initialisation du moteur en arrière-plan, la navigation, puis l'exécution des étapes avec le compte rendu en temps réel.
6. Le logiciel clôture la session proprement (succès ou erreur) et le résultat ainsi que les logs finaux s'affichent.
