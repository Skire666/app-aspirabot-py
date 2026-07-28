# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import base64
import hashlib
from pathlib import Path

from shared.exception_util import InvalidDataUriFormatError


def export_base64_image(prefix: str, url_ok: str, data_uri: str, output_dir: str | Path = ".") -> str:
    """Décode une image base64 et l'enregistre sur disque.

    Args:
        prefix:        préfixe pour le nom du fichier.
        url_ok:        URL valide de l'image (sert à calculer le SHA-256).
        data_uri:      chaîne au format ``data:<mime>;base64,<données>``.
        output_dir:  répertoire de destination (créé si besoin).

    Returns:
        Le hash MD5 hexadécimal de l'URL source.

    Raises:
        InvalidDataUriFormatError: Si data_uri ne contient pas de séparateur ",".
    """
    # --- 1. Hash de l'URL source -----------------------------------------
    hash32char = hashlib.md5(url_ok.encode(), usedforsecurity=False).hexdigest()

    # --- 2. Séparer l'en-tête du payload --------------------------------
    header, _, raw_b64 = data_uri.partition(",")
    if not raw_b64:
        raise InvalidDataUriFormatError()

    mime = header.split(":")[1].split(";")[0]  # "image/png"
    ext = mime.split("/")[1]  # "png"
    if ext == "jpeg":
        ext = "jpg"

    # --- 3. Décoder et écrire --------------------------------------------
    image_bytes = base64.b64decode(raw_b64)

    output_path = Path(output_dir) / "export_img"
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / f"{prefix.replace('.', '_')}_{hash32char}.{ext}"
    filepath.write_bytes(image_bytes)

    return str("./export_img/" + filepath.name)


# EOF
