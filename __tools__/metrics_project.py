#!/usr/bin/env python3
"""Analyseur de métriques pour un projet Python.
Lit récursivement un dossier (par défaut '__src__') et affiche des métriques
dans une interface tkinter : lignes, fonctions, classes, taille des fonctions
et complexité cyclomatique de McCabe.
"""

import ast
import os
import pathlib
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog, messagebox, ttk

DEFAULT_DIR = "__src__"
IGNORED_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".idea", ".mypy_cache"}


# --------------------------------------------------------------------------- #
#  Outils statistiques
# --------------------------------------------------------------------------- #
TRANCHES = ((0.10, "10% les pires"), (0.20, "20% suivants "), (0.30, "30% suivants "), (0.40, "40% restants "))


def decouper_tranches(valeurs):
    """Trie les valeurs du pire (plus grand) au meilleur, puis les répartit
    en tranches de 10 / 20 / 30 / 40 %. Renvoie [(label, count, moyenne, mini, maxi)].
    """
    if not valeurs:
        return []
    v = sorted(valeurs, reverse=True)
    n = len(v)
    resultats = []
    debut = 0
    cumul = 0.0
    for i, (p, label) in enumerate(TRANCHES):
        cumul += p
        fin = n if i == len(TRANCHES) - 1 else round(cumul * n)
        morceau = v[debut:fin]
        if morceau:
            moy = sum(morceau) / len(morceau)
            resultats.append((label, len(morceau), moy, min(morceau), max(morceau)))
        else:
            resultats.append((label, 0, 0, 0, 0))
        debut = fin
    return resultats


def formater_tranches(valeurs):
    lignes = []
    for label, n, moy, mini, maxi in decouper_tranches(valeurs):
        if n:
            lignes.append(f"  {label} ({n:>4} fn) : moy {moy:6.1f}  [{mini}–{maxi}]")
        else:
            lignes.append(f"  {label} (   0 fn) : —")
    return "\n".join(lignes)


def formater_top(fns, cle, n=5):
    """Top n des fonctions selon une clé ('lignes' ou 'mccabe')."""
    top = sorted(fns, key=lambda f: -f[cle])[:n]
    if not top:
        return "  —"
    return "\n".join(f"  {f[cle]:>4}  {f['nom']}  ({f['fichier']})" for f in top)


def rang_mccabe(c):
    """Rang qualitatif façon radon."""
    if c <= 5:
        return "A"
    if c <= 10:
        return "B"
    if c <= 20:
        return "C"
    if c <= 30:
        return "D"
    if c <= 40:
        return "E"
    return "F"


def formater_taille(octets):
    for unite in ("o", "Ko", "Mo", "Go"):
        if octets < 1024:
            return f"{octets:.1f} {unite}"
        octets /= 1024
    return f"{octets:.1f} To"


# --------------------------------------------------------------------------- #
#  Complexité cyclomatique de McCabe
# --------------------------------------------------------------------------- #
class VisiteurComplexite(ast.NodeVisitor):
    """Calcule la complexité cyclomatique d'UNE fonction.
    Ne descend pas dans les fonctions imbriquées (comptées séparément).
    Complexité = 1 + nombre de points de décision.
    """

    def __init__(self):
        self.complexite = 1
        self._racine = True

    def visit_FunctionDef(self, noeud):
        if self._racine:
            self._racine = False
            self.generic_visit(noeud)
        # sinon : fonction imbriquée -> ignorée ici

    visit_AsyncFunctionDef = visit_FunctionDef

    def _decision(self, noeud):
        self.complexite += 1
        self.generic_visit(noeud)

    visit_If = _decision
    visit_For = _decision
    visit_AsyncFor = _decision
    visit_While = _decision
    visit_ExceptHandler = _decision

    def visit_BoolOp(self, noeud):
        # 'a and b and c' ajoute 2 chemins
        self.complexite += len(noeud.values) - 1
        self.generic_visit(noeud)

    def visit_IfExp(self, noeud):  # expression ternaire
        self.complexite += 1
        self.generic_visit(noeud)

    def visit_comprehension(self, noeud):  # if dans une compréhension
        self.complexite += len(noeud.ifs)
        self.generic_visit(noeud)


def complexite_fonction(noeud):
    v = VisiteurComplexite()
    v.visit(noeud)
    return v.complexite


def _est_docstring(noeud):
    """Vrai si le nœud est une simple expression chaîne (une docstring)."""
    return isinstance(noeud, ast.Expr) and isinstance(noeud.value, ast.Constant) and isinstance(noeud.value.value, str)


