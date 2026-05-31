"""Télécharge les transcripts (sous-titres) FR et EN d'une vidéo YouTube.
Stratégie : on télécharge D'ABORD les sous-titres manuels disponibles,
PUIS on teste les sous-titres auto-générés EN et FR (incl. '* (Original)').
Gère le rate-limiting (HTTP 429) avec des délais fixes (5, 10, 15, 20 s).

Pour chaque piste, produit (horodatage TOUJOURS en fin de nom) :
  ID - langue - KIND - clean  - HORODATAGE.txt    (texte nettoyé, une ligne)
  ID - langue - KIND - brute  - HORODATAGE.txt    (texte brut, un segment/ligne)
  ID - langue - KIND - source - HORODATAGE.json3  (source yt_dlp conservée)
où KIND vaut 'manual', 'autogen' ou 'original'.

Installation : pip install yt-dlp
Utilisation  : python transcript.py "<URL>" [--list] [--out DOSSIER]
"""

import glob
import json
import logging
import os
import pathlib
import re
import sys
import time
from datetime import datetime

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# ============================================================
#  CONSTANTES PRINCIPALES
# ============================================================

OUTPUT_DIR = "transcripts"  # dossier de sortie par défaut (--out)

# Formats demandés : json3 en priorité, repli sur VTT (utile en manuel).
SUB_FORMAT_PREF = "json3/vtt"
SUB_EXTS = ("json3", "vtt")  # extensions sources que l'on sait lire

TEXT_EXT = "txt"  # extension des transcripts texte
CLEAN_LABEL = "clean"  # variante nettoyée (une ligne)
RAW_LABEL = "brute"  # variante brute (un segment/ligne)
SOURCE_LABEL = "source"  # fichier source conservé
STAMP_FORMAT = "%Y%m%d_%H%M%S"  # horodatage ajouté EN FIN de nom

# Langues de base autorisées (toutes variantes) + toute piste '* (Original)'
ACCEPTED_NAMES = {"French", "English"}
ORIGINAL_SUFFIX = "(Original)"

# Code langue base -> code 3 lettres (sert à restreindre l'auto à EN/FR)
LANG3 = {"fr": "FRA", "en": "ENG"}

# Origine de la piste -> libellé utilisé dans le nom de fichier ET les logs
KIND_NAMES = {"man": "manual", "auto": "autogen", "orig": "original"}

# Réessais : durées d'attente FIXES (en s) avant chaque nouvel essai
RETRY_DELAYS = [5, 10, 15, 20]
INNER_RETRIES = 3  # réessais internes yt_dlp
REQUEST_SLEEP = 1.5  # pause entre requêtes d'extraction (s)
DOWNLOAD_SLEEP_MIN = 2  # pause min avant un téléchargement (s)
DOWNLOAD_SLEEP_MAX = 6  # pause max avant un téléchargement (s)
PAUSE_BETWEEN_PHASES = 8  # pause entre phase manuelle et phase auto (s)

logger = logging.getLogger("transcript")


# ============================================================
#  OPTIONS yt_dlp
# ============================================================


def build_list_opts() -> dict:
    """Options pour une simple extraction de métadonnées."""
    return {"skip_download": True, "quiet": True, "no_warnings": True, "sleep_interval_requests": REQUEST_SLEEP}


def build_download_opts(langs: list[str], output_dir: str, manual: bool, auto: bool) -> dict:
    """Options de téléchargement (manuel et/ou auto-généré selon les flags)."""
    opts = build_list_opts()
    opts.update(
        {
            "writesubtitles": manual,
            "writeautomaticsub": auto,
            "subtitleslangs": langs,
            "subtitlesformat": SUB_FORMAT_PREF,
            "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
            "retries": INNER_RETRIES,
            "extractor_retries": INNER_RETRIES,
            "sleep_interval": DOWNLOAD_SLEEP_MIN,
            "max_sleep_interval": DOWNLOAD_SLEEP_MAX,
        }
    )
    return opts


# ============================================================
#  SÉLECTION DES LANGUES
# ============================================================


