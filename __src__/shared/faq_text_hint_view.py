# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import ClassVar

# -----------------------------------------------------------------------------
# Contextual help content
# -----------------------------------------------------------------------------


class FaqTextTextHint:
    """Centralised help strings displayed in the 'Aide à la saisie' panel.

    Update values in BY_CATEGORY to customise guidance without touching layout
    or logic code. Keys must match the values in STEP_TYPE_LABELS exactly.

    Attributes:
        CATEGORY_HINTS: Mapping from category label to its intro help string.
        BY_CATEGORY: Mapping from category label to step help entries.
    """

    CATEGORY_HINTS: ClassVar[dict[str, str]] = {
        "Comportement à connaitre": ("Infos sur les comportements à connaitre\n."),
        "Usage des données": (
            "Infos sur des données spécifiques.\nSélectionnez pour en savoir plus sur une donnée générique.\n"
        ),
        "Brique logique": (
            "Regroupe les étapes de navigation, contrôle et synchronisation.\n\n"
            "Sélectionnez une étape pour voir comment utiliser les paramètres."
        ),
    }

    BY_CATEGORY: ClassVar[dict[str, dict[str, str]]] = {
        "Comportement à connaitre": {
            "Délai d'attente DNS": (
                "Lors d'une ouverture d'une URL avec OpenURL, plusieurs cas de figure peuvent faire échouer l'action\n"
                "- La résolution du DNS interne à chromium peut échouer (timeout, éhec de résolution, etc...).\n"
                "- une redirection http 300 peut subvenir et être cancel"
                " par les sécurités sandbox de l'automatisation\n"
                "\nDu coup, si une page génère un 'ERR_NAME_NOT_RESOLVED',"
                " OpenURL fait un retry (refresh explicite)\n"
                "Par contre, si le refresh échoue à nouveau, où que la page demandée"
                " n'est pas la même que la page résultat, alors OpenURL retourne une erreur"
                "le délai d'attente avant le retry est de 5 secondes"
                " (avant, marche pas), et il n'y a qu'un seul refresh."
            ),
            "Fermer les onglets": (
                "3 choses à savoir sur le fonctionnement de la fermeture des onglets :\n"
                "- Est un find donc cherche partout dans l'URL.\n"
                "- Est insensible à la casse (plus pratique, évite les erreurs de majuscules).\n"
                "- N'est pas un regexp, juste une string plate, donc le '.' n'est pas interprété\n"
                "\nAucune idée si le https est dedans au moment du check (éviter de le mettre)\n"
                "Si le mode n'est pas custom, utilise la dernière URL ouverte par l'event OpenURL\n"
                "Le refresh ne change pas la dernière URL ouverte.\n"
                "Donc si redirection il y a eu, le filtre peut planter\n"
            ),
            "Consommer une URL": (
                "Si la source est cablé en mode 'dossier'\n"
                "Va lire le plus vieux '.url', et update sa date modif à chaque OpenURL\n"
                "L'update se fait au moment de l'ouverture, et non pas à la fin du processus\n"
                "(compliqué fin, car extraction peut échouer, peut lire plusieurs lien, etc...\n"
                "Attention lit en UTF-8, possibilité que le contenu soit mal lu\n"
                "Donc valider à la fin n'est pas une preuve que tout est OK\n"
                "(formatage utf-8, échappement spéciaux, fichier '.url' pas en mode chrome)\n"
            ),
        },
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
            )
        },
        "Type d'étape": {
            "Section": (
                "Étape organisationnelle sans interaction navigateur.\n"
                "Sert à regrouper des étapes sous un titre visible dans le journal.\n"
                "Toujours succès — aucun effet sur l'état du navigateur.\n\n"
                "• Titre : obligatoire, ne peut pas être vide ou uniquement des espaces\n"
                "• Commentaire : optionnel"
            ),
            "Ouvrir une URL": (
                "Navigue vers une URL et attend que la page soit dans l'état choisi.\n\n"
                "• Mode URL :\n"
                "  - Source : consomme la prochaine URL de la source scénario\n"
                "  - Personnalisé : utilise l'URL saisie (doit inclure https://)\n"
                "• État d'attente : domcontentloaded / load / networkidle (idle 500 ms)\n"
                "• Timeout : durée > 0 + unité valide\n"
                "• Délai DNS : entre 1 et 30 secondes\n"
                "  Délai d'attente avant retry si ERR_NAME_NOT_RESOLVED\n\n"
                "Erreurs runtime :\n"
                "  - URL personnalisée vide (mode personnalisé sans URL saisie)\n"
                "  - Source épuisée (mode source, plus d'URL disponible)\n"
                "  - Mismatch navigation : URL résultante ≠ URL cible\n"
                "    (ex. redirection de domaine détectée après navigation)"
            ),
            "Fermer des onglets": (
                "Ferme les onglets dont l'URL contient le filtre,\n"
                "en conservant au plus max_tabs onglets ouverts.\n\n"
                "• Mode filtre :\n"
                "  - Source : utilise la dernière URL ouverte par OpenURL\n"
                "    (le refresh ne met pas à jour cette dernière URL)\n"
                "  - Personnalisé : filtre saisi manuellement\n"
                "• Filtre : substring, insensible à la casse, pas de regexp\n"
                "  (le '.' n'est pas interprété, éviter le préfixe https://)\n"
                "• Max tabs : >= 1\n\n"
                "Erreurs runtime :\n"
                "  - Filtre manquant (mode source sans URL précédemment ouverte)\n"
                "  - L'onglet de travail a été fermé par l'opération"
            ),
            "Rafraîchir la page": (
                "Recharge la page courante du navigateur.\n\n"
                "• Vider le cache : si coché, force Ctrl+F5\n"
                "  (rechargement complet sans cache navigateur)\n"
                "• État d'attente : domcontentloaded / load / networkidle\n"
                "• Timeout : > 0 + unité valide\n\n"
                "Ne met pas à jour la dernière URL ouverte dans le contexte."
            ),
            "Attendre un état de page": (
                "Attend que la page courante atteigne un état de chargement précis.\n"
                "N'effectue aucune navigation — attend uniquement l'état.\n\n"
                "• État : domcontentloaded / load / networkidle (idle 500 ms)\n"
                "• Timeout : > 0 + unité valide\n\n"
                "Utile après un clic ou une action qui modifie la page\n"
                "sans navigation explicite."
            ),
            "Attendre une durée fixe": (
                "Pause inconditionnelle avant de passer à l'étape suivante.\n\n"
                "• Durée : >= 0  (0 = pas d'attente réelle)\n"
                "• Unité : valeur de temps valide\n\n"
                "Valide pour toute durée nulle ou positive.\n"
                "Aucune erreur runtime possible sur cette étape."
            ),
            "Attendre action manuelle": (
                "Suspend l'exécution jusqu'à ce que l'opérateur clique 'Reprendre'.\n\n"
                "• Condition de déclenchement :\n"
                "  - always : pause systématique\n"
                "  - success : pause si l'étape précédente a réussi\n"
                "  - failure : pause si l'étape précédente a échoué\n"
                "• Délai post-reprise : durée > 0 attendue après le clic 'Reprendre'\n"
                "  avant de continuer l'exécution\n"
                "• Unité : valide\n\n"
                "Erreur de config : durée post-reprise doit être > 0."
            ),
            "Compter les éléments": (
                "Compte les éléments DOM correspondant à un sélecteur CSS,\n"
                "puis évalue une condition sur ce nombre.\n"
                "Retour instantané — aucun retry, aucune attente.\n\n"
                "• Sélecteur CSS : obligatoire, non vide\n"
                "• Opérateur : equal / not_equal / greater_than / less_than\n"
                "              greater_or_equal / less_or_equal\n"
                "• Valeur de comparaison : >= 0\n"
                "• Résultat attendu (success_if) : 'success' ou 'failure'\n"
                "  Lecture : 'C'est un succès si COUNT est <opérateur> <valeur>'\n\n"
                "Le nombre brut trouvé et le résultat de la condition\n"
                "sont consignés dans le journal d'exécution."
            ),
            "Compter les images": (
                "Compte les images de la page filtrées par dimensions,\n"
                "puis évalue une condition sur ce nombre.\n"
                "Retour instantané — aucun retry.\n\n"
                "• Largeur min/max et hauteur min/max : filtres en pixels\n"
                "  - min >= 0, max >= 1\n"
                "  - min doit être <= max (hauteur et largeur indépendamment)\n"
                "• Opérateur / valeur / success_if : mêmes règles que 'Compter les éléments'"
            ),
            "Attendre X éléments": (
                "Attend avec retries répétés que le nombre d'éléments CSS\n"
                "corresponde à la condition définie.\n\n"
                "• Sélecteur CSS : obligatoire\n"
                "• Opérateur + quantité (>= 0) : condition à atteindre\n"
                "• Délai entre retries : > 0 + unité valide\n"
                "• Nombre max de retries : > 0\n\n"
                "Erreur runtime si la condition n'est pas atteinte\n"
                "après avoir épuisé tous les retries."
            ),
            "Attendre X images": (
                "Attend avec retries que le nombre d'images filtrées par dimensions\n"
                "corresponde à la condition.\n\n"
                "• Filtres dimensions : mêmes règles que 'Compter les images'\n"
                "  (min >= 0, max >= 1, min <= max)\n"
                "• Opérateur + quantité (>= 0) + retries : mêmes règles que 'Attendre X éléments'\n\n"
                "Utile pour les images chargées en progressive ou lazy-load."
            ),
            "Cliquer sur un élément": (
                "Localise un élément via sélecteur CSS et le clique.\n\n"
                "• Sélecteur CSS : obligatoire\n"
                "• Mode de clic :\n"
                "  - Normal : clic standard Playwright\n"
                "  - Forced : clic même si l'élément est masqué/désactivé\n"
                "  - JS Direct : exécute element.click() via JavaScript\n"
                "• Index : >= 0 (0 = premier élément trouvé par le sélecteur)\n\n"
                "Erreur runtime : aucun élément trouvé pour le sélecteur."
            ),
            "Cliquer pour télécharger": (
                "Clique un élément pour déclencher un téléchargement fichier,\n"
                "puis sauvegarde le fichier dans le dossier d'export.\n\n"
                "• Mêmes paramètres que 'Cliquer sur un élément'\n"
                "  (sélecteur CSS, mode de clic, index)\n"
                "• Timeout de détection download : 10 secondes (non configurable)\n\n"
                "Erreurs runtime :\n"
                "  - Sélecteur CSS ne trouve aucun élément\n"
                "  - Clic effectué mais aucun téléchargement détecté dans le délai\n\n"
                "Note : utilise uniquement le mode JS Direct en interne\n"
                "pour maximiser la compatibilité avec les liens de téléchargement."
            ),
            "Télécharger les images": (
                "Télécharge des images présentes sur la page dans le dossier d'export.\n\n"
                "• Mode : first / last / all\n"
                "• Unique uniquement : filtre les doublons (déduplication)\n"
                "• Filtres dimensions (optionnels) : width_min/max, height_min/max\n"
                "  - min >= 0, max >= 1, min <= max\n\n"
                "Erreur de config si les bornes de dimensions sont incohérentes."
            ),
            "YouTube Transcripts": (
                "Extrait les données textuelles d'une vidéo YouTube via yt-dlp.\n"
                "Utilise la dernière URL ouverte par un step 'Ouvrir une URL'.\n\n"
                "• Titre : obligatoire, non vide (identifiant dans le journal)\n"
                "• Infos de base : si coché, sauvegarde un fichier JSON\n"
                "  avec les métadonnées de la vidéo (titre, durée, vues, etc.)\n"
                "• Sous-titres SRT : si coché, télécharge les sous-titres FR et EN\n"
                "  (manuels en premier, puis automatiques)\n"
                "  - Retry automatique si HTTP 429 (rate-limit YouTube)\n"
                "  - Si aucun sous-titre trouvé pour une langue,\n"
                "    un placeholder .error est créé à la place\n\n"
                "Erreurs runtime :\n"
                "  - 'Infos de base' coché mais aucun fichier JSON produit\n"
                "  - 'Sous-titres SRT' coché mais aucun fichier de sous-titres produit\n\n"
                "Attention : l'étape échoue si aucune des deux options n'est cochée."
            ),
            "Extraire textes": (
                "Extrait du contenu depuis des éléments DOM via sélecteur CSS.\n\n"
                "• Sélecteur CSS : obligatoire\n"
                "• Mode d'extraction :\n"
                "  - innerText : texte visible selon le CSS (recommandé)\n"
                "  - textContent : texte brut incluant les nœuds masqués\n"
                "  - outerHTML : HTML complet incluant la balise elle-même\n"
                "  - innerHTML : HTML interne à l'élément\n"
                "  - value : valeur d'un <input> ou <textarea>\n"
                "• Cible : first / last / all\n"
                "  (all → résultats joints par un saut de ligne)\n"
                "• Clé de mapping : obligatoire, non vide\n"
                "  (nom de la clé dans les données extraites)\n\n"
                "Si aucun élément ne correspond, un avertissement est consigné\n"
                "sans interrompre l'exécution (pas d'erreur fatale)."
            ),
            "Extraire liens": (
                "Extrait les attributs href depuis des éléments DOM via sélecteur CSS.\n\n"
                "• Sélecteur CSS : obligatoire\n"
                "• Cible : first / last / all\n"
                "• Clé de mapping : obligatoire, non vide\n\n"
                "Extrait uniquement l'attribut href — pas le texte du lien.\n"
                "Si aucun élément ne correspond, avertissement sans erreur fatale."
            ),
            "Exporter une variable": (
                "Capture une variable système dans les données extraites du scénario.\n\n"
                "• Variable (valeurs autorisées) :\n"
                "  - datetime_now : horodatage au moment de l'exécution\n"
                "  - last_url : dernière URL ouverte par un step 'Ouvrir une URL'\n"
                "  - last_domain : domaine extrait de la dernière URL ouverte\n"
                "• Clé de mapping : obligatoire, non vide\n\n"
                "Toute valeur de variable hors de ces trois identifiants génère une erreur."
            ),
            "Exporter données (json)": (
                "Écrit toutes les données extraites jusqu'ici\n"
                "dans un fichier JSON dans le dossier d'export.\n\n"
                "• Préfixe fichier : obligatoire, non vide\n"
                "  (préfixé au nom du fichier généré automatiquement)\n\n"
                "Consigne le nombre de clés exportées dans le journal."
            ),
            "Sauter vers l'étape si...": (
                "Redirige l'exécution vers une autre étape selon le résultat\n"
                "de l'étape précédente.\n\n"
                "• Condition :\n"
                "  - success : saut si l'étape précédente a réussi\n"
                "  - failure : saut si l'étape précédente a échoué\n"
                "  - always : saut inconditionnel\n"
                "• Étape cible : doit exister dans le workflow\n\n"
                "Erreurs de config :\n"
                "  - Auto-référence interdite (une étape ne peut pas pointer vers elle-même)\n"
                "  - Étape cible introuvable dans le workflow"
            ),
            "Défiler vers le bas": (
                "Fait défiler la page vers le bas d'un nombre de pixels donné.\n"
                "Utile pour déclencher le chargement en infinite scroll.\n\n"
                "• Pixels : >= 1\n\n"
                "Valeur 0 ou négative génère une erreur de config."
            ),
            "Quitter navigateur": (
                "Termine le flux de scraping et ferme le navigateur\n"
                "après un délai optionnel.\n\n"
                "• Durée d'attente : >= 0  (0 = fermeture immédiate)\n"
                "• Unité : valide\n\n"
                "Utile pour laisser les téléchargements asynchrones\n"
                "se terminer avant la fermeture du navigateur."
            ),
        },
    }


# EOF