def compter_lignes_effectives(noeud_fonction, lignes_physiques):
    """Lignes de code effectives du CORPS de la fonction (méthode « physique »,
    identique à EPI025) :
      - la signature (def ...) n'est pas comptée ;
      - une docstring en tête de corps est ignorée ;
      - on compte les lignes physiques couvertes par les instructions, sans les
        lignes vides ni les commentaires (déduplication par numéro de ligne).
    """
    corps = noeud_fonction.body
    if corps and _est_docstring(corps[0]):
        corps = corps[1:]
    if not corps:
        return 0

    numeros = set()
    for stmt in corps:
        debut = stmt.lineno
        fin = getattr(stmt, "end_lineno", debut) or debut
        numeros.update(range(debut, fin + 1))

    total = 0
    for n in numeros:
        ligne = lignes_physiques[n - 1].strip()
        if ligne and not ligne.startswith("#"):
            total += 1
    return total


# --------------------------------------------------------------------------- #
#  Analyse d'un fichier
# --------------------------------------------------------------------------- #
def analyser_fichier_python(chemin, chemin_relatif):
    lignes_code = lignes_commentaire = lignes_vide = 0
    nb_classes = 0
    fonctions = []  # liste de dicts : nom, fichier, lignes, mccabe

    try:
        with pathlib.Path(chemin).open(encoding="utf-8", errors="replace") as f:
            contenu = f.read()
    except OSError:
        return None

    lignes_physiques = contenu.splitlines()
    for ligne in lignes_physiques:
        depouille = ligne.strip()
        if not depouille:
            lignes_vide += 1
        elif depouille.startswith("#"):
            lignes_commentaire += 1
        else:
            lignes_code += 1

    try:
        arbre = ast.parse(contenu)
        for noeud in ast.walk(arbre):
            if isinstance(noeud, ast.ClassDef):
                nb_classes += 1
            elif isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fonctions.append(
                    {
                        "nom": noeud.name,
                        "fichier": chemin_relatif,
                        "lignes": compter_lignes_effectives(noeud, lignes_physiques),
                        "mccabe": complexite_fonction(noeud),
                    }
                )
    except SyntaxError:
        pass

    return {
        "code": lignes_code,
        "commentaire": lignes_commentaire,
        "vide": lignes_vide,
        "total": lignes_code + lignes_commentaire + lignes_vide,
        "classes": nb_classes,
        "fonctions": fonctions,
    }


def analyser_projet(racine):
    stats = {
        "nb_fichiers_total": 0,
        "nb_fichiers_py": 0,
        "taille_octets": 0,
        "code": 0,
        "commentaire": 0,
        "vide": 0,
        "total_lignes": 0,
        "classes": 0,
        "par_extension": defaultdict(int),
        "fichiers": [],  # (chemin_relatif, lignes_total)
        "fonctions": [],  # dicts agrégés de toutes les fonctions
    }

    for dossier, sous_dossiers, fichiers in os.walk(racine):
        sous_dossiers[:] = [d for d in sous_dossiers if d not in IGNORED_DIRS]
        for nom in fichiers:
            chemin = os.path.join(dossier, nom)
            stats["nb_fichiers_total"] += 1
            ext = os.path.splitext(nom)[1].lower() or "(sans ext.)"
            stats["par_extension"][ext] += 1
            try:
                stats["taille_octets"] += pathlib.Path(chemin).stat().st_size
            except OSError:
                pass

            if ext == ".py":
                rel = os.path.relpath(chemin, racine)
                m = analyser_fichier_python(chemin, rel)
                if m:
                    stats["nb_fichiers_py"] += 1
                    stats["code"] += m["code"]
                    stats["commentaire"] += m["commentaire"]
                    stats["vide"] += m["vide"]
                    stats["total_lignes"] += m["total"]
                    stats["classes"] += m["classes"]
                    stats["fonctions"].extend(m["fonctions"])
                    stats["fichiers"].append((rel, m["total"]))

    return stats


