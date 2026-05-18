"""Example usage of ColumnListbox with 1000 Produit objects."""

import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "__src__"))

from views.components.column_listbox import ColumnListbox


@dataclass
class Produit:
    id: int
    nom: str
    categorie: str
    prix: float


def main() -> None:
    root = tk.Tk()
    root.title("ColumnListbox — exemple Produit")
    root.geometry("700x500")

    clb = ColumnListbox(root, scrollbar=True, width=60, height=15)
    clb.pack(fill="both", expand=True, padx=10, pady=10)

    clb.add_column("id",        lambda p: p.id,               width=6,  visible=False)
    clb.add_column("nom",       lambda p: p.nom,              width=25, visible=True)
    clb.add_column("categorie", lambda p: p.categorie,         width=15, visible=True)
    clb.add_column("prix",      lambda p: f"{p.prix:.2f} €",  width=10, visible=True)

    produits = [Produit(i, f"Produit {i}", f"Cat {'ABC'[i % 3]}", i * 1.5) for i in range(1000)]
    clb.add_items(produits)

    info_var = tk.StringVar(value="Cliquez sur un élément…")
    tk.Label(root, textvariable=info_var, anchor="w", relief="sunken", pady=4).pack(
        fill="x", padx=10, pady=(0, 6)
    )

    def on_select(event: tk.Event) -> None:
        obj = clb.get_selected_object()
        row = clb.get_selected_row()
        if obj is None or row is None:
            return
        prix_val = clb.get_selected_value("prix")
        info_var.set(f"Objet: {obj}  |  ID caché: {row['id']}  |  Prix: {prix_val}")

    clb.bind("<<ListboxSelect>>", on_select)

    controls = tk.Frame(root)
    controls.pack(fill="x", padx=10, pady=(0, 10))

    def toggle_categorie() -> None:
        current = clb.get_column_visible("categorie")
        clb.set_column_visible("categorie", not current)
        label = "Masquer catégorie" if not current else "Afficher catégorie"
        btn_toggle.configure(text=label)

    btn_toggle = tk.Button(controls, text="Masquer catégorie", command=toggle_categorie)
    btn_toggle.pack(side="left", padx=(0, 6))

    def clear_and_reload() -> None:
        clb.clear()
        clb.add_items(produits)
        info_var.set("Rechargé — cliquez sur un élément…")

    tk.Button(controls, text="Recharger (1000)", command=clear_and_reload).pack(side="left")

    root.mainloop()


if __name__ == "__main__":
    main()
