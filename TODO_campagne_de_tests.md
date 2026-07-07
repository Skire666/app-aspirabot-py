---------------------------------------------------------------------------
Exemple prompt IA
---------------------------------------------------------------------------

En python, je voudrais un regexp pour transformer une URL et la convertir en un autre résultat.
Le but est d'utiliser le regexp, puis de prendre le résultat, le suffixer à droite de la base, et avoir l'URL finale.

Donne la regexp, la base, et si oui ou non il faut ajouter un '/' à la fin.

Exemple :
https://AA1
https://AA2

Donne :
https://BB1
https://BB2

---------------------------------------------------------------------------
steam
---------------------------------------------------------------------------

"pattern":
store\.steampowered\.com/(app/\d+/[^/?#]+)

"base":
https://store.steampowered.com/

"trailing_slash":
True
	
https://store.steampowered.com/app/3672400/Farever/?snr=1_4_seasonalsale__617
https://store.steampowered.com/app/1172470/Apex_Legends?snr=1_7001_topselling_
https://store.steampowered.com/app/1172470/Apex_Legends/
https://store.steampowered.com/app/1172470/Apex_Legends
https://store.steampowered.com/app/730?snr=1_241_4_teambased_salebrowseall
https://store.steampowered.com/app/730

---------------------------------------------------------------------------
goodread
---------------------------------------------------------------------------

"pattern":
https://www\.goodreads\.com/([^?]+)

"base":
https://www.goodreads.com/

"trailing_slash":
False

https://www.goodreads.com/list/show/19.Best_for_Book_Clubs
https://www.goodreads.com/book/show/219385951-gone-before-goodbye?ref=rae_0
https://www.goodreads.com/book/show/43641.Water_for_Elephants
https://www.goodreads.com/book/show/170448.Animal_Farm

#EOF
