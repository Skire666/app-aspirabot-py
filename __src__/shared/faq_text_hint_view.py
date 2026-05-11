# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from typing import ClassVar

# ---------------------------------------------------------------------------
# Contextual help content
# ---------------------------------------------------------------------------


class FaqTextTextHint:
    """Centralised help strings displayed in the 'Aide à la saisie' panel.

    Update values in BY_CATEGORY to customise guidance without touching layout
    or logic code. Keys must match the values in STEP_TYPE_LABELS exactly.

    Attributes:
        CATEGORY_HINTS: Mapping from category label to its intro help string.
        BY_CATEGORY: Mapping from category label to step help entries.
    """

    CATEGORY_HINTS: ClassVar[dict[str, str]] = {
        "Usage des données": (
            "Regroupe les données spécifiques données.\n\n"
            "Sélectionnez une étape pour voir comment utiliser les paramètres."
        ),
        "Brique logique": (
            "Regroupe les étapes de navigation, contrôle et "
            "synchronisation.\n\n"
            "Sélectionnez une étape pour voir comment utiliser les paramètres."
        ),
    }

    BY_CATEGORY: ClassVar[dict[str, dict[str, str]]] = {
        "Usage des données": {
            "HTML → Sélecteur CSS": (
                "Transforme un extrait HTML en sélecteur CSS.\n"
                "Penser à faire le 'copy selector' dans chrome/debug (outil devs)\n"
                "\n Tags\n"
                "<h1>Hello</h1>                      → h1\n"
                '<p class="desc">Texte</p>           → p.desc\n'
                '<img class="avatar" src="user.jpg"> → img.avatar\n'
                "<button enabled>Push</button>       → button[enabled]\n"
                "\n Classes\n"
                '<div class="price">19€</div>        → .price\n'
                '<span class="btn prm lrg">OK</span> → .btn.prm\n'
                '<div class="card feat">abcdef</div> → .card.feat\n'
                "\n Avec id -> #\n"
                '<div id="main">                     → #main\n'
                '<span id="stock">En stock</span>    → #stock\n'
                '<img id="logo" src="logo.svg">      → img#logo\n'
                "\n Descendant (qu'importe la prodondeur)\n"
                "<article><a>Voir</a><article>       → article a\n"
                "<ul><li>Item 1</li></ul>            → ul li\n"
                '<div id="xx"><h2>abc</h2></div>     → div#xx h2\n'
                "\n Avec regexp\n"
                '<a href="/page">Lien</a>            → a[href="/page"]\n'
                '<a href="/administrer">Admin</a>    → a[href^="/adm"]\n'
                '<a href="/doc.pdf">Doc</a>          → a[href$=".pdf"]\n'
                "\n Enfant direct\n"
                "<nav><a>Menu</a></nav>              → nav > a\n"
                "<ul><li>Direct</li></ul>            → ul > li\n"
                '<header><img src="bn.jpg"></header> → header > img\n'
                "\n Image\n"
                '<img src="photo.jpg" alt="Prd">     → img[alt="Prd"]\n'
                '<img src="photo.png">               → img[src^="pho"]\n'
                '<img src="photo.jpg">               → img[src$=".jpg"]\n'
                "\n\n"
                "•  id -> # \n"
                "      - Cible un élément unique via son attribut id.\n"
                "      - Un id doit être unique dans la page\n\n"
                "•  > (enfant direct) \n"
                "      - cible uniquement les enfants directs\n"
                "        (pas les descendants profonds)\n"
                "•  $ (finit par) \n"
                "      - Cible une valeur se terminant par...\n"
                '      - Ex: <img src="photo.jpg"> → img[src$=".jpg"]\n'
                "        (src finit par .jpg)\n"
                "•  * (tout ou contient) : deux usages :\n"
                "      - Universel : tout élément → Ex: * (cible tout)\n"
                "      - Valeur qui contient un fragment :\n"
                '      - Ex: <a href="/api/user/123"> → a[href*="user"]\n'
                '            (Le href contient "user")'
            ),
        },
        "Brique logique": {
            "Ouvrir une URL": (
                "Navigue vers l'URL indiquée et attend que la page soit dans "
                "l'état choisi.\n\n"
                "• URL : adresse complète incluant https://\n"
                "• État d'attente :\n"
                "  -domcontentloaded : attend le DOM (plus rapide)\n"
                "  -load : attend page chargée (l'événement window.load)\n"
                "  -networkidle : attend la fin des requêtes réseau"
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
                "Le nombre brut d'éléments et le résultat final\n"
                "sont tous deux consignés dans le journal d'exécution."
            ),
            "Défiler vers le bas": (
                "Fait défiler la page vers le bas d'un nombre de pixels donné.\n"
                "Utile pour déclencher le chargement en infinite scroll.\n\n"
                "• Pixels : distance de défilement en pixels (ex. 1000)"
            ),
            "Fermer des onglets": (
                "Ferme les onglets du navigateur selon les critères définis.\n\n"
                "• Filtre URL : chaîne recherchée dans l'adresse des onglets\n"
                "  Si renseigné, seuls les onglets dont l'URL contient cette\n"
                "  chaîne sont conservés — les autres sont fermés.\n"
                "• Max onglets : nombre maximum d'onglets à conserver"
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
            "Télécharger une image": (
                "Capture et sauvegarde une image présente sur la page.\n\n"
                "• Mode :\n"
                "  -largest : image la plus grande (surface en pixels)\n"
                "  -first / last : première ou dernière image du DOM\n"
                "  -all : toutes les images de la page\n"
                "• Hauteur / Largeur : filtres optionnels sur les dimensions (px)"
            ),
            "Attendre taille d'image": (
                "Attend qu'une image atteigne les dimensions minimales indiquées.\n"
                "Utile pour les images chargées en progressive ou lazy-load.\n\n"
                "• Hauteur min / max : intervalle de hauteur attendue (px)\n"
                "• Largeur min / max : intervalle de largeur attendue (px)"
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
        },
    }
