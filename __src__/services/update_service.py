# Service pour la mise à jour (Update)
import re
import os
from pathlib import Path
from typing import Callable

def sanitize_name(name: str) -> str:
    # Retire un éventuel .json à la fin
    has_ext = name.lower().endswith(".json")
    if has_ext:
        name = name[:-5]
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip()).lower()
    safe_name = safe_name if safe_name else "fournisseur"
    return f"{safe_name}.json" if has_ext else safe_name

class UpdateService:
    """Service encapsulant le domaine de mise à jour des fournisseurs."""
    
    def generate_filename(self, name: str, date: str) -> str:
        """Génère le nom de fichier basé sur le nom et la date."""
        raw = f"{name}_{date}"
        # Remplace les espaces par _
        raw = raw.replace(" ", "_").replace("-", "").replace(":", "")
        # Retire les caractères spéciaux (garde uniquement alphanumérique et _)
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', raw).lower()
        if not safe_name:
            safe_name = "nouveau_fournisseur"
        # Ajoute l'extension .json
        return f"{safe_name}.json"

    def process_rename(self, old_stem: str, new_name: str, get_next_available_path_func: Callable[[str], Path], provider_file_path: str) -> tuple[str, str]:
        """
        Gère la logique de renommage d'un fournisseur.
        Retourne le nouveau stem et le nouveau chemin du fichier.
        """
        safe_name = sanitize_name(new_name)
        new_stem = safe_name
        
        if new_stem != old_stem:
            new_file_path = get_next_available_path_func(new_stem)
            os.rename(provider_file_path, new_file_path)
            return new_file_path.stem, str(new_file_path)
            
        return old_stem, provider_file_path