def fetch_info(url: str) -> dict:
    """Récupère les métadonnées de la vidéo SANS rien télécharger."""
    with YoutubeDL(build_list_opts()) as ydl:
        return ydl.extract_info(url, download=False)


def collect_tracks(subs: dict | None) -> list[tuple[str, str]]:
    """Transforme un dict {code: [formats]} en liste de (code, nom)."""
    tracks = []
    for code, formats in (subs or {}).items():
        name = formats[0].get("name") if formats else None
        tracks.append((code, name or code))
    return tracks


def base_name(name: str) -> str:
    """Nom de langue sans parenthèses (ex: 'French (Original)' -> 'French')."""
    return name.split("(")[0].strip()


def is_accepted_name(name: str | None) -> bool:
    """Vrai si la langue de base est autorisée, ou si piste '* (Original)'."""
    if not name:
        return False
    name = name.strip()
    return name.endswith(ORIGINAL_SUFFIX) or base_name(name) in ACCEPTED_NAMES


def lang3(code: str) -> str:
    """Code langue base -> code 3 lettres (ex: 'fr-FR' -> 'FRA')."""
    base = code.split("-")[0].lower()
    return LANG3.get(base, base.upper()[:3])


def manual_selection(info: dict) -> dict:
    """Sous-titres MANUELS retenus : {code: nom}."""
    tracks = dict(collect_tracks(info.get("subtitles")))
    return {c: n for c, n in tracks.items() if is_accepted_name(n)}


def auto_selection(info: dict) -> dict:
    """Sous-titres AUTO retenus, limités à EN et FR : {code: nom}."""
    tracks = dict(collect_tracks(info.get("automatic_captions")))
    return {c: n for c, n in tracks.items() if is_accepted_name(n) and lang3(c) in {"FRA", "ENG"}}


# ============================================================
#  NOMMAGE DES FICHIERS
# ============================================================


def kind_tag(name: str | None, source: str) -> str:
    """Origine de la piste : 'orig', 'man' (manuel) ou 'auto'."""
    if (name or "").strip().endswith(ORIGINAL_SUFFIX):
        return "orig"
    return "man" if source == "manual" else "auto"


def file_stem(video_id: str, code: str, name: str, source: str) -> str:
    """Construit 'ID - langue - KIND' (sans variante, horodatage, extension)."""
    language = base_name(name) or code
    kind = KIND_NAMES[kind_tag(name, source)]
    return f"{video_id} - {language} - {kind}"


def output_path(out_dir: str, stem: str, variant: str, stamp: str, ext: str) -> str:
    """Assemble 'STEM - variante - HORODATAGE.ext' (horodatage en fin)."""
    return os.path.join(out_dir, f"{stem} - {variant} - {stamp}.{ext}")


# ============================================================
#  TÉLÉCHARGEMENT (avec réessais à délais fixes)
# ============================================================


def is_rate_limited(error: Exception) -> bool:
    """Détecte un HTTP 429 dans le message d'erreur."""
    msg = str(error).lower()
    return "429" in msg or "too many requests" in msg


def find_subtitle_files(output_dir: str, video_id: str) -> list[str]:
    """Retrouve UNIQUEMENT les fichiers bruts '<id>.<lang>.<ext>'."""
    # Le point après l'ID évite de capter les fichiers déjà renommés.
    files = []
    for ext in SUB_EXTS:
        files += glob.glob(os.path.join(output_dir, f"{video_id}.*.{ext}"))
    return sorted(files)


def report_partial(error: Exception, files: list[str]) -> list[str]:
    """Échec non réessayable : on convertit ce qui a quand même été récupéré."""
    if files:
        logger.warning("Erreur '%s' : poursuite avec %d fichier(s) déjà obtenu(s).", error, len(files))
    else:
        logger.error("Échec du téléchargement : %s", error)
    return files


