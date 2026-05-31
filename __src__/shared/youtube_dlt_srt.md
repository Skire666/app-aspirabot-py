# Téléchargeur de transcripts YouTube (FR/EN)

Script Python qui récupère les sous-titres **français et anglais** d'une vidéo YouTube via `yt-dlp`, les convertit en texte lisible, et nomme les fichiers de façon structurée. Conçu pour être robuste face aux limitations de débit de YouTube (HTTP 429) et aux échecs partiels.

---

## Installation

```bash
pip install yt-dlp
```

Le script ne dépend que de `yt-dlp` ; tout le reste vient de la bibliothèque standard.

---

## Utilisation

```bash
# Télécharger les transcripts FR/EN dans le dossier par défaut (./transcripts)
python transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Choisir le dossier de destination
python transcript.py "<URL>" --out ./mes_transcripts
python transcript.py "<URL>" -o "D:/exports/yt"

# Lister les langues disponibles SANS rien télécharger
python transcript.py "<URL>" --list
```

| Argument        | Rôle                                                        |
|-----------------|-------------------------------------------------------------|
| `<URL>`         | URL de la vidéo YouTube (obligatoire, sauf si erreur d'usage)|
| `--list`        | Affiche les pistes disponibles et s'arrête                  |
| `--out` / `-o`  | Dossier de destination (défaut : `transcripts`)             |

---

## Ce que produit le script

Pour **chaque piste retenue**, trois fichiers sont créés selon le schéma :

```
ID - langue - KIND - variante - HORODATAGE.ext
```

Exemple concret pour une vidéo en anglais :

```
huAwz_BR8WM - English - autogen - clean  - 20260531_143000.txt
huAwz_BR8WM - English - autogen - brute  - 20260531_143000.txt
huAwz_BR8WM - English - autogen - source - 20260531_143000.json3
```

### Les champs du nom

- **ID** — identifiant YouTube de la vidéo.
- **langue** — nom lisible de la langue (`French`, `English`).
- **KIND** — origine de la piste :
  - `manual` : sous-titres déposés manuellement par l'auteur (les plus fiables) ;
  - `autogen` : sous-titres générés/traduits automatiquement par YouTube ;
  - `original` : piste auto correspondant à la langue d'origine de l'audio (`* (Original)`).
- **variante** — type de sortie :
  - `clean` : texte nettoyé, **tout sur une seule ligne** ;
  - `brute` : texte brut, **un segment de sous-titre par ligne** ;
  - `source` : fichier source conservé tel quel (`json3` ou `vtt`).
- **HORODATAGE** — date/heure du lancement, format `AAAAMMJJ_HHMMSS`, **identique pour tous les fichiers d'une même exécution** (pratique pour les regrouper).

---

## Comportements importants à connaître

### 1. Sélection des langues
- Sont retenues **toutes les variantes** de `French` et `English` (ex. `French`, `French (France)`, `French (auto-generated)`), ainsi que **toute piste se terminant par `(Original)`**, quelle que soit sa langue.
- La sélection se fait sur le **nom affiché** de la piste, pas seulement sur le code (`fr`, `en`…), pour éviter les ambiguïtés.

### 2. Ordre de téléchargement : manuel d'abord
Le téléchargement se fait en **deux phases distinctes** :
1. **Phase manuelle** — uniquement les sous-titres déposés par l'auteur.
2. **Phase auto** — uniquement les sous-titres auto-générés, **limités à l'anglais et au français**.

Cette séparation est **nécessaire** : dans un seul appel, `yt-dlp` fusionne manuel et auto pour une même langue, ce qui empêcherait de les distinguer et de les ordonner. Une pause (8 s par défaut) sépare les deux phases pour ménager YouTube.

> **Conséquence** : pour une même langue, vous pouvez obtenir **deux jeux de fichiers** (un `manual` et un `autogen`). C'est volontaire — ils se distinguent par le champ KIND.

### 3. Nettoyage de l'effet « karaoké »
Les sous-titres auto-générés réémettent chaque ligne en la reconstruisant mot à mot. Le script ne conserve que la **version la plus complète** de chaque ligne (les versions partielles, qui sont des préfixes, sont éliminées). Cela bénéficie aux deux sorties `clean` et `brute`.

> **Limite connue** : le dédoublonnage repose sur la relation de préfixe entre lignes successives. Si l'ASR fait défiler deux lignes avec un chevauchement portant sur la **fin** d'une ligne, un léger doublon peut subsister.

### 4. Formats : json3 puis VTT
Le format demandé est `json3/vtt`. Les pistes auto sont toujours servies en json3, mais **certains sous-titres manuels ne le sont pas** : le repli sur VTT évite que ces pistes ne produisent aucun fichier. Les deux formats sont lus correctement.

### 5. Résistance au rate-limiting (HTTP 429)
- En cas de 429, le script réessaie avec des **délais fixes** : `5, 10, 15, 20` secondes (soit 5 tentatives maximum).
- Lors d'un réessai, `yt-dlp` saute les fichiers déjà téléchargés ; les tentatives ne servent qu'à récupérer les langues manquantes.

### 6. Tolérance aux échecs partiels
Si une langue échoue (429 persistant, piste indisponible…), les langues **déjà téléchargées sont quand même converties**. Un `WARNING` signale la situation. Une seule langue défaillante ne fait donc plus perdre les autres.

### 7. Reprise des fichiers orphelins
Au lancement, tout fichier source brut déjà présent dans le dossier (`<id>.<lang>.json3` ou `.vtt`) est détecté, converti et renommé. Un run interrompu peut donc être « rattrapé » en relançant la commande dans le même dossier.

### 8. Journalisation
Les étapes majeures sont tracées via le module `logging`, avec horodatage et niveau :

```
14:30:01 [INFO] Dossier de sortie : /home/user/transcripts
14:30:01 [INFO] Récupération des métadonnées de la vidéo...
14:30:03 [INFO] Phase auto-générés EN/FR : 3 langue(s) -> en, en-orig, fr
14:30:09 [INFO] [en | autogen] 312 lignes -> huAwz_BR8WM - English - autogen - clean - 20260531_143000.txt
14:30:25 [WARNING] Erreur '...' : poursuite avec 2 fichier(s) déjà obtenu(s).
14:30:25 [INFO] Terminé : 2 transcript(s) écrit(s).
```

Le niveau (`INFO`/`WARNING`/`ERROR`) et le champ KIND dans les logs permettent de savoir d'un coup d'œil si une piste est manuelle, auto-générée ou originale.

---

## Réglages (constantes en tête de fichier)

| Constante              | Rôle                                                  | Défaut                |
|------------------------|-------------------------------------------------------|-----------------------|
| `OUTPUT_DIR`           | Dossier de sortie par défaut                          | `"transcripts"`       |
| `SUB_FORMAT_PREF`      | Formats demandés à yt-dlp (ordre de préférence)       | `"json3/vtt"`         |
| `ACCEPTED_NAMES`       | Langues de base autorisées (toutes variantes)         | `{"French","English"}`|
| `LANG3`                | Mapping code → code 3 lettres (restriction auto EN/FR)| `{"fr":"FRA","en":"ENG"}` |
| `RETRY_DELAYS`         | Délais fixes (s) entre réessais sur 429               | `[5, 10, 15, 20]`     |
| `STAMP_FORMAT`         | Format de l'horodatage                                | `"%Y%m%d_%H%M%S"`     |
| `PAUSE_BETWEEN_PHASES` | Pause entre phase manuelle et phase auto (s)          | `8`                   |

Quelques personnalisations courantes :
- Mettre le **code** plutôt que le nom dans le champ « langue » : remplacer `base_name(name)` par `code` dans `file_stem`.
- Étendre à d'autres langues : ajouter le nom dans `ACCEPTED_NAMES` et le code 3 lettres dans `LANG3`.
- Ne pas conserver le fichier source : supprimer la ligne `os.replace(...)` finale dans `save_transcript`.

---

## Limites et points d'attention

- Les sous-titres **auto-générés** sont par nature imparfaits (ponctuation, homophones), surtout pour les traductions automatiques.
- La phase auto est **volontairement restreinte** à l'anglais et au français ; les autres langues auto ne sont pas téléchargées, même si elles sont acceptées par leur nom.
- L'accès à un compte connecté (option cookies de yt-dlp) réduit fortement les 429 ; ce n'est pas activé par défaut mais peut être ajouté dans les options de téléchargement.
- Le script ne télécharge **pas** la vidéo : seules les pistes de sous-titres sont récupérées.

---

## Structure interne (vue d'ensemble)

Le code est découpé en petites fonctions ciblées, regroupées par thème :

- **Options yt-dlp** : `build_list_opts`, `build_download_opts`.
- **Sélection des langues** : `fetch_info`, `collect_tracks`, `is_accepted_name`, `manual_selection`, `auto_selection`.
- **Nommage** : `kind_tag`, `file_stem`, `output_path`.
- **Téléchargement** : `download_subtitles`, `report_partial`, `find_subtitle_files`, `is_rate_limited`.
- **Lecture/conversion** : `load_lines` (→ `load_json3_lines` / `load_vtt_lines`), `dedup_lines`, `save_transcript`.
- **Orchestration** : `process_phase`, `run`, `parse_args`, `main`.