# --------------------------------------------------------------------------- #
#  Interface
# --------------------------------------------------------------------------- #
class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Métriques du projet")
        self.geometry("720x640")
        self.dossier = tk.StringVar(value=DEFAULT_DIR)
        self._construire_interface()

    def _construire_interface(self):
        haut = ttk.Frame(self, padding=10)
        haut.pack(fill="x")
        ttk.Label(haut, text="Dossier :").pack(side="left")
        ttk.Entry(haut, textvariable=self.dossier, width=40).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(haut, text="Parcourir…", command=self._choisir).pack(side="left")
        ttk.Button(haut, text="Analyser", command=self._analyser).pack(side="left", padx=5)

        carnet = ttk.Notebook(self)
        carnet.pack(fill="both", expand=True, padx=10, pady=5)

        # Onglets de résumé (texte)
        self.txt_basique = self._creer_zone_texte(carnet, "Basique")
        self.txt_fonctions = self._creer_zone_texte(carnet, "Fonctions")
        self.txt_mccabe = self._creer_zone_texte(carnet, "McCabe")

        # Onglet fichiers (table)
        onglet_f = ttk.Frame(carnet)
        carnet.add(onglet_f, text="Fichiers")
        self.table_fichiers = self._creer_table(onglet_f, [("#0", "Fichier", 300), ("lignes", "Lignes", 80)])

        # Onglet fonctions (table)
        onglet_fn = ttk.Frame(carnet)
        carnet.add(onglet_fn, text="Fonctions (McCabe)")
        self.table_fonctions = self._creer_table(
            onglet_fn,
            [
                ("#0", "Fonction", 220),
                ("fichier", "Fichier", 200),
                ("lignes", "Lignes", 70),
                ("mccabe", "McCabe", 70),
                ("rang", "Rang", 50),
            ],
        )

    def _creer_table(self, parent, colonnes):
        ids = [c[0] for c in colonnes if c[0] != "#0"]
        table = ttk.Treeview(parent, columns=ids, show="tree headings")
        for cid, titre, largeur in colonnes:
            table.heading(cid, text=titre)
            ancre = "w" if cid in ("#0", "fichier") else "e"
            table.column(cid, width=largeur, anchor=ancre)
        defile = ttk.Scrollbar(parent, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=defile.set)
        table.pack(side="left", fill="both", expand=True)
        defile.pack(side="right", fill="y")
        return table

    def _creer_zone_texte(self, carnet, titre):
        onglet = ttk.Frame(carnet)
        carnet.add(onglet, text=titre)
        txt = tk.Text(onglet, wrap="word", state="disabled", font="TkFixedFont")
        defile = ttk.Scrollbar(onglet, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=defile.set)
        txt.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        defile.pack(side="right", fill="y")
        return txt

    @staticmethod
    def _ecrire(widget, texte):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", texte)
        widget.configure(state="disabled")

    def _choisir(self):
        choix = filedialog.askdirectory(title="Choisir le dossier source")
        if choix:
            self.dossier.set(choix)

    def _analyser(self):
        racine = self.dossier.get()
        if not pathlib.Path(racine).is_dir():
            messagebox.showerror("Erreur", f"Dossier introuvable : {racine}")
            return

        stats = analyser_projet(racine)
        fns = stats["fonctions"]
        tailles = [f["lignes"] for f in fns]
        complexites = [f["mccabe"] for f in fns]

        ratio_comm = 100 * stats["commentaire"] / stats["total_lignes"] if stats["total_lignes"] else 0
        moy_lignes = stats["total_lignes"] / stats["nb_fichiers_py"] if stats["nb_fichiers_py"] else 0
        moy_taille_fn = sum(tailles) / len(tailles) if tailles else 0
        moy_mccabe = sum(complexites) / len(complexites) if complexites else 0

        extensions = ", ".join(f"{ext}: {n}" for ext, n in sorted(stats["par_extension"].items(), key=lambda x: -x[1]))

        texte_basique = (
            f"Fichiers totaux         : {stats['nb_fichiers_total']}\n"
            f"Fichiers Python         : {stats['nb_fichiers_py']}\n"
            f"Taille totale           : {formater_taille(stats['taille_octets'])}\n"
            f"Lignes de code          : {stats['code']}\n"
            f"Lignes de commentaire   : {stats['commentaire']} ({ratio_comm:.1f} %)\n"
            f"Lignes vides            : {stats['vide']}\n"
            f"Total lignes (.py)      : {stats['total_lignes']}\n"
            f"Moyenne lignes/fichier  : {moy_lignes:.1f}\n"
            f"Classes                 : {stats['classes']}\n"
            f"Fonctions               : {len(fns)}\n"
            f"Extensions              : {extensions}"
        )
        texte_fonctions = (
            "Taille = lignes de code physiques du corps (signature et docstring\n"
            "exclues, sans lignes vides ni commentaires) — comme EPI025.\n\n"
            f"Moyenne globale          : {moy_taille_fn:.1f}\n\n"
            "--- Tranches, du pire au meilleur ---\n"
            f"{formater_tranches(tailles)}\n\n"
            "--- Top 5 fonctions les plus longues ---\n"
            f"{formater_top(fns, 'lignes')}"
        )
        texte_mccabe = (
            "Complexité cyclomatique de McCabe, par fonction.\n\n"
            f"Moyenne globale          : {moy_mccabe:.2f}\n\n"
            "--- Tranches, du pire au meilleur ---\n"
            f"{formater_tranches(complexites)}\n\n"
            "--- Top 5 complexités les plus hautes ---\n"
            f"{formater_top(fns, 'mccabe')}"
        )
        self._ecrire(self.txt_basique, texte_basique)
        self._ecrire(self.txt_fonctions, texte_fonctions)
        self._ecrire(self.txt_mccabe, texte_mccabe)

        # Table fichiers
        self.table_fichiers.delete(*self.table_fichiers.get_children())
        for rel, total in sorted(stats["fichiers"], key=lambda x: -x[1]):
            self.table_fichiers.insert("", "end", text=rel, values=(total,))

        # Table fonctions (triées par complexité décroissante)
        self.table_fonctions.delete(*self.table_fonctions.get_children())
        for f in sorted(fns, key=lambda x: -x["mccabe"]):
            self.table_fonctions.insert(
                "", "end", text=f["nom"], values=(f["fichier"], f["lignes"], f["mccabe"], rang_mccabe(f["mccabe"]))
            )


if __name__ == "__main__":
    Application().mainloop()
