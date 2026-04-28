


E:\app-py-life-selector\src_python_2026_03_sushi_scan


bug :
si créer
et directe une step
il save le fichier, c'est qui qui fait ça ?


Ajouter brique fin
induqer temps écoulée par étape dans le log
compter le nombre de fois qu'une étape est RUN
indiquer si erreur ou succès (true false), dans le code, et le log
Faire un brique IF qui regarde bool et jump
Faire un brique WHILE


Nom et URL
a la sauvegarde
vérifier longueur (c'est à titre indicatif)

plus tard
dispatcher en fonction de l'URL
Pouvoir faire plusieurs workflow selon le dispatch
pouvoir process un fihcier text avec toute les URL en input (faire une regle spéciale ?)


Documenter l'usage des briques que l'on peut ajoute au worlflow.
- commit (URL changée), domcontentloaded (DOM prêt), load (ressources chargées), networkidle (réseau calme)
Playwright propose plusieurs états de chargement lors de la navigation entre les pages, tels que `load` , `domcontentloaded` et `networkidle` . Avec `domcontentloaded` , votre script s'exécutera plus rapidement s'il n'a besoin que de la structure HTML principale et du DOM. Attendez d'avoir besoin de tous vos fichiers multimédias avant d'utiliser ` load` . Si l'activité réseau affecte votre processus, veillez à utiliser `networkidle` une fois que tout est terminé. Étant donné que `networkidle` ralentit les tests, il est préférable d'adapter la stratégie de délai à l'activité de chargement en arrière-plan de la page plutôt que d'utiliser systématiquement `networkidle` .


D'une manière général, les trucs qui nécessite un rendu, alors il faudrait que les briques compatibles soit filtrée en conséquences (à confirmer, mais le scroll il faut quoi ? rien ? un bug ? marche parmagie ?)


Modifier briques qui peuvent vérifer la présence d'un truc :
- resneigner un timeout
Continu, par contre,  si timeout à l'origine ,retour false



Brique spécial :
Regarder état de la dernière étape (d'ailleurs, le display en temps réel ce truc)
Jump to ... -> Si succès -> step ID (+1 par défaut), si Erreur Goto ID


Brique spécial :
Read state : lit le nombre de fois qu'une étape a été exécuté, et renvoie true ou false.
Pratique, je pourrais le combiner avec jump to.
Genre si j'ai fait tel étape X fois, il quitte, ou avance.


Brique spéical :
délcncher la fin (genre juste FIN)


Brique spécial
What if... -> En gros, prends le "false" de la dernière étape, et soit il s'arrête définitivement, soit il relance une step existante.
NOTE PCO : PAS besoin, c'est jump to + FIN


D'une manière générale :
Les jump fait les steps
penser à vérifier tout le temps l'intégrité du truc (le step est un id, et il doit être valide, donc doit exister).
Le but : Faire un truc genre, vérifier la fin, sinon relance à partir d'une certaine étapes ?



Autre brique tout simple : Jump à une étape, et renseigner le nombre de fois qu'il doit faire ça.
concernant le goto special
si succès, déroule la suite



Faire du validators
en mode fluent validation
généré par IA, ça devrait être rapide d'avoir des trucs de base : est vide; est un nombre, et entre X et Y


Brique supplémentaire à ajouter, mais non prioritaire :
- scroll aléatoire humain pour simuler comportement ératique
- rendre visible un élément et le focus (mettre focus dessus)
pratique poru les trucs hros cham pqui se render unqiuemetn lorsque visible
- Brique spéciale : un mode pour télécharger les nouvelles images ? (ne vrai, le mode télécharger la dernière devrait faire le taff)


- Lorsque j'exécute le workflow, il me faut absolument un rapport avec dedans :
- indique toutes les actions (grosse verbosité), le temps passé pour chaque action
- compter les erreurs, les réussites
- Compter le nombre total de clic
- Si erreur : retenir l'URL en cours, et la nature de l'erreur (code HTTP ?)



prendre un screenshot. NOTE PCO s'en servir comme debug de ce qui palnte ?
page.screencast.on('screencastFrame', data => {
  console.log('received frame, jpeg size:', data.length);
});


Débat sur les erreurs fatale :
Dnas l'idéal, faut retru, mais encore fautil pouvoir.
faut juste autoriser la reprise des trucs plantés, genre lister les URL en erreur à la toute fin ?
surtout qu'en plus si erreur du style erreur 500, etc... tu peux rien faire
et en plus ,toutes les URL en sont pas rechargaeble
typiquement sushiscan fait l'URL, mais le compteur de page en cours dedans, il n'est pas save. Donc si tu plante à 103 sur 150, t'es oblifé de tout refaire.
un mode qui dit continué, ou alors refresh, ou alors stop tout
genre ignore, retry, fail.
Surtout que même si la page est chargé, tu as du cloudflare dedans, et pas sur tout le site.
Bref, un enfer de gérer l'echec.




page.waitForSelector(selector[, options])
Cette fonction recherche l'élément dans le DOM et, si elle le rend visible, autorise la page à l'afficher. Cela s'avère important lorsque vous avez besoin d'éléments à l'écran avant d'exécuter votre script.


Ce qu'il manque : une aide, pour savoir quoi saisir
gner des exemples en bas, rapide à copier et à adapter
faudrait un tuto

trop de menu, ça serait bien de faire moins de clique
le tableau, n'a pas de colonne, on pourrait imaginer le template : ID, action, value (est ootionnel) , goto special
J'ai envie de réutiliser mon datagrid
même si il faudrait refondre le truc un peu pour éviter de ne pas pouvoir trier du tout.



WISIWYG temps réel
genre lance un debug (surveiller si déjà lancer)
laisse playwright ouvert
injecte une étape (oneshot)


télécharger l'iamge c'est fait
mais il ne fait rien sur le disque dur
le WebBrowserUtil deviens bordélique, à voir pour refonte
rajouter les options de human_delay

tester chaque choix dans le tableau
et regarder commne ça se comporte.

dans l'édition d'un forunissseur avec les stesp
mettre l'enum a droit d'ajouter, arreter d'ouvrir la 1er fenetre.

config, pas tout le temps calber
pas de vérif de la configuration
replace constante en dur, jpp y'a des doublons

hauteur des boutons, c'est petit, truc de mouche, mettre un style

splashscreen avant de lancer l'application
avec vérif + chargement 

bonus :
lorqu'on edit
sauvegarder temporaire à chaque modif
et ainsi ne pas perdre le travail

ce que j'ai pas :
C'est pas un WYSIWIG en temps réel
c'est juste un éditeur de workflow
il faudrait run une page, et tester en live l'impact d'une action
genre un bouton test ?

journal
pouvoir filtrer les erreurs selon le niveau de log
genre error, warning, info
comme VS et ses filtres


fonction :
manque l'ouverture d'une autre URL
refondre le principe de click et y intégrer une fermeture automatique des autres onglet
le click, n'est assez résilient, reprendre le code d'avant (plus robuste)

// FIN
