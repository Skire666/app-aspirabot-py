"""Repository for YouTube I/O: yt-dlp network calls and local file operations."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Final, cast

import yt_dlp
from models.youtube_infos_video_model import YoutubeInfosVideoModel
from models.Youtube_subtitles_list_model import YoutubeSubtitleModel, YoutubeSubtitlesListModel
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.enums.youtube_subtitle_enum import SubtitleOriginEnum
from shared.exception_util import RepositoryWriteError

# ============================================================================
# INTERNAL CONSTANTS
# ============================================================================

_SUBTITLE_FORMATS: Final[str] = "srt/vtt/json3/best"
_NA_TOKEN: Final[str] = "<<_#N/A_>>"

# ============================================================================
# CLASS
# ============================================================================

cached_video_info: dict[str, YoutubeSubtitlesListModel] = {}


class YoutubeRepository:
    """Sole owner of all YouTube-related I/O: yt-dlp network calls and local files.

    All methods raise :class:`RepositoryWriteError` on local filesystem failures.
    yt-dlp ``DownloadError`` is propagated as-is so callers can inspect the message
    (age restriction, video unavailable, rate limit …) and react accordingly.
    """

    def __init__(self) -> None:
        """Initialise the repository logger."""
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # yt-dlp network calls
    # ------------------------------------------------------------------

    @staticmethod
    def update_cached_subtitles(url: str, info: YoutubeInfosVideoModel) -> None:
        """Update the cached video info."""
        global cached_video_info
        cached_video_info[url] = info.subtitles_ls

    def fetch_cached_subtitles(self, url: str) -> YoutubeSubtitlesListModel | None:
        """Fetch cached subtitle info for a given URL."""
        global cached_video_info
        if url not in cached_video_info:
            obj = self.fetch_video_info(url)
            casted = YoutubeInfosVideoModel(obj)
            self.update_cached_subtitles(url, casted)
        return cached_video_info.get(url)

    @staticmethod
    def fetch_video_info(url: str) -> dict[str, Any]:
        """Fetch raw video metadata via yt-dlp without downloading any media.

        Args:
            url: The YouTube video URL to query.

        Returns:
            The raw info dict returned by yt-dlp.

        Raises:
            DownloadError: Propagated from yt-dlp on network or YouTube errors
                (includes age-restriction, video-unavailable, rate-limiting …).
            RuntimeError: On unexpected yt-dlp failures.
        """
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": False,  # list manual
            "writeautomaticsub": False,  # list auto
            "socket_timeout": 30,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            raw = ydl.extract_info(url, download=False)
        return cast(dict[str, Any], raw)

    @staticmethod
    def execute_subtitle_download(
        url_youtube: str, id_video: str, out_dir: Path, srt: YoutubeSubtitleModel
    ) -> None:
        """Invoke yt-dlp to download a specific set of subtitle tracks to disk.

        Args:
            url_youtube: The YouTube video URL.
            id_video: The YouTube video identifier used for naming output files.
            out_dir: Directory where subtitle files are written.
            srt: Subtitle track metadata (auto vs. manual, language, quality).

        Raises:
            DownloadError: Propagated from yt-dlp on download failures.
        """
        ts_date = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        is_automatic = srt.origin is SubtitleOriginEnum.E_AUTO

        # name
        template = str(
            out_dir / f"{id_video} - Q{srt.quality} - {srt.origin.value} - {srt.language.value} - {ts_date}.%(ext)s"
        )

        # payload
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": not is_automatic,
            "writeautomaticsub": is_automatic,
            "subtitleslangs": [srt.code],
            "subtitlesformat": _SUBTITLE_FORMATS,
            "outtmpl": template,
            "overwrites": False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            ydl.download([url_youtube])

    # ------------------------------------------------------------------
    # Local filesystem operations
    # ------------------------------------------------------------------

    def prepare_output_dir(self, output_dir: str) -> Path:
        """Create the output directory (parents included) and return its Path.

        Args:
            output_dir: Path string for the directory to create.

        Returns:
            The resolved :class:`Path` for the created directory.

        Raises:
            RepositoryWriteError: If the directory cannot be created.
        """
        path = Path(output_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RepositoryWriteError() from exc
        self._logger.debug("Répertoire de sortie prêt : %s", path)
        return path

    def save_basic_data_json(self, info: YoutubeInfosVideoModel, target: Path) -> None:
        """Serialize *info* as indented JSON and write it to *target*.

        Args:
            info: The video model whose ``to_dict()`` payload is serialized.
            target: Destination file path (parent directory must exist).

        Raises:
            RepositoryWriteError: If the file cannot be written.
        """
        try:
            target.write_text(json.dumps(info.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        except OSError as exc:
            raise RepositoryWriteError() from exc
        self._logger.debug("Données basiques enregistrées : %s", target.name)

    def rename_subtitle_file(self, src: Path, dest: Path) -> None:
        """Rename *src* to *dest* on the local filesystem.

        Args:
            src: Existing subtitle file to rename.
            dest: Target path after the rename.

        Raises:
            RepositoryWriteError: If the rename fails.
        """
        try:
            src.rename(dest)
        except OSError as exc:
            raise RepositoryWriteError() from exc
        self._logger.debug("Fichier renommé : %s -> %s", src.name, dest.name)

    def write_placeholder_file_when_error(self, target: Path) -> None:
        """Write the N/A placeholder token to *target*.

        Args:
            target: Destination file path for the placeholder.

        Raises:
            RepositoryWriteError: If the file cannot be written.
        """
        try:
            target.write_text(_NA_TOKEN, encoding="utf-8")
        except OSError as exc:
            raise RepositoryWriteError() from exc
        self._logger.debug("Placeholder N/A créé : %s", target.name)


# EOF
