"""Download YouTube transcripts (FR/EN subtitles) via yt-dlp.

Strategy: manual subtitles are downloaded first, then auto-generated EN/FR
(including any '* (Original)' tracks). HTTP 429 rate-limiting is handled with
fixed-delay retries.

Each accepted track produces three output files, timestamp always at the end:
  ID - lang - KIND - clean  - TIMESTAMP.txt    (cleaned text, single line)
  ID - lang - KIND - brute  - TIMESTAMP.txt    (raw text, one segment per line)
  ID - lang - KIND - source - TIMESTAMP.json3  (raw yt-dlp source kept on disk)
where KIND is 'manual', 'autogen', or 'original'.

Installation: pip install yt-dlp
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import json
import logging
import pathlib
import re
import time
from datetime import datetime

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# ============================================================
#  Main constants
# ============================================================

OUTPUT_DIR = "transcripts"  # default output directory

# Preferred subtitle format; json3 first, VTT as fallback (useful for manual).
SUB_FORMAT_PREF = "json3/vtt"
SUB_EXTS = ("json3", "vtt")  # source file extensions we know how to parse

TEXT_EXT = "txt"         # output text file extension
CLEAN_LABEL = "clean"    # cleaned variant (single line)
RAW_LABEL = "brute"      # raw variant (one segment per line)
SOURCE_LABEL = "source"  # kept source file label
STAMP_FORMAT = "%Y%m%d_%H%M%S"  # timestamp appended at the END of the filename

# Accepted base languages (all variants) plus any '* (Original)' track.
ACCEPTED_NAMES = {"French", "English"}
ORIGINAL_SUFFIX = "(Original)"

# Base language code -> 3-letter code (used to restrict auto-generated to EN/FR).
LANG3 = {"fr": "FRA", "en": "ENG"}

# Track origin -> label used in filenames and logs.
KIND_NAMES = {"man": "manual", "auto": "autogen", "orig": "original"}

# Retry delays in seconds (fixed); one entry per retry attempt.
RETRY_DELAYS = [3, 6]  # old = [5, 10, 15, 20] --- IGNORE ---
PAUSE_BETWEEN_PHASES = 3  # pause between manual and auto phases in seconds

logger = logging.getLogger("youtube_transcript")


# ============================================================
#  yt-dlp options
# ============================================================


def build_list_opts() -> dict:
    """Return yt-dlp options for metadata-only extraction (no download)."""
    return {"skip_download": True, "quiet": True, "no_warnings": True}


def build_download_opts(langs: list[str], output_dir: str, manual: bool, auto: bool) -> dict:
    """Return yt-dlp options configured for subtitle download.

    Args:
        langs: Language codes to request from yt-dlp.
        output_dir: Destination directory for downloaded files.
        manual: Whether to request manually uploaded subtitles.
        auto: Whether to request auto-generated captions.

    Returns:
        A yt-dlp options dict ready to pass to ``YoutubeDL``.
    """
    opts = build_list_opts()
    opts.update(
        {
            "writesubtitles": manual,
            "writeautomaticsub": auto,
            "subtitleslangs": langs,
            "subtitlesformat": SUB_FORMAT_PREF,
            "outtmpl": str(pathlib.Path(output_dir) / "%(id)s.%(ext)s"),
        }
    )
    return opts


# ============================================================
#  Language selection
# ============================================================


def fetch_info(url: str) -> dict:
    """Fetch video metadata from yt-dlp without downloading any media.

    Args:
        url: The YouTube video URL.

    Returns:
        Raw yt-dlp info dict containing subtitle tracks, video ID, etc.
    """
    with YoutubeDL(build_list_opts()) as ydl:
        return ydl.extract_info(url, download=False)


def collect_tracks(subs: dict | None) -> list[tuple[str, str]]:
    """Flatten a yt-dlp subtitle dict into a list of (code, name) pairs.

    Args:
        subs: The ``subtitles`` or ``automatic_captions`` dict from yt-dlp,
              mapping language codes to lists of format dicts.

    Returns:
        Ordered list of ``(code, display_name)`` tuples; empty when *subs* is None.
    """
    tracks = []
    for code, formats in (subs or {}).items():
        name = formats[0].get("name") if formats else None
        tracks.append((code, name or code))
    return tracks


def base_name(name: str) -> str:
    """Strip the parenthesised qualifier from a language name.

    Args:
        name: Full language name, e.g. ``'French (Original)'``.

    Returns:
        Name without parentheses, e.g. ``'French'``.
    """
    return name.split("(")[0].strip()


def is_accepted_name(name: str | None) -> bool:
    """Return True when the track name matches an accepted language or is '* (Original)'.

    Args:
        name: Display name of the subtitle track, or None.

    Returns:
        True if the track should be downloaded.
    """
    if not name:
        return False
    name = name.strip()
    return name.endswith(ORIGINAL_SUFFIX) or base_name(name) in ACCEPTED_NAMES


def lang3(code: str) -> str:
    """Convert a BCP-47 language code to a 3-letter code for EN/FR filtering.

    Args:
        code: BCP-47 code such as ``'fr'`` or ``'fr-FR'``.

    Returns:
        3-letter uppercase code (e.g. ``'FRA'``), or the first 3 uppercase chars
        of the base code when the mapping is unknown.
    """
    base = code.split("-")[0].lower()
    return LANG3.get(base, base.upper()[:3])


def manual_selection(info: dict) -> dict:
    """Return the accepted manual subtitle tracks as ``{code: name}``.

    Args:
        info: yt-dlp info dict returned by ``fetch_info``.

    Returns:
        Filtered dict of manually uploaded subtitle tracks.
    """
    tracks = dict(collect_tracks(info.get("subtitles")))
    return {c: n for c, n in tracks.items() if is_accepted_name(n)}


def auto_selection(info: dict) -> dict:
    """Return the accepted auto-generated subtitle tracks limited to EN and FR.

    Args:
        info: yt-dlp info dict returned by ``fetch_info``.

    Returns:
        Filtered dict of auto-generated caption tracks (EN/FR only).
    """
    tracks = dict(collect_tracks(info.get("automatic_captions")))
    return {c: n for c, n in tracks.items() if is_accepted_name(n) and lang3(c) in {"FRA", "ENG"}}


# ============================================================
#  File naming
# ============================================================


def kind_tag(name: str | None, source: str) -> str:
    """Derive the short origin tag for a subtitle track.

    Args:
        name: Display name of the track (may be None).
        source: Either ``'manual'`` or ``'auto'``.

    Returns:
        ``'orig'`` for Original tracks, ``'man'`` for manual, ``'auto'`` for auto-generated.
    """
    if (name or "").strip().endswith(ORIGINAL_SUFFIX):
        return "orig"
    return "man" if source == "manual" else "auto"


def file_stem(video_id: str, code: str, name: str, source: str) -> str:
    """Build the base filename stem ``'ID - language - KIND'``.

    Does not include variant, timestamp, or extension — those are appended by
    ``output_path``.

    Args:
        video_id: yt-dlp video ID.
        code: BCP-47 language code of the track.
        name: Display name of the track.
        source: Either ``'manual'`` or ``'auto'``.

    Returns:
        Stem string, e.g. ``'abc123 - French - manual'``.
    """
    language = base_name(name) or code
    kind = KIND_NAMES[kind_tag(name, source)]
    return f"{video_id} - {language} - {kind}"


def output_path(out_dir: str, stem: str, variant: str, stamp: str, ext: str) -> str:
    """Assemble the full output path ``'STEM - variant - TIMESTAMP.ext'``.

    Args:
        out_dir: Target directory.
        stem: Base filename stem from ``file_stem``.
        variant: One of ``CLEAN_LABEL``, ``RAW_LABEL``, or ``SOURCE_LABEL``.
        stamp: Timestamp string in ``STAMP_FORMAT``.
        ext: File extension without leading dot.

    Returns:
        Path string suitable for ``open()`` or ``Path.replace()``.
    """
    return str(pathlib.Path(out_dir) / f"{stem} - {variant} - {stamp}.{ext}")


# ============================================================
#  Download (with fixed-delay retries)
# ============================================================


def is_https_rate_limited(error: Exception) -> bool:
    """Return True when *error* signals an HTTP 429 Too Many Requests response.

    Args:
        error: Exception raised by yt-dlp during download.

    Returns:
        True if the error message contains '429' or 'too many requests'.
    """
    msg = str(error).lower()
    return "429" in msg or "too many requests" in msg


def find_subtitle_files(output_dir: str, video_id: str) -> list[str]:
    """Find all raw subtitle files matching ``<video_id>.<lang>.<ext>``.

    The dot after the ID prevents matching already-renamed output files.

    Args:
        output_dir: Directory to search.
        video_id: yt-dlp video ID used as the filename prefix.

    Returns:
        Sorted list of matching file paths as strings.
    """
    files: list[str] = []
    for ext in SUB_EXTS:
        files += [str(p) for p in pathlib.Path(output_dir).glob(f"{video_id}.*.{ext}")]
    return sorted(files)


def report_partial(error: Exception, files: list[str]) -> list[str]:
    """Log a non-retryable download failure and return whatever was already downloaded.

    Args:
        error: The exception that caused the failure.
        files: Files successfully downloaded before the failure.

    Returns:
        The *files* list unchanged, for use in the caller's conversion step.
    """
    if files:
        logger.warning("Erreur '%s' : poursuite avec %d fichier(s) déjà obtenu(s).", error, len(files))
    else:
        logger.error("Échec du téléchargement : %s", error)
    return files


def download_subtitles(
    url: str, langs: list[str], output_dir: str, video_id: str, manual: bool, auto: bool
) -> list[str]:
    """Download subtitles with tolerance for partial failures.

    A single-language failure does not discard already-downloaded tracks.
    On HTTP 429, the download is retried (yt-dlp skips already-present files).

    Args:
        url: YouTube video URL.
        langs: Language codes to request.
        output_dir: Destination directory.
        video_id: yt-dlp video ID for locating output files.
        manual: Whether to request manually uploaded subtitles.
        auto: Whether to request auto-generated captions.

    Returns:
        Sorted list of downloaded subtitle file paths.
    """
    opts = build_download_opts(langs, output_dir, manual, auto)
    max_loop = len(RETRY_DELAYS) + 1
    for attempt in range(max_loop):
        try:
            logger.debug("Tentative de téléchargement (essai %d/%d)...", attempt + 1, max_loop)
            with YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            return find_subtitle_files(output_dir, video_id)
        except DownloadError as exp:
            got = find_subtitle_files(output_dir, video_id)
            if is_https_rate_limited(exp) and attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    "HTTP 429 (essai %d/%d) : %d fichier(s) déjà téléchargé(s). Nouvelle tentative dans %ds.",
                    attempt + 1, max_loop, len(got), delay,
                )
                time.sleep(delay)
                continue
            return report_partial(exp, got)
        except Exception:  # final safety net for unexpected yt-dlp errors
            logger.exception("Erreur inattendue")
            return find_subtitle_files(output_dir, video_id)
    return find_subtitle_files(output_dir, video_id)


# ============================================================
#  Subtitle reading (JSON3 or VTT) -> lines
# ============================================================


def event_text(event: dict) -> str:
    """Extract the plain text from a single JSON3 subtitle event.

    Args:
        event: A JSON3 event dict containing a ``segs`` list.

    Returns:
        Concatenated UTF-8 text of all segments, stripped of whitespace.
    """
    segs = event.get("segs")
    if not segs:
        return ""
    return "".join(seg.get("utf8", "") for seg in segs).strip()


def load_json3_lines(path: str) -> list[str]:
    """Parse a JSON3 subtitle file into a list of raw text lines.

    Args:
        path: Path to the ``.json3`` file.

    Returns:
        List of non-empty text strings, one per subtitle event.
    """
    with pathlib.Path(path).open(encoding="utf-8") as f:
        events = json.load(f).get("events", [])
    return [event_text(e) for e in events]


def vtt_cue_lines(block: str) -> list[str]:
    """Extract visible text lines from a single VTT cue block.

    Strips timing lines, WEBVTT/NOTE headers, cue numbers, and inline tags.

    Args:
        block: Raw text of one VTT cue block (split on double newline).

    Returns:
        List of non-empty visible text lines from the cue.
    """
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
    """Parse a VTT subtitle file into a flat list of text lines.

    Args:
        path: Path to the ``.vtt`` file.

    Returns:
        Flat list of visible text lines across all cue blocks.
    """
    with pathlib.Path(path).open(encoding="utf-8") as f:
        content = f.read()
    lines = []
    for block in content.split("\n\n"):
        lines.extend(vtt_cue_lines(block))
    return lines


def load_lines(path: str) -> list[str]:
    """Dispatch to the correct parser based on the file extension.

    Args:
        path: Path to a ``.json3`` or ``.vtt`` subtitle file.

    Returns:
        Raw text lines as produced by the appropriate parser.
    """
    if path.endswith(".json3"):
        return load_json3_lines(path)
    return load_vtt_lines(path)


def dedup_lines(lines: list[str]) -> list[str]:
    """Remove karaoke-style overlaps by keeping only the most complete phrase.

    yt-dlp often emits overlapping segments where each new line extends the
    previous one. This function discards shorter prefixes and retains the
    longest form of each phrase.

    Args:
        lines: Raw subtitle lines, possibly with karaoke-style overlaps.

    Returns:
        Deduplicated list with prefix duplicates removed.
    """
    out, buffer = [], ""
    for text in lines:
        text = text.strip()
        if not text:
            continue
        if buffer and text.startswith(buffer):
            buffer = text  # longer (more complete) version
        elif buffer and buffer.startswith(text):
            continue  # older partial version, discard
        else:
            if buffer:
                out.append(buffer)
            buffer = text
    if buffer:
        out.append(buffer)
    return out


# ============================================================
#  Conversion & renaming
# ============================================================


def code_from_filename(path: str) -> str:
    """Infer the BCP-47 language code from a yt-dlp output filename.

    yt-dlp names files as ``<id>.<lang>.<ext>``; this function extracts
    the ``<lang>`` component.

    Args:
        path: Full path to the downloaded subtitle file.

    Returns:
        Language code string, or ``'unknown'`` when the pattern does not match.
    """
    base = pathlib.Path(path).name
    match = re.search(r"\.([A-Za-z0-9\-]+)\.(?:json3|vtt)$", base)
    return match.group(1) if match else "unknown"


def write_text(path: str, text: str) -> None:
    """Write *text* to *path* encoded as UTF-8.

    Args:
        path: Destination file path (created or overwritten).
        text: Content to write.
    """
    with pathlib.Path(path).open("w", encoding="utf-8") as f:
        f.write(text)


def save_transcript(path: str, video_id: str, names: dict, source: str, stamp: str) -> bool:
    """Convert a raw subtitle file into clean, raw, and source variants.

    Reads the file at *path*, deduplicates lines, writes the cleaned and raw
    text files, then renames the source file to the final stamped name.

    Args:
        path: Path to the raw downloaded subtitle file.
        video_id: yt-dlp video ID.
        names: Mapping of language code to display name for this phase.
        source: Either ``'manual'`` or ``'auto'``.
        stamp: Timestamp string used in all output filenames.

    Returns:
        True on success, False if the source file could not be read.
    """
    code = code_from_filename(path)
    name = names.get(code, code)
    stem = file_stem(video_id, code, name, source)
    out_dir = str(pathlib.Path(path).parent)
    try:
        lines = dedup_lines(load_lines(path))
    except (json.JSONDecodeError, OSError):
        logger.exception("Lecture impossible (%s)", pathlib.Path(path).name)
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
#  Display / orchestration
# ============================================================


def show_tracks(subs: dict | None) -> None:
    """Log available subtitle tracks, marking the ones that will be downloaded.

    Args:
        subs: The ``subtitles`` or ``automatic_captions`` dict from yt-dlp info.
    """
    tracks = collect_tracks(subs)
    if not tracks:
        logger.info("  (aucun)")
        return
    for code, name in sorted(tracks):
        mark = "x" if is_accepted_name(name) else " "
        logger.info("  [%s] %-8s %s", mark, code, name)


def process_phase(url: str, names: dict, source: str, video_id: str, stamp: str, output_dir: str) -> int:
    """Download and convert one subtitle phase ('manual' or 'auto').

    Args:
        url: YouTube video URL.
        names: Accepted tracks for this phase as ``{code: display_name}``.
        source: Either ``'manual'`` or ``'auto'``.
        video_id: yt-dlp video ID.
        stamp: Timestamp string appended to all output filenames.
        output_dir: Destination directory.

    Returns:
        Number of transcript files successfully written.
    """
    if not names:
        return 0
    label = "manuels" if source == "manual" else "auto-générés EN/FR"
    logger.info("Phase %s : %d langue(s) -> %s", label, len(names), ", ".join(names))
    is_manual = source == "manual"
    files = download_subtitles(url, list(names), output_dir, video_id, is_manual, not is_manual)
    return sum(save_transcript(p, video_id, names, source, stamp) for p in sorted(set(files)))


def download_youtube_srt(urlyoutube: str, output_dir: str) -> int:
    """Run phase 1 (manual) then phase 2 (auto EN/FR), with conversion and renaming.

    Args:
        urlyoutube: YouTube video URL.
        output_dir: Root directory for all output files (created if absent).

    Returns:
        Total number of transcript files written across both phases.
    """
    pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)
    logger.info("Dossier de sortie : %s", pathlib.Path(output_dir).resolve())
    logger.info("Récupération des métadonnées de la vidéo...")
    info = fetch_info(urlyoutube)
    video_id = info.get("id", "video")
    manual, auto = manual_selection(info), auto_selection(info)
    if not manual and not auto:
        logger.warning("Aucune piste FR/EN ni '* (Original)' disponible.")
        return 0
    stamp = datetime.now().strftime(STAMP_FORMAT)

    # do original
    total = process_phase(urlyoutube, manual, "manual", video_id, stamp, output_dir)

    # do autogen
    if auto:
        if manual:
            # pause before auto to reduce the risk of HTTP 429 after the manual phase
            logger.info("Pause de %ds avant les pistes auto-générées...", PAUSE_BETWEEN_PHASES)
            time.sleep(PAUSE_BETWEEN_PHASES)
        total += process_phase(urlyoutube, auto, "auto", video_id, stamp, output_dir)

    logger.info("Terminé : %d transcript(s) écrit(s).", total)
    return total


def print_and_debug_available_languages(url: str) -> None:
    """Log all available subtitle tracks for a video, grouped by type.

    Intended for development/debug use to inspect which subtitle tracks
    yt-dlp finds for a given URL.

    Args:
        url: YouTube video URL.
    """
    logger.info("Récupération des langues disponibles...")
    info = fetch_info(url)
    logger.info("== Sous-titres manuels ==")
    show_tracks(info.get("subtitles"))
    logger.info("== Sous-titres auto-générés ==")
    show_tracks(info.get("automatic_captions"))


# EOF
