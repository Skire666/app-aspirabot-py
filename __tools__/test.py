"""Visionneuse CSV avec colonne de tags.
Python 3.13 - tksheet (pip install "tksheet>=7")

- Chargement d'un CSV (séparateur détecté, BOM géré)
- Tri par clic sur l'en-tête de colonne
- Ajout d'une colonne "tags"
- Clic sur une cellule "tags" -> choix de tags existants / création de nouveaux
- Bouton d'enregistrement
- Optimisé pour de gros fichiers (tksheet ne dessine que les cellules visibles)
"""

import csv
import os
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tksheet import Sheet


# --------------------------------------------------------------------------- #
#  Boîte de dialogue de sélection / création de tags
# --------------------------------------------------------------------------- #
class TagDialog(tk.Toplevel):
    def __init__(self, parent, all_tags, current_tags):
        super().__init__(parent)
        self.title("Choisir des tags")
        self.result = None
        self.transient(parent)
        self.grab_set()  # modale
        self.geometry("360x440")

        self._tags = list(all_tags)  # tags proposés (ordre d'affichage)

        ttk.Label(self, text="Tags existants (sélection multiple) :").pack(anchor="w", padx=10, pady=(10, 2))

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10)
        self.listbox = tk.Listbox(frame, selectmode="multiple", activestyle="none", exportselection=False)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for t in self._tags:
            self.listbox.insert("end", t)

        # présélection des tags déjà présents dans la cellule
        cur = set(current_tags)
        for i, t in enumerate(self._tags):
            if t in cur:
                self.listbox.selection_set(i)
        # tags de la cellule qui ne sont pas encore connus -> on les ajoute
        for t in current_tags:
            if t not in self._tags:
                self.listbox.insert("end", t)
                self._tags.append(t)
                self.listbox.selection_set("end")

        add = ttk.Frame(self)
        add.pack(fill="x", padx=10, pady=8)
        ttk.Label(add, text="Nouveau(x) tag(s) — séparés par des virgules :").pack(anchor="w")
        row = ttk.Frame(add)
        row.pack(fill="x", pady=2)
        self.entry = ttk.Entry(row)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self._add_new())
        ttk.Button(row, text="Ajouter", command=self._add_new).pack(side="left", padx=(6, 0))

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=(4, 10))
        ttk.Button(btns, text="Valider", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Annuler", command=self._cancel).pack(side="right", padx=(0, 6))

        self.entry.focus_set()
        self.bind("<Escape>", lambda e: self._cancel())

    def _add_new(self):
        for name in (p.strip() for p in self.entry.get().split(",")):
            if not name:
                continue
            if name not in self._tags:
                self.listbox.insert("end", name)
                self._tags.append(name)
            self.listbox.selection_set(self._tags.index(name))
        self.entry.delete(0, "end")

    def _ok(self):
        self.result = [self._tags[i] for i in self.listbox.curselection()]
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# --------------------------------------------------------------------------- #
#  Application principale
# --------------------------------------------------------------------------- #
class CsvTagViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Visionneuse CSV + tags")
        self.geometry("1100x650")

        # État
        self.headers = []  # noms de colonnes (sans les flèches de tri)
        self.data = []  # liste de listes = source de vérité
        self.delimiter = ";"
        self.tags_col = None  # index de la colonne des tags (None si absente)
        self.all_tags = set()  # tags connus
        self.dirty = False
        self._sort_col = None
        self._sort_desc = False

        self._build_toolbar()
        self._build_sheet()

    # ----------------------------------------------------------------- UI --- #
    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=5)
        bar.pack(fill="x")

        ttk.Button(bar, text="Ouvrir…", command=self.open_csv).pack(side="left")
        self.add_col_btn = ttk.Button(bar, text="➕ Colonne de tags", command=self.add_tags_column, state="disabled")
        self.add_col_btn.pack(side="left", padx=6)
        self.save_btn = ttk.Button(bar, text="💾 Enregistrer…", command=self.save_csv, state="disabled")
        self.save_btn.pack(side="left")

        self.info = ttk.Label(bar, text="Aucun fichier chargé")
        self.info.pack(side="left", padx=12)

    def _build_sheet(self):
        self.sheet = Sheet(self, headers=[], data=[], show_row_index=True)
        self.sheet.pack(fill="both", expand=True)

        # Lecture seule sur le corps : pas de "edit_cell".
        self.sheet.enable_bindings(
            "single_select",
            "row_select",
            "column_select",
            "drag_select",
            "column_width_resize",
            "double_click_column_resize",
            "row_height_resize",
            "arrowkeys",
            "copy",
            "ctrl_select",
        )
        # Clic cellule -> éventuel éditeur de tags ; clic en-tête -> tri.
        self.sheet.extra_bindings([("cell_select", self.on_cell_select), ("column_select", self.on_column_select)])

    # ------------------------------------------------------------ Chargement - #
    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Choisir un fichier CSV", filetypes=[("Fichiers CSV", "*.csv"), ("Tous", "*.*")]
        )
        if path:
            self.load_csv(path)

    def load_csv(self, path):
        try:
            with pathlib.Path(path).open(newline="", encoding="utf-8-sig") as f:
                sample = f.read(8192)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
                    self.delimiter = dialect.delimiter
                except csv.Error:
                    dialect = csv.excel
                    dialect.delimiter = self.delimiter = ";"
                rows = list(csv.reader(f, dialect))
        except (OSError, UnicodeDecodeError) as e:
            messagebox.showerror("Erreur de lecture", str(e))
            return

        if not rows:
            messagebox.showwarning("Fichier vide", "Rien à afficher.")
            return

        self.headers = rows[0]
        n = len(self.headers)
        # normalise chaque ligne à la longueur de l'en-tête
        self.data = [(r + [""] * (n - len(r)))[:n] if len(r) != n else r for r in rows[1:]]

        # réinitialise l'état de tri / tags
        self._sort_col = self._sort_desc = None, False
        self._sort_col = None
        self.all_tags.clear()
        self.dirty = False

        # colonne "tags" déjà présente dans le fichier ?
        self.tags_col = self.headers.index("tags") if "tags" in self.headers else None
        if self.tags_col is not None:
            self._collect_tags()
            self.add_col_btn.config(state="disabled")
        else:
            self.add_col_btn.config(state="normal")

        self.sheet.set_sheet_data(self.data, reset_col_positions=True, reset_row_positions=True, redraw=True)
        self._render_headers()
        self.save_btn.config(state="normal")
        self._update_info(os.path.basename(path))

    def _collect_tags(self):
        c = self.tags_col
        for row in self.data:
            for t in row[c].split(","):
                t = t.strip()
                if t:
                    self.all_tags.add(t)

    # -------------------------------------------------------- Colonne tags --- #
    def add_tags_column(self):
        if self.tags_col is not None or not self.data:
            return
        self.headers.insert(0, "tags")  # ajoutée en tête pour la visibilité
        for row in self.data:
            row.insert(0, "")
        self.tags_col = 0
        if self._sort_col is not None:
            self._sort_col += 1
        self.sheet.set_sheet_data(self.data, reset_col_positions=True, reset_row_positions=False, redraw=True)
        self._render_headers()
        self.add_col_btn.config(state="disabled")
        self._mark_dirty()

    # ------------------------------------------------------------- Événements #
    def on_cell_select(self, event):
        sel = getattr(event, "selected", None)
        if sel is None or getattr(sel, "type_", "cells") != "cells":
            return  # ignore les sélections de colonne/ligne
        if self.tags_col is not None and sel.column == self.tags_col:
            self._edit_tags(sel.row)  # sel.row == index de données (voir note)

    def on_column_select(self, event):
        sel = getattr(event, "selected", None)
        if sel is not None and sel.column is not None:
            self.sort_by_column(int(sel.column))

    def _edit_tags(self, row):
        current = [t.strip() for t in self.data[row][self.tags_col].split(",") if t.strip()]
        dlg = TagDialog(self, sorted(self.all_tags), current)
        self.wait_window(dlg)
        if dlg.result is not None:
            value = ", ".join(dlg.result)
            self.data[row][self.tags_col] = value
            self.sheet.set_cell_data(row, self.tags_col, value, redraw=True)
            self.all_tags.update(dlg.result)
            self._mark_dirty()

    # ----------------------------------------------------------------- Tri --- #
    def sort_by_column(self, col):
        if not self.data:
            return
        self._sort_desc = not self._sort_desc if col == self._sort_col else False
        self._sort_col = col
        self.data.sort(key=lambda r: self._sort_key(r[col] if col < len(r) else ""), reverse=self._sort_desc)
        # On réordonne physiquement les données : index affiché == index de données.
        self.sheet.set_sheet_data(self.data, reset_col_positions=False, reset_row_positions=False, redraw=True)
        self._render_headers()

    @staticmethod
    def _sort_key(v):
        s = (v or "").strip()
        if not s:
            return (2, "")  # vides en dernier
        try:
            return (0, float(s.replace(",", ".")))
        except ValueError:
            return (1, s.lower())

    # -------------------------------------------------------------- En-têtes - #
    def _render_headers(self):
        arrow = " ▼" if self._sort_desc else " ▲"
        self.sheet.headers([h + (arrow if i == self._sort_col else "") for i, h in enumerate(self.headers)])

    # ------------------------------------------------------- Enregistrement -- #
    def save_csv(self):
        if not self.data:
            return
        path = filedialog.asksaveasfilename(
            title="Enregistrer sous",
            defaultextension=".csv",
            initialfile="export_tags.csv",
            filetypes=[("Fichiers CSV", "*.csv")],
        )
        if not path:
            return
        try:
            with pathlib.Path(path).open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=self.delimiter)
                w.writerow(self.headers)
                w.writerows(self.data)
        except OSError as e:
            messagebox.showerror("Erreur d'écriture", str(e))
            return
        self.dirty = False
        self.title(self.title().rstrip(" *"))
        messagebox.showinfo("Enregistré", f"Fichier écrit :\n{path}")

    # ------------------------------------------------------------- Divers ---- #
    def _mark_dirty(self):
        self.dirty = True
        if not self.title().endswith("*"):
            self.title(self.title() + " *")

    def _update_info(self, filename):
        cols = len(self.headers)
        self.info.config(text=f"{len(self.data)} lignes × {cols} colonnes — {filename}")


if __name__ == "__main__":
    CsvTagViewer().mainloop()
