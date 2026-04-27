
déployé avec toml (à découvrir)
https://realpython.com/python-toml/
https://stackoverflow.com/questions/62983756/what-is-pyproject-toml-file-for



converters, pour mapper du viewmodel sur du model
https://chatgpt.com/c/69e3835e-b140-83eb-99e3-2a2f6bb733ba



E:\app-py-life-selector\src_python_2026_03_sushi_scan


commit (URL changée), domcontentloaded (DOM prêt), load (ressources chargées), networkidle (réseau calme)



open url, rajouter quoi surveiller :
  ↓ commit (URL changée)
  ↓ domcontentloaded (DOM prêt)  
  ↓ load (ressources chargées)
  ↓ networkidle (réseau calme)

Playwright propose plusieurs états de chargement lors de la navigation entre les pages, tels que `load` , `domcontentloaded` et `networkidle` . Avec `domcontentloaded` , votre script s'exécutera plus rapidement s'il n'a besoin que de la structure HTML principale et du DOM. Attendez d'avoir besoin de tous vos fichiers multimédias avant d'utiliser ` load` . Si l'activité réseau affecte votre processus, veillez à utiliser `networkidle` une fois que tout est terminé. Étant donné que `networkidle` ralentit les tests, il est préférable d'adapter la stratégie de délai à l'activité de chargement en arrière-plan de la page plutôt que d'utiliser systématiquement `networkidle` .

pause aléatoire entre X et Y millsecondes / sec / min / heure


comportement alméatoire humain


actio nqui scrool vers le bas (pratique pour les scroller infini)


rendre visible un élément et le focus (mettre focus dessus)
pratique poru les trucs hros cham pqui se render unqiuemetn lorsque visible


mettre un mode pour télécharger :
Uniquement les nouvelles images
mais ça voufrait gérer le delta avant et apres


faut absolument un report
qui indique toutes les actions, et le temps passé
comp^ter les erreurs, les réussites, le nombre de clique effectuer


quid de la question des boucles ?
Faire un truc genre, vérifier la fin, sinon relance à partir d'une certaine étapes ?


prendre un screenshot. NOTE PCO s'en servir comme debug de ce qui palnte ?
page.screencast.on('screencastFrame', data => {
  console.log('received frame, jpeg size:', data.length);
});





si échec de wait for, je fais quoi ?
je laisse le timeout se dérouler ? et il avance, en mode yolo N
ou juste je refresh, et il retente ?
ou sinon, crash directe
genre il peut planter, mais en vrai, c'est stable tout le temps
et si jamais y'a une erreur :
faut juste autoriser la reprise des trucs plantés, genre URL en erreur à la fin ?
surtout qu'en plus si erreur du style erreur 500, etc... tu peux rien faire
et en plus ,toutes les URL en sont pas rechargaeble
typiquement sushiscan fait l'URL, mais le compteur de page dedans, il n'est pas save. Donc si tu plante à 103 sur 150, t'es oblifé de tout refaire.
un modequi dit continué, ou alors refresh, ou alors stop tout
genre ignore, retry, fail.
Surtout que même si la page est chargé, tu as du cloudflare dedans, et pas sur tout le site.
Bref, un enfer de gérer l'echec.


Fair des jalons si echec ?
ou pas....



transformer l'iamge en waitforimage,

page.waitForSelector(selector[, options])
Cette fonction recherche l'élément dans le DOM et, si elle le rend visible, autorise la page à l'afficher. Cela s'avère important lorsque vous avez besoin d'éléments à l'écran avant d'exécuter votre script.


Ce qu'il manque : une aide, pour savoir quoi saisir
gner des exemples en bas, rapide à copier et à adapter

trop de menu, ça serait bien de faire moins de clique
le tableau, n'a pas de colonne, on pourrait imaginer le template : ID, action, value (est ootionnel) , goto special

concernant le goto special
si succès, déroule la suite
si erreur, jump quelque part, sur un ID
(un comme à l'époque de l'assembleur)

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
