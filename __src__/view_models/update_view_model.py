import tkinter as tk
from dataclasses import dataclass, field
from typing import Any

@dataclass
class UpdateViewModel:
    provider_filename: tk.StringVar = field(default_factory=tk.StringVar)
    provider_title: tk.StringVar = field(default_factory=tk.StringVar)
    url: tk.StringVar = field(default_factory=tk.StringVar)
    created_date: tk.StringVar = field(default_factory=tk.StringVar)
    modified_date: tk.StringVar = field(default_factory=tk.StringVar)
    version: tk.StringVar = field(default_factory=tk.StringVar)
    browser_displayed: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    automation_obfuscated: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    steps: list[dict[str, Any]] = field(default_factory=list) # type: ignore[reportUnknownVariableType]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.provider_title.get() or not self.provider_title.get().strip():
            errors.append("Le champ 'Nom' est obligatoire.")
        if not self.provider_filename.get() or not self.provider_filename.get().strip():
            errors.append("Le champ 'Nom de fichier' est obligatoire.")
        if not self.url.get() or not self.url.get().strip():
            errors.append("Le champ 'URL' est obligatoire.")
            
        for idx, step in enumerate(self.steps):
            t = step.get("type")
            if t in ["FIND_ELEMENT", "CLICK", "EXTRACT_TEXT"]:
                if not step.get("selector"):
                    errors.append(f"Étape {idx + 1} ({t}) : le sélecteur est requis.")
            elif t == "WAIT":
                if not step.get("timeout") and not step.get("selector"):
                    errors.append(f"Étape {idx + 1} ({t}) : timeout ou sélecteur est requis.")
        return errors