def download_subtitles(
    url: str, langs: list[str], output_dir: str, video_id: str, manual: bool, auto: bool
) -> list[str]:
    """Télécharge en tolérant les échecs partiels : l'échec d'une langue ne
    fait pas perdre celles déjà téléchargées. Sur 429, on réessaie pour
    récupérer les langues manquantes (yt_dlp saute celles déjà présentes).
    """
    opts = build_download_opts(langs, output_dir, manual, auto)
    for attempt in range(1, len(RETRY_DELAYS) + 2):
        try:
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            return find_subtitle_files(output_dir, video_id)
        except DownloadError as e:
            got = find_subtitle_files(output_dir, video_id)
            if is_rate_limited(e) and attempt <= len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt - 1]
                logger.warning(
                    "HTTP 429 (essai %d) : %d fichier(s) obtenu(s), réessai dans %ds.", attempt, len(got), delay
                )
                time.sleep(delay)
                continue
            return report_partial(e, got)
        except Exception as e:
            logger.error("Erreur inattendue : %s", e)
            return find_subtitle_files(output_dir, video_id)
    return find_subtitle_files(output_dir, video_id)


# ============================================================
#  LECTURE DES SOUS-TITRES (JSON3 ou VTT) -> LIGNES
# ============================================================


def event_text(event: dict) -> str:
    """Extrait le texte d'un évènement de sous-titre JSON3."""
    segs = event.get("segs")
    if not segs:
        return ""
    return "".join(seg.get("utf8", "") for seg in segs).strip()


def load_json3_lines(path: str) -> list[str]:
    """Lignes brutes depuis un fichier JSON3."""
    with pathlib.Path(path).open(encoding="utf-8") as f:
        events = json.load(f).get("events", [])
    return [event_text(e) for e in events]


def vtt_cue_lines(block: str) -> list[str]:
    """Texte d'un bloc de cue VTT (en retirant timings et balises inline)."""
    result = []
    for line in block.splitlines():
        if "-->" in line or line.startswith(("WEBVTT", "NOTE")):
            continue
        if line.strip().isdigit():
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        if text:
            result.append(text)
    return result


def load_vtt_lines(path: str) -> list[str]:
    """Lignes brutes depuis un fichier VTT."""
    with pathlib.Path(path).open(encoding="utf-8") as f:
        content = f.read()
    lines = []
    for block in content.split("\n\n"):
        lines.extend(vtt_cue_lines(block))
    return lines


def load_lines(path: str) -> list[str]:
    """Charge les lignes brutes selon le format du fichier (json3/vtt)."""
    if path.endswith(".json3"):
        return load_json3_lines(path)
    return load_vtt_lines(path)


def dedup_lines(lines: list[str]) -> list[str]:
    """Supprime l'effet 'karaoké' : ne garde que la ligne la plus complète."""
    out, buffer = [], ""
    for text in lines:
        text = text.strip()
        if not text:
            continue
        if buffer and text.startswith(buffer):
            buffer = text  # version plus complète
        elif buffer and buffer.startswith(text):
            continue  # version partielle ancienne
        else:
            if buffer:
                out.append(buffer)
            buffer = text
    if buffer:
        out.append(buffer)
    return out


# ============================================================
#  CONVERSION & RENOMMAGE
# ============================================================


def code_from_filename(path: str) -> str:
    """Déduit le code langue depuis le nom de fichier téléchargé."""
    base = os.path.basename(path)
    match = re.search(r"\.([A-Za-z0-9\-]+)\.(?:json3|vtt)$", base)
    return match.group(1) if match else "unknown"


def write_text(path: str, text: str) -> None:
    """Écrit un fichier texte UTF-8."""
    with pathlib.Path(path).open("w", encoding="utf-8") as f:
        f.write(text)


