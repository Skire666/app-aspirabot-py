import tkinter as tk
from tkinter import messagebox

from tksheet import Sheet

# ── Configuration ────────────────────────────────────────────────────────────
HEADERS = ["Nom", "Âge", "Ville", ""]  # "" = colonne action
DEL_COL = 3  # index de la colonne "Supprimer"
DEL_LABEL = "🗑"

# ── Données ──────────────────────────────────────────────────────────────────
data = [
    ["Alice", "30", "Paris", DEL_LABEL],
    ["Bob", "25", "Lyon", DEL_LABEL],
    ["Charlie", "35", "Marseille", DEL_LABEL],
]

# ── Fenêtre ──────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Tableau tksheet")
root.geometry("680x420")

# ── Toolbar ──────────────────────────────────────────────────────────────────
toolbar = tk.Frame(root, pady=6, padx=6)
toolbar.pack(fill="x")


def clear_all():
    if messagebox.askyesno("Effacer", "Effacer toutes les lignes ?"):
        sheet.set_sheet_data([])


tk.Button(
    toolbar, text="🗑 Effacer la liste", fg="white", bg="#e74c3c", relief="flat", padx=10, pady=4, command=clear_all
).pack(side="left")

# ── Sheet ─────────────────────────────────────────────────────────────────────
frame = tk.Frame(root)
frame.pack(fill="both", expand=True, padx=6, pady=4)

sheet = Sheet(
    frame, headers=HEADERS[:], data=[row[:] for row in data], row_height=30, header_height=32, column_width=160
)
sheet.pack(fill="both", expand=True)

# Activer les bindings utiles (édition, navigation, copier/coller…)
sheet.enable_bindings(
    "single_select",
    "drag_select",
    "column_select",
    "row_select",
    "column_width_resize",
    "double_click_column_resize",
    "right_click_popup_menu",
    "rc_select",
    "copy",
    "cut",
    "paste",
    "delete",
    "undo",
    "redo",
    "edit_cell",
    "edit_header",  # double-clic en-tête pour renommer
)

# Colonne "🗑" : lecture seule + centrée + étroite
sheet.column_width(column=DEL_COL, width=55)
sheet.readonly_columns(columns=[DEL_COL])  # on ne peut pas l'éditer


# Forcer le label 🗑 sur toutes les lignes existantes
def set_del_labels():
    for r in range(sheet.get_total_rows()):
        sheet.set_cell_data(r, DEL_COL, DEL_LABEL)


set_del_labels()


# ── Clic sur la colonne "Supprimer" ─────────────────────────────────────────
def on_cell_click(event):
    # Récupère la cellule sélectionnée après le clic
    root.after(50, check_selected_cell)


def check_selected_cell():
    sel = sheet.get_currently_selected()
    if not sel:
        return
    # sel est un objet avec .row et .column
    try:
        r, c = sel.row, sel.column
    except AttributeError:
        # anciennes versions : sel est un tuple (row, col)
        r, c = sel[0], sel[1]
    if c == DEL_COL:
        delete_row(r)


sheet.bind("<Button-1>", on_cell_click)


def delete_row(idx):
    if messagebox.askyesno("Supprimer", f"Supprimer la ligne {idx + 1} ?"):
        sheet.delete_rows(rows=[idx])


# ── Bouton "+" ────────────────────────────────────────────────────────────────
bottom = tk.Frame(root, pady=6, padx=6)
bottom.pack(fill="x")


def add_row():
    new_row = ["", "", "", DEL_LABEL]
    sheet.insert_row(values=new_row, idx="end")
    last = sheet.get_total_rows() - 1
    sheet.set_cell_data(last, DEL_COL, DEL_LABEL)
    sheet.see(last, 0)
    sheet.set_currently_selected(last, 0)


tk.Button(
    bottom, text="＋ Ajouter une ligne", bg="#2980b9", fg="white", relief="flat", padx=10, pady=4, command=add_row
).pack(side="left")

root.mainloop()
