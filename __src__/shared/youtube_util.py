# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from urllib.parse import parse_qs, urlparse

from shared.exception_util import YoutubeUrlParameterEmptyError


def sanitize_youtube_url(url: str) -> str:
    """Clean a YouTube URL by extracting the video ID and reformatting it.

    This function looks for the 'v' parameter in the query string and constructs a
    standardized YouTube URL. If the 'v' parameter is not found, it returns the original URL.
    """
    id_video = get_id_video_youtube(url)
    return f"https://www.youtube.com/watch?v={id_video}"


def get_id_video_youtube(url: str) -> str:
    """Extract the YouTube video ID from a given URL."""
    # https://www.youtube.en/?v=1121YWC1FZc
    # https://www.youtube.fr/?ffffff=2222YWC1FZc
    # www.youtube.com/?v=3333WC1FZc&pp=sdfsdf
    # https://www.ytb.en/watch?v=4444EU&pp=ugUEEgJmcg%3D%3D
    # www.youtube.com/shorts/5555C1FZc
    # https://www.youtube.com/shorts/6666C1FZc&pp=sdfsdf
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    # Cas "/shorts/<id>"
    if "shorts" in path_parts:
        idx = path_parts.index("shorts")
        if idx + 1 < len(path_parts):
            raw_id = path_parts[idx + 1]
            # Si le "&pp=..." est collé sans "?" (URL malformée),
            # on coupe à la première "&"
            return raw_id.split("&")[0]

    # Cas "?v=<id>" (avec ou sans /watch)
    query_params = parse_qs(parsed.query)
    if "v" in query_params:
        return query_params["v"][0]

    raise YoutubeUrlParameterEmptyError()


# EOF