def save_transcript(path: str, video_id: str, names: dict, source: str, stamp: str) -> bool:
    """Produit les versions clean + brute et conserve la source renommée."""
    code = code_from_filename(path)
    name = names.get(code, code)
    stem = file_stem(video_id, code, name, source)
    out_dir = os.path.dirname(path)
    try:
        lines = dedup_lines(load_lines(path))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Lecture impossible (%s) : %s", os.path.basename(path), e)
        return False
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    write_text(output_path(out_dir, stem, CLEAN_LABEL, stamp, TEXT_EXT), text)
    write_text(output_path(out_dir, stem, RAW_LABEL, stamp, TEXT_EXT), "\n".join(lines))
    src_ext = path.rsplit(".", 1)[-1]
    pathlib.Path(path).replace(output_path(out_dir, stem, SOURCE_LABEL, stamp, src_ext))
    logger.info(
        "[%s | %s] %d lignes -> %s - %s - %s.%s",
        code,
        KIND_NAMES[kind_tag(name, source)],
        len(lines),
        stem,
        CLEAN_LABEL,
        stamp,
        TEXT_EXT,
    )
    return True


# ============================================================
#  AFFICHAGE / ORCHESTRATION
# ============================================================


def setup_logging() -> None:
    """Configure des logs lisibles, horodatés, avec niveau."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")


def show_tracks(subs: dict | None) -> None:
    """Affiche les pistes d'une source en marquant celles retenues."""
    tracks = collect_tracks(subs)
    if not tracks:
        print("  (aucun)")
        return
    for code, name in sorted(tracks):
        mark = "x" if is_accepted_name(name) else " "
        print(f"  [{mark}] {code:<8} {name}")


def print_available_languages(url: str) -> None:
    """Liste les langues disponibles (mode --list)."""
    logger.info("Récupération des langues disponibles...")
    info = fetch_info(url)
    print("== Sous-titres manuels ==")
    show_tracks(info.get("subtitles"))
    print("== Sous-titres auto-générés ==")
    show_tracks(info.get("automatic_captions"))


def process_phase(url: str, names: dict, source: str, video_id: str, stamp: str, output_dir: str) -> int:
    """Télécharge puis convertit une phase ('manual' ou 'auto')."""
    if not names:
        return 0
    label = "manuels" if source == "manual" else "auto-générés EN/FR"
    logger.info("Phase %s : %d langue(s) -> %s", label, len(names), ", ".join(names))
    is_manual = source == "manual"
    files = download_subtitles(url, list(names), output_dir, video_id, is_manual, not is_manual)
    return sum(save_transcript(p, video_id, names, source, stamp) for p in sorted(set(files)))


def run(url: str, output_dir: str) -> None:
    """Phase 1 (manuel) PUIS phase 2 (auto EN/FR), avec conversion/renommage."""
    pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)
    logger.info("Dossier de sortie : %s", os.path.abspath(output_dir))
    logger.info("Récupération des métadonnées de la vidéo...")
    info = fetch_info(url)
    video_id = info.get("id", "video")
    manual, auto = manual_selection(info), auto_selection(info)
    if not manual and not auto:
        logger.warning("Aucune piste FR/EN ni '* (Original)' disponible.")
        return
    stamp = datetime.now().strftime(STAMP_FORMAT)
    total = process_phase(url, manual, "manual", video_id, stamp, output_dir)
    if auto:
        if manual:
            logger.info("Pause de %ds avant les pistes auto-générées...", PAUSE_BETWEEN_PHASES)
            time.sleep(PAUSE_BETWEEN_PHASES)
        total += process_phase(url, auto, "auto", video_id, stamp, output_dir)
    logger.info("Terminé : %d transcript(s) écrit(s).", total)


def parse_args() -> tuple[str | None, str, bool]:
    """Lit URL, dossier (--out/-o) et le mode --list."""
    url, out_dir, list_only = None, OUTPUT_DIR, False
    it = iter(sys.argv[1:])
    for arg in it:
        if arg == "--list":
            list_only = True
        elif arg in ("--out", "-o"):
            out_dir = next(it, out_dir)
        elif not arg.startswith("-") and url is None:
            url = arg
    return url, out_dir, list_only


def main() -> None:
    setup_logging()
    url, output_dir, list_only = parse_args()
    if url is None:
        print("Usage : python transcript.py <URL> [--list] [--out DOSSIER]")
        return
    if list_only:
        print_available_languages(url)
    else:
        run(url, output_dir)


if __name__ == "__main__":
    main()
