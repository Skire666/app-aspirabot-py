#!/usr/bin/env python3
"""Analyse des lignes 'Bilan step' d'un fichier de log.

Principe :
  - Chaque bloc d'étape partage un même code à 4 caractères (2e champ).
  - Le type d'étape est déclaré sur une ligne '... | CODE | <TYPE> | ...'
  - La durée est sur la ligne '... | CODE | Bilan step : STATUS | XX.XXXs'
  On relie les deux via le dernier <TYPE> vu pour ce code.
"""

import pathlib
import re
import sys
from collections import defaultdict

# --- Config ---------------------------------------------------------------
FICHIER = "try stats.txt"  # adapte le chemin si besoin
TOP_TYPES = 5
TOP_DUREES = 20

# --- Regex ----------------------------------------------------------------
RE_TYPE = re.compile(r"<([A-Z0-9_]+)>")  # ex: <WAIT_HTML_ELEMENTS>
RE_DUREE = re.compile(r"(\d+\.\d+)\s*s")  # ex: 2.953s
RE_STATUS = re.compile(r"Bilan step\s*:\s*(\w+)")  # ex: SUCCESS / FAILED


def parse(fichier):
    """Retourne la liste des étapes 'Bilan step' : (type, duree, status, code, ligne)."""
    type_courant = {}  # code -> dernier type vu
    etapes = []

    with pathlib.Path(fichier).open(encoding="utf-8", errors="replace") as f:
        for ligne in f:
            champs = [c.strip() for c in ligne.split("|")]
            if len(champs) < 3:
                continue
            code = champs[1]

            # Ligne de déclaration de type -> on mémorise pour ce code
            m_type = RE_TYPE.search(ligne)
            if m_type and "Bilan step" not in ligne:
                type_courant[code] = m_type.group(1)

            # Ligne de bilan -> on enregistre la durée
            if "Bilan step" in ligne:
                m_dur = RE_DUREE.search(ligne)
                if not m_dur:
                    continue
                duree = float(m_dur.group(1))
                status = (RE_STATUS.search(ligne) or [None, "?"])[1] if RE_STATUS.search(ligne) else "?"
                m_status = RE_STATUS.search(ligne)
                status = m_status.group(1) if m_status else "?"
                etape_type = type_courant.get(code, "<INCONNU>")
                etapes.append(
                    {"type": etape_type, "duree": duree, "status": status, "code": code, "ligne": ligne.strip()}
                )
    return etapes


def agreger(etapes):
    """Agrège par type : total, moyenne, nb occurrences."""
    total = defaultdict(float)
    count = defaultdict(int)
    for e in etapes:
        total[e["type"]] += e["duree"]
        count[e["type"]] += 1
    stats = []
    for t in total:
        stats.append({"type": t, "total": total[t], "nb": count[t], "moyenne": total[t] / count[t]})
    return stats


def main():
    fichier = sys.argv[1] if len(sys.argv) > 1 else FICHIER
    etapes = parse(fichier)

    if not etapes:
        print("Aucune ligne 'Bilan step' exploitable trouvée.")
        return

    total_global = sum(e["duree"] for e in etapes)
    print(f"Fichier         : {fichier}")
    print(f"Étapes analysées: {len(etapes)}")
    print(f"Temps total     : {total_global:.3f}s\n")

    # --- Top des types par TEMPS CUMULÉ ---
    stats = agreger(etapes)
    stats_cumul = sorted(stats, key=lambda s: s["total"], reverse=True)

    print(f"=== TOP {TOP_TYPES} TYPES PAR TEMPS CUMULÉ ===")
    print(f"{'Type':<28}{'Total':>12}{'Nb':>7}{'Moy':>12}{'% total':>10}")
    for s in stats_cumul[:TOP_TYPES]:
        pct = 100 * s["total"] / total_global
        print(f"{s['type']:<28}{s['total']:>10.3f}s{s['nb']:>7}{s['moyenne']:>10.3f}s{pct:>9.1f}%")

    # --- Top des types par TEMPS MOYEN (bonus) ---
    stats_moy = sorted(stats, key=lambda s: s["moyenne"], reverse=True)
    print(f"\n=== TOP {TOP_TYPES} TYPES PAR TEMPS MOYEN / occurrence ===")
    print(f"{'Type':<28}{'Moy':>12}{'Nb':>7}{'Total':>12}")
    for s in stats_moy[:TOP_TYPES]:
        print(f"{s['type']:<28}{s['moyenne']:>10.3f}s{s['nb']:>7}{s['total']:>10.3f}s")

    # --- Top des durées individuelles ---
    plus_longues = sorted(etapes, key=lambda e: e["duree"], reverse=True)
    print(f"\n=== TOP {TOP_DUREES} DURÉES LES PLUS LONGUES ===")
    print(f"{'#':>3}{'Durée':>12}  {'Type':<28}{'Status':<10}{'Code'}")
    for i, e in enumerate(plus_longues[:TOP_DUREES], 1):
        print(f"{i:>3}{e['duree']:>10.3f}s  {e['type']:<28}{e['status']:<10}{e['code']}")


if __name__ == "__main__":
    main()
