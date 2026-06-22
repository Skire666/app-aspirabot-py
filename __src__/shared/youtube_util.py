import re
from urllib.parse import parse_qs, urlparse


def sanitize_youtube_url(url: str) -> str:
    """Clean a YouTube URL by extracting the video ID and reformatting it.

    This function looks for the 'v' parameter in the query string and constructs a
    standardized YouTube URL. If the 'v' parameter is not found, it returns the original URL.

    # https://www.youtube.com/?v=cmXyYWC1FZc&pp=sdfsdf -> https://www.youtube.com/watch?v=cmXyYWC1FZc
    # https://www.youtube.com/watch?v=aaaaGEU&pp=ugUEEgJmcg%3D%3D -> https://www.youtube.com/watch?v=aaaaGEU
    # https://www.youtube.com/shorts/cmXyYWC1FZc&pp=sdfsdf -> https://www.youtube.com/watch?v=cmXyYWC1FZc
    """
    match = re.search(r"[?&]v=([a-zA-Z0-9_-]+)", url)
    if not match:
        match = re.search(r"shorts/([a-zA-Z0-9_-]+)", url)

    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return ""  # pas de paramètre v, on retourne l'URL telle quelle


def get_id_video_youtube(url: str) -> str:
    # https://www.youtube.en/?v=1111YWC1FZc
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

    raise ValueError("undefine id vide youtube")
