"""Validation d'un champ texte de mappings clé = clé.

Format attendu :
    - Une affectation par ligne : A = B
    - Exactement un '=' par ligne
    - La ligne ne peut pas commencer par e0., e1., …, e6.
    - A et B sont des clés composées uniquement de minuscules, chiffres, '_' et '.'
    - Les lignes vides sont ignorées

La validation s'arrête à la première erreur et renvoie un code AGG_10XX.
"""

import re
from dataclasses import dataclass

_KEY_RE = re.compile(r"^[a-z0-9_.]+$")
# _FORBIDDEN_PREFIXES = tuple(f"e{i}." for i in range(6))  # e0. … e5.
_FORBIDDEN_PREFIXES = ["e6"]

# ── Résultat ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParsingResult:
    """Résultat de la validation (fail-fast : 0 ou 1 erreur)."""

    is_valid: bool
    code: str | None = None
    message: str | None = None
    line_number: int | None = None
    line_content: str | None = None

    def __str__(self) -> str:
        if self.is_valid:
            return "✓ Aucune erreur détectée."
        return f"[{self.code}] ligne {self.line_number} : {self.message}\n  → {self.line_content!r}"


_OK = ParsingResult(is_valid=True)


def _fail(code: str, msg: str, ln: int, content: str) -> ParsingResult:
    return ParsingResult(False, code, msg, ln, content)


# ── Codes d'erreur ──────────────────────────────────────────────────
#
#   AGG_1001  champ vide
#   AGG_1002  ligne commence par un préfixe interdit (e0. … e6.)
#   AGG_1003  aucun '=' trouvé
#   AGG_1004  plusieurs '=' sur la même ligne
#   AGG_1005  clé vide (gauche ou droite)
#   AGG_1006  clé contient des majuscules
#   AGG_1007  clé contient des espaces
#   AGG_1008  clé contient des caractères interdits
#   AGG_1009  clé commence ou finit par un point
#   AGG_1010  clé contient un double point (..)
#


# ── Validation d'une clé ────────────────────────────────────────────


def _validate_key(key: str, side: str, ln: int, content: str) -> ParsingResult | None:
    """Renvoie un ValidationResult d'erreur, ou None si la clé est valide."""
    if not key:
        return _fail("AGG_1005", f"clé {side} vide", ln, content)

    if re.search(r"[A-Z]", key):
        return _fail("AGG_1006", f"clé {side} contient des majuscules : {key!r}", ln, content)

    if re.search(r"\s", key):
        return _fail("AGG_1007", f"clé {side} contient des espaces : {key!r}", ln, content)

    if not _KEY_RE.match(key):
        bad = sorted({ch for ch in key if not re.match(r"[a-z0-9_.]", ch)})
        return _fail("AGG_1008", f"clé {side} contient des caractères interdits {bad} : {key!r}", ln, content)

    if key.startswith(".") or key.endswith("."):
        return _fail("AGG_1009", f"clé {side} commence ou finit par un point : {key!r}", ln, content)

    if ".." in key:
        return _fail("AGG_1010", f"clé {side} contient un double point : {key!r}", ln, content)

    return None


# ── Validation du champ complet ─────────────────────────────────────


def validate_aggregators_list(text: str) -> ParsingResult:
    """Valide un champ texte multi-lignes de mappings ``A = B``.

    S'arrête dès la première erreur et renvoie un code AGG_10XX.

    Paramètres
    ----------
    text : str
        Le contenu du champ à vérifier.

    Retourne
    --------
    ValidationResult
        ``is_valid=True`` si tout est conforme,
        sinon ``is_valid=False`` avec ``code``, ``message``,
        ``line_number`` et ``line_content``.
    """
    if not text or not text.strip():
        return _fail("AGG_1001", "le champ est vide", 0, "")

    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue

        # ── Préfixe interdit ────────────────────────────────────
        for prefix in _FORBIDDEN_PREFIXES:
            if not line.startswith(prefix):
                return _fail("AGG_1002", f"la ligne doit commencer le préfixe : {prefix!r}", number, line)

        # ── Exactement un '=' ───────────────────────────────────
        eq_count = line.count("=")
        if eq_count == 0:
            return _fail("AGG_1003", "aucun séparateur '=' trouvé", number, line)
        if eq_count > 1:
            return _fail("AGG_1004", "plusieurs '=' sur la même ligne", number, line)

        # ── Validation des clés ─────────────────────────────────
        left, right = line.split("=")
        left, right = left.strip(), right.strip()

        err = _validate_key(left, "gauche (A)", number, line)
        if err:
            return err

        err = _validate_key(right, "droite (B)", number, line)
        if err:
            return err

    return _OK


# ── Parsing ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Mapping:
    """Une paire clé gauche / clé droite."""

    e6: str
    sourcing: str


def parse_aggregators_list(text: str) -> list[Mapping]:
    """Extrait la liste des paires depuis le champ texte.

    Ne fait aucune validation. Appeler ``validate()`` avant si nécessaire.

    Paramètres
    ----------
    text : str
        Le contenu du champ à analyser.

    Retourne
    --------
    list[Mapping]
        Liste des paires ``(e6, sourcing)`` extraites.
    """
    mappings: list[Mapping] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        left, right = line.split("=")
        mappings.append(Mapping(e6=left.strip(), sourcing=right.strip()))

    return mappings


# ── Point d'entrée rapide ───────────────────────────────────────────

if __name__ == "__main__":
    tests = {
        "Valide": "abc_x = def.y\nfoo = bar",
        "AGG_1001 – vide": "",
        "AGG_1002 – préfixe interdit": "e3.title = something",
        "AGG_1003 – pas de =": "abc def",
        "AGG_1004 – plusieurs =": "a = b = c",
        "AGG_1005 – clé vide": " = foo",
        "AGG_1006 – majuscules": "Abc = foo",
        "AGG_1007 – espace dans clé": "ab c = foo",
        "AGG_1008 – caractère interdit": "ab@c = foo",
        "AGG_1009 – point en bord": ".abc = foo",
        "AGG_1010 – double point": "a..b = foo",
    }

    for label, sample in tests.items():
        r = validate_aggregators_list(sample)
        print(f"[{label}]")
        print(f"  {r}\n")

    # ── Démo de parse() ──
    print("=" * 60)
    print("Démo parse_aggregators_list()\n")

    valid_text = "title_full = source_name\ndesc = origin_label"
    mappings = parse_aggregators_list(valid_text)
    for m in mappings:
        print(f"  e6={m.e6!r}  sourcing={m.sourcing!r}")
