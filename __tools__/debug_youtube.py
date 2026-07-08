import yt_dlp

# https://www.youtube.com/watch?v=oEjZUfpZ8dA # chinois et ANG
# https://www.youtube.com/watch?v=Szoeo4HBJ4c # c dans l'air (FRA 1 seul)
# https://www.youtube.com/watch?v=huAwz_BR8WM # two minutes papier please
# https://www.youtube.com/watch?v=YQHsXMglC9A # adele music (ENG)
# https://www.youtube.com/watch?v=5XPlYxjKQ6k # james bond (audio ANG)
# https://www.youtube.com/watch?v=JgHXD8211T4 # warcraft 5h (FRA)
# https://www.youtube.com/watch?v=xXMUpqSyJJo # back music allemand
# https://www.youtube.com/watch?v=aSOSYAk-o9Y # trump quebec (2 FRA)

url = "https://www.youtube.com/watch?v=ljeKLuu3pYY"

ydl_opts = {"skip_download": True, "quiet": False, "verbose": True}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)

    # Sous-titres manuels (uploadés par le créateur)
    subtitles = info.get("subtitles", {})
    # Sous-titres auto-générés
    auto_captions = info.get("automatic_captions", {})

    print(f"URL: {url}")
    all_keys = info.keys()
    print("=== Clés disponibles dans les infos extraites ===")
    for key in sorted(all_keys):
        value = str(info[key])
        if len(value) > 80:
            value = value[:77] + "..."
        print(key + ": " + value)

    print("=== Sous-titres manuels ===")
    for lang, formats in subtitles.items():
        exts = [f.get("ext") for f in formats]
        print(f"{lang}: {exts}")

    print("\n=== Sous-titres auto-générés ===")
    for lang, formats in auto_captions.items():
        exts = [f.get("ext") for f in formats]
        print(f"{lang}: {exts}")
