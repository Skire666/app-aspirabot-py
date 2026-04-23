
## Prérequis

Rajoute un nouvel onglet 'Scrapping'.
Ce nouvel onglet permettra de suivre la progression du scrapping.
Il se positionne en dernier dans les onglets.

## Nouveau comportement :

Lorque l'on clique sur le bouton 'Lancer' d'un fournisseur, il passe vers le nouvel onglet.
Il journalise en détail toutes les étapes en cours, 1 à 1 (lancement du navigateur, mise en cache, ouverture d'un lien, etc...).
Les messages s'ajoute de haut en bas.
Ce panneau reste actif tant que le scrapping n'est pas terminé (c'est à dire toutes les étapes sont déroulées, ou bien une erreur fatale est survenue).

Pendant le processus de scrapping :
Pendant ce temps là, l'utlisateur ne peut pas faire aucune autre action en lien avec le scrapping ou les fournisseurs.
Bloque les autres actions : lancer un autre scrapping, modifier un fournisseur, supprimer un fournisseur, etc...
L'utlisateur peut changer d'onglet, cela n'affecte pas les opérations en cours.

Si succès (tout se termine) :
Affiche la fin et le résumé (temps écoulées, nombres d'action effectuées).
Il rends la main à l'utilisateur et débloque les actions qui étaient bloquées.

Si échec (une erreur fatale est survenue).
Affiche la fin et résumé (temps écoulées, nombres d'action effectuées) ainsi que l'erreur effectuée.
Il rends la main à l'utilisateur et débloque les actions qui étaient bloquées.

## Composition de l'IHM

Dans le nouvel onglet 'Scrapping' :

Sur la 1ère ligne :

Bouton N°1 à ajouter : "Stopper le scrapping"
En haut du panneau, un bouton "Stopper le scrapping" est affiché et stop de force la fin du scrapping.
Il est disponible tant que le scrapping est en cours. Il est grisé si rien n'est lancé.

Bouton N°2 à ajouter : "Lancer / Relancer"
Un bouton "Lancer / Relancer" permet de lancer/relancer le processus de scrapping.
Il n'est disponiblque que si aucun processus de scrapping est en cours.

En dessous, sur la 2ème ligne :
Un texte résume les informations sur le fournisseur qu'on vient de lancer.

Le reste de la journalisation occupe le bas de l'écran.

## Contrainte d'architecture logicielle

Génère du code propre, maintenable et modulaire en respectant STRICTEMENT l’architecture suivante :

Règles de dépendances (OBLIGATOIRES) :
- View -> utilise uniquement ViewModel OU Controller
- ViewModel -> utilisé uniquement par la View
- Controller -> utilise Service OU Repository OU Model (aucune logique métier complexe)
- Service -> utilise Repository (via interfaces) OU Model
- Model -> Utilisable uniquement par le service
- Repository -> utilise Model
- Converter -> transforme un objet A en objet B (nommage : A_Converter), utilisable partout

Contraintes générales :
- Respecte une séparation stricte des responsabilités (SRP)
- Aucune dépendance circulaire
- Utilise des interfaces (ABC ou Protocol) pour les Repository
- Injection de dépendances obligatoire (pas d’instanciation directe dans les classes métier)
- Typage Python complet (type hints obligatoires)
- Code compatible Python 3.11+
- Chaque couche est pensé pour permettre d'avoir un code testable.

Structure attendue :
- /views
- /viewmodels
- /controllers
- /services
- /models
- /repositories
- /converters
- /interfaces

Règles spécifiques :
- Les Controllers orchestrent, mais ne transforment pas les données
- Les Services contiennent la logique métier
- Les ViewModels préparent les données pour la View
- Les Models représentent les entités métier (simples et cohérentes)
- Les Repositories encapsulent l’accès aux données
- Les Converters sont stateless et isolés

Style de code :
- Lisible, concis, documenté (docstrings)
- Pas de logique inutile
- Nommage explicite (anglais recommandé)

----------------------------------------------------------------------
----------------------------------------------------------------------
REPONSE de Google Pro (Preview) :
----------------------------------------------------------------------
----------------------------------------------------------------------


Les modifications ont été apportées avec succès. J'ai créé un nouvel onglet "Scrapping" dédié au suivi de l'extraction, et fait en sorte qu'il respecte strictement l'architecture en couches et les responsabilités que tu as décrites.

Voici comment la fonctionnalité a été intégrée :

Couche View (views/scraping_panel_view.py)
- Composé de la 1ère ligne (bouton "Stopper" et "Lancer/Relancer").
- Composé de la 2ème ligne (affichage des informations sur le fournisseur).
- Composé du grand panneau texte dédié à la journalisation du composant.
- Ne contient aucune logique métier : uniquement le binding avec le contrôleur, ou la réaction aux variables du ViewModel.

Couche ViewModel (view_models/scraping_view_model.py)
- Maintient l'état des variables d'interfaces (is_running_var, has_provider_var, provider_info_var, logs_var).
- Sert d'intermédiaire pour les données à afficher dans la View.

Couche Controlleur (controllers/scraping_controller.py)
- Orchestre le lien entre la View (et le ViewModel) et le Service.
- Construit le Thread utilisé pour l'exécution asynchrone (permettant que l'IHM tkinter ne "freeze" pas). La gestion concurrente a lieu ici, pour isoler l'orchestration du backend strict.

Couche Logicielle Métier "Service" (services/scraping_service.py)
- Contient la logique d'exécution : il lance Playwright de façon "wrappée", récupère les logs en temps réel, implémente le chronomètre (temps écoulé), compte le processus d'actions, et attrape/rattrape les exceptions afin de retourner un bilan asynchrone complet (Succès oui/non, Temps écoulé, Nombre d'actions).
- Comportements mis en place :
- Onglet à la fin et redirection : Ajouté en dernier dans MultiTabsPanel. Le clic sur "Lancer" (dans la liste des fournisseurs) bascule automatiquement la vue sur l'onglet "Scrapping".
- Le blocage des vues transverses : Dès qu'une tâche est lancée, les onglets "Fournisseurs" et "Mettre à jour" passent à l'état désactivé (state="disabled"), empêchant l'utilisateur de modifier ou déclencher d'autres actions.

Les boutons de contrôle :
- "Stopper le scrapping" : Lève une exception signalant l'arrêt forcé lors de l'exécution, ce qui ferme proprement le contexte du navigateur en cours et finalise le rapport.
- "Lancer/Relancer" : Désactivé quand la tâche tourne, il permet de re-déclencher un run facilement (vide les logs et redémarre).
- Rapport de fin : À la complétion (ou erreur interceptée), le flux dresse un bilan avec les informations requises dans le panneau de texte et déverrouille les onglets et actions.

