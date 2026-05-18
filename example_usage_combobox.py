"""Example usage of ColumnCombobox with 100 Produit objects."""

import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).parent / "__src__"))

from views.components.column_combobox import ColumnCombobox


@dataclass
class Produit:
    id: int
    nom: str
    categorie: str
    prix: float


def main() -> None:
    root = tk.Tk()
    root.title("ColumnCombobox — exemple Produit")
    root.geometry("700x300")

    tk.Label(root, text="Sélectionner un produit :", anchor="w").pack(
        fill="x", padx=10, pady=(10, 2)
    )

    ccb = ColumnCombobox(root, width=60)
    ccb.pack(fill="x", padx=10, pady=(0, 10))

    ccb.add_column("id",        lambda p: p.id,               width=6,  visible=False)
    ccb.add_column("nom",       lambda p: p.nom,              width=25, visible=True)
    ccb.add_column("categorie", lambda p: p.categorie,         width=15, visible=True)
    ccb.add_column("prix",      lambda p: f"{p.prix:.2f} €",  width=10, visible=True)

    produits = [Produit(i, f"Produit {i}", f"Cat {'ABC'[i % 3]}", i * 1.5) for i in range(100)]
    ccb.add_items(produits)

    info_var = tk.StringVar(value="Aucun élément sélectionné…")
    tk.Label(root, textvariable=info_var, anchor="w", relief="sunken", pady=4).pack(
        fill="x", padx=10, pady=(0, 6)
    )

    def on_select(event: tk.Event) -> None:
        obj = ccb.get_selected_object()
        row = ccb.get_selected_row()
        if obj is None or row is None:
            return
        prix_val = ccb.get_selected_value("prix")
        info_var.set(f"Objet: {obj}  |  ID caché: {row['id']}  |  Prix: {prix_val}")

    ccb.bind("<<ComboboxSelected>>", on_select)

    controls = tk.Frame(root)
    controls.pack(fill="x", padx=10, pady=(0, 10))

    def toggle_categorie() -> None:
        current = ccb.get_column_visible("categorie")
        ccb.set_column_visible("categorie", not current)
        label = "Masquer catégorie" if not current else "Afficher catégorie"
        btn_toggle.configure(text=label)

    btn_toggle = ttk.Button(controls, text="Masquer catégorie", command=toggle_categorie)
    btn_toggle.pack(side="left", padx=(0, 6))

    def clear_and_reload() -> None:
        ccb.clear()
        ccb.add_items(produits)
        info_var.set("Rechargé — sélectionnez un élément…")

    ttk.Button(controls, text="Recharger", command=clear_and_reload).pack(side="left")

    root.mainloop()


if __name__ == "__main__":
    main()
