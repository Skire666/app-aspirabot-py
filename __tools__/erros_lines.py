import tkinter as tk


class ValidatedField(tk.Frame):
    """Champ Entry avec :
      - validation en temps réel (à chaque frappe)
      - cadre rouge sur l'Entry en cas d'erreur
      - message d'erreur inline à droite

    Paramètres :
        parent    – widget parent
        label     – texte du label affiché à gauche
        validator – fonction(value: str) -> str | None
                    Retourne un message d'erreur, ou None si valide.
        **kwargs  – options passées à l'Entry (width, etc.)
    """

    COLOR_ERR = "#e53935"  # rouge
    COLOR_OK = "#cccccc"  # gris neutre (bordure normale)
    COLOR_IDLE = "#cccccc"

    def __init__(self, parent, label="", validator=None, **kwargs):
        super().__init__(parent)
        self._validator = validator

        # ── Label descriptif ──────────────────────────────────────────
        tk.Label(self, text=label, width=15, anchor="w").pack(side="left")

        # ── Cadre simulant la bordure colorée de l'Entry ──────────────
        # Tkinter ne permet pas de changer la couleur de bordure d'un Entry
        # directement ; on l'enveloppe dans un Frame coloré.
        self._border = tk.Frame(self, bg=self.COLOR_IDLE, padx=2, pady=2)
        self._border.pack(side="left", padx=(0, 6))

        self._var = tk.StringVar()
        self._entry = tk.Entry(
            self._border,
            textvariable=self._var,
            relief="flat",  # retire la bordure native de l'Entry
            highlightthickness=0,
            **kwargs,
        )
        self._entry.pack()

        # ── Label d'erreur inline ─────────────────────────────────────
        self._error_label = tk.Label(self, text="", fg=self.COLOR_ERR, anchor="w", width=22)
        self._error_label.pack(side="left")

        # ── Validation en temps réel ──────────────────────────────────
        self._var.trace_add("write", lambda *_: self.validate())

    # ─────────────────────────────────────────────────────────────────
    def validate(self) -> bool:
        """Valide le champ, met à jour le style et le message. Retourne True si valide."""
        if self._validator is None:
            return True

        msg = self._validator(self._var.get())
        is_valid = msg is None

        # Couleur de cadre
        self._border.config(bg=self.COLOR_OK if is_valid else self.COLOR_ERR)
        # Message
        self._error_label.config(text="" if is_valid else f"⚠ {msg}")
        return is_valid

    def get(self) -> str:
        return self._var.get()

    def set_error(self, msg: str):
        """Force un message d'erreur depuis l'extérieur."""
        self._border.config(bg=self.COLOR_ERR)
        self._error_label.config(text=f"⚠ {msg}")

    def clear_error(self):
        self._border.config(bg=self.COLOR_IDLE)
        self._error_label.config(text="")


# ── Validateurs ────────────────────────────────────────────────────────


def not_empty(v):
    return None if v.strip() else "Champ requis"


def is_email(v):
    return None if ("@" in v and "." in v.split("@")[-1]) else "Email invalide"


def is_positive_int(v):
    if not v:
        return "Champ requis"
    return None if (v.isdigit() and int(v) > 0) else "Entier positif attendu"


# ── Application exemple ────────────────────────────────────────────────

root = tk.Tk()
root.title("Validation inline – temps réel")
root.resizable(False, False)

frame = tk.Frame(root, padx=24, pady=20)
frame.pack()

fields = [
    ValidatedField(frame, label="Nom", validator=not_empty, width=22),
    ValidatedField(frame, label="Email", validator=is_email, width=22),
    ValidatedField(frame, label="Âge", validator=is_positive_int, width=22),
]

for f in fields:
    f.pack(pady=5, anchor="w")


def on_submit():
    count = 0
    for f in fields:
        if f.validate():
            count += 1
    print("Formulaire soumis. Valide :", count)
    status.config(
        text="✅ Formulaire valide !" if count == len(fields) else "❌ Corrigez les erreurs.",
        fg="#2e7d32" if count == len(fields) else COLOR_ERR,
    )


COLOR_ERR = "#e53935"

tk.Button(frame, text="Valider", command=on_submit).pack(pady=(14, 0))
status = tk.Label(frame, text="")
status.pack()

root.mainloop()
