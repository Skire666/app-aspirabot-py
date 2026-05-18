"""Demonstration of ColumnCombobox with 10 000 Produit objects."""

from __future__ import annotations

import time
import tkinter as tk
from dataclasses import dataclass

from column_combobox import ColumnCombobox


@dataclass
class Produit:
    id: int
    nom: str
    categorie: str
    prix: float


def main() -> None:
    root = tk.Tk()
    root.title("ColumnCombobox Demo")

    ccb = ColumnCombobox(root, state="readonly", width=60)
    ccb.pack(fill="x", padx=10, pady=10)

    ccb.add_column("id",        lambda p: p.id,              width=60,  visible=False)
    ccb.add_column("nom",       lambda p: p.nom,             width=200, visible=True)
    ccb.add_column("categorie", lambda p: p.categorie,       width=120, visible=True)
    ccb.add_column("prix",      lambda p: f"{p.prix:.2f} €", width=80,  visible=True)

    ccb.set_display_column("nom")

    t0 = time.perf_counter()
    produits = [Produit(i, f"Produit {i}", f"Cat {i % 10}", i * 1.5) for i in range(10_000)]
    for p in produits:
        ccb.add_item(p)
    print(f"Inserted 10 000 items in {(time.perf_counter() - t0) * 1000:.0f} ms")

    def on_select(_event: tk.Event) -> None:
        obj = ccb.get_selected_object()
        row = ccb.get_selected_row()
        print(f"Objet   : {obj}")
        print(f"ID caché: {row['id']}")
        print(f"Prix    : {ccb.get_selected_value('prix')}")

    ccb.bind("<<ComboboxSelected>>", on_select)

    status = tk.Label(root, text="", anchor="w")
    status.pack(fill="x", padx=10)

    def toggle_categorie() -> None:
        cur = ccb.get_column_visible("categorie")
        ccb.set_column_visible("categorie", not cur)
        status.configure(text=f"categorie visible: {not cur}")

    tk.Button(root, text="Afficher/Masquer catégorie", command=toggle_categorie).pack(pady=4)

    root.mainloop()


if __name__ == "__main__":
    main()
