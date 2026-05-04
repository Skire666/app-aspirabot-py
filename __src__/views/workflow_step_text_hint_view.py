## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from typing import ClassVar

# ---------------------------------------------------------------------------
# Contextual help content
# ---------------------------------------------------------------------------


class WorkflowStepTextHint:
    """Centralised help strings displayed in the 'Aide à la saisie' panel.

    Update values in BY_LABEL to customise guidance without touching layout
    or logic code.  Keys must match the values in STEP_TYPE_LABELS exactly.

    Attributes:
        BY_LABEL: Mapping from French step-type label to its help string.
    """

    BY_LABEL: ClassVar[dict[str, str]] = {
        "Ouvrir une URL": (
            "Navigue vers l'URL indiquée et attend que la page soit dans "
            "l'état choisi.\n\n"
            "• URL : adresse complète incluant https://\n"
            "• État d'attente :\n"
            "  -load : attend l'événement window.load\n"
            "  -domcontentloaded : attend le DOM (plus rapide)\n"
            "  -networkidle : attend la fin des requêtes réseau\n"
            "  -commit : attend la première réponse HTTP"
        ),
        "Pause fixe": (
            "Attend un délai fixe avant de passer à l'étape suivante.\n\n"
            "• Durée : valeur numérique (entier ou décimal)\n"
            "• Unité : millisecond, second, minute"
        ),
        "Pause aléatoire": (
            "Attend un délai aléatoire compris entre Min et Max.\n"
            "Utile pour simuler un comportement humain.\n\n"
            "• Min : borne inférieure (strictement < Max)\n"
            "• Max : borne supérieure\n"
            "• Unité : millisecond, second, minute"
        ),
        "Rafraîchir la page": (
            "Recharge la page courante du navigateur.\n\n"
            "• Vider le cache : si coché, force un rechargement complet\n"
            "  sans utiliser le cache du navigateur."
        ),
        "Télécharger une image": (
            "Capture et sauvegarde une image présente sur la page.\n\n"
            "• Mode :\n"
            "  -largest : image la plus grande (surface en pixels)\n"
            "  -first / last : première ou dernière image du DOM\n"
            "  -all : toutes les images de la page\n"
            "• Hauteur / Largeur : filtres optionnels sur les dimensions (px)"
        ),
        "Attendre une taille d'image": (
            "Attend qu'une image atteigne les dimensions minimales indiquées.\n"
            "Utile pour les images chargées en progressive ou lazy-load.\n\n"
            "• Hauteur min / max : intervalle de hauteur attendue (px)\n"
            "• Largeur min / max : intervalle de largeur attendue (px)"
        ),
        "Cliquer sur un élément": (
            "Localise un élément via son sélecteur CSS et le clique.\n\n"
            "• Sélecteur CSS : ex. #submit-btn, .card:first-child\n"
            "• Mode de clic :\n"
            "  -Normal : clic standard Playwright\n"
            "  -Forced : clic même si l'élément est masqué\n"
            "  -JS Direct : exécute element.click() via JavaScript"
        ),
        "Attendre un élément": (
            "Attend qu'un élément CSS soit présent dans le DOM avant de "
            "continuer.\n\n"
            "• Sélecteur CSS : ex. .results-loaded, #content\n"
            "  L'exécution est bloquée jusqu'à ce que l'élément soit visible."
        ),
        "Compter les éléments": (
            "Compte les éléments du DOM correspondant à un sélecteur CSS,\n"
            "puis évalue une condition sur ce nombre. L'exécution est\n"
            "bloquée jusqu'à la fin de l'évaluation.\n\n"
            "• Sélecteur CSS : ex. .card, #results li, div.item\n"
            "• Pré-attente : délai appliqué avant le comptage (0 = immédiat)\n\n"
            "• Condition : lecture naturelle\n"
            "  ex. 'C'est un succès si COUNT est supérieur à 3'\n\n"
            "• Opérateurs de plage :\n"
            "  - compris entre (inclus) : value_min ≤ COUNT ≤ value_max\n"
            "  - non compris entre : COUNT hors de [value_min, value_max]\n\n"
            "Le nombre brut d'éléments et le résultat final\n"
            "sont tous deux consignés dans le journal d'exécution."
        ),
        "Défiler vers le bas": (
            "Fait défiler la page vers le bas d'un nombre de pixels donné.\n"
            "Utile pour déclencher le chargement en infinite scroll.\n\n"
            "• Pixels : distance de défilement en pixels (ex. 1000)"
        ),
        "Fermer les onglets": (
            "Ferme les onglets du navigateur selon les critères définis.\n\n"
            "• Filtre URL : chaîne recherchée dans l'adresse des onglets\n"
            "  Si vide, tous les onglets correspondants sont fermés.\n"
            "  Si renseigné, seuls les onglets dont l'URL contient cette\n"
            "  chaîne sont conservés — les autres sont fermés.\n"
            "• Max onglets : nombre maximum d'onglets à conserver (0 = tous)"
        ),
        "Extraire le texte (CSS)": (
            "Extrait du contenu depuis des éléments DOM via un sélecteur CSS.\n\n"
            "• Sélecteur CSS : ex. h1, .title, #price, div.card:first-child\n"
            "• Mode d'extraction :\n"
            "  - innerText : texte visible selon le CSS (recommandé)\n"
            "  - textContent : texte brut incluant les nœuds masqués\n"
            "  - outerHTML : HTML complet incluant la balise elle-même\n"
            "  - innerHTML : HTML interne à l'élément\n"
            "  - value : valeur d'un <input> ou <textarea>\n"
            "• Éléments ciblés :\n"
            "  - Premier / Dernier : un seul résultat extrait\n"
            "  - Tous : résultats joints par un saut de ligne\n\n"
            "Si aucun élément ne correspond, un avertissement est consigné\n"
            "sans interrompre l'exécution."
        ),
        "Sauter à une étape": (
            "Redirige l'exécution vers une autre étape selon le résultat\n"
            "de l'étape précédente.\n\n"
            "• Condition :\n"
            "  - Si succès : saut si l'étape précédente a réussi\n"
            "  - Si échec : saut si l'étape précédente a échoué\n"
            "  - Toujours : saut inconditionnel\n"
            "• Étape cible : étape vers laquelle rediriger l'exécution\n\n"
            "Une étape ne peut pas pointer vers elle-même\n"
            "(boucle infinie interdite)."
        ),
        "Fin du processus": (
            "Marque la fin du flux de scraping et attend un délai fixe\n"
            "avant de libérer les ressources du navigateur.\n\n"
            "• Durée d'attente : délai à respecter avant la fin\n"
            "• Unité : milli-sec, seconde, minute\n\n"
            "Utile pour laisser les actions asynchrones se terminer\n"
            "avant la fermeture du navigateur."
        ),
    }
