"""benchmark_filter_sort.py

Benchmark avant/après optimisation de _filter_and_sort_urls.
top_n = 0 (aucune limite) — les deux versions font le même travail.
Aucune dépendance externe. Python 3.11+ (dont 3.13).

    python benchmark_filter_sort.py
"""

from __future__ import annotations

import enum
import random
import statistics
import time
from datetime import datetime, timedelta
from operator import itemgetter


class UrlSortOrderEnum(enum.Enum):
    E_MTIME_ASC = "asc"
    E_MTIME_DESC = "desc"


class UrlProcessor:
    def __init__(self, newest, oldest, sort_order) -> None:
        self._date_modified_newest = newest
        self._date_modified_oldest = oldest
        self._sort_order = sort_order

    # --- VERSION ORIGINALE ------------------------------------------------
    def original(self, url_with_time: dict[str, datetime]) -> list[str]:
        list_filtered: list[tuple[str, datetime]] = []

        for url, dt in url_with_time.items():
            if (self._date_modified_newest is None or dt <= self._date_modified_newest) and (
                self._date_modified_oldest is None or dt >= self._date_modified_oldest
            ):
                list_filtered.append((url, dt))

        reverse = self._sort_order == UrlSortOrderEnum.E_MTIME_DESC
        list_filtered.sort(key=lambda x: x[1], reverse=reverse)

        return [url for url, _ in list_filtered]

    # --- VERSION OPTIMISÉE ------------------------------------------------
    def optimized(self, url_with_time: dict[str, datetime]) -> list[str]:
        newest = self._date_modified_newest
        oldest = self._date_modified_oldest
        reverse = self._sort_order == UrlSortOrderEnum.E_MTIME_DESC

        filtered = [
            (url, dt)
            for url, dt in url_with_time.items()
            if (newest is None or dt <= newest) and (oldest is None or dt >= oldest)
        ]
        filtered.sort(key=itemgetter(1), reverse=reverse)

        return [url for url, _ in filtered]


def make_fake_data(n: int, seed: int = 42) -> dict[str, datetime]:
    rng = random.Random(seed)
    base = datetime(2020, 1, 1)
    return {
        f"https://example.com/page/{i}": base + timedelta(seconds=rng.randint(0, 5 * 365 * 24 * 3600)) for i in range(n)
    }


def time_call(fn, data, repeats: int) -> float:
    """Temps médian (ms) sur `repeats` exécutions."""
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(data)
        t1 = time.perf_counter()
        samples.append((t1 - t0) * 1000.0)
    return statistics.median(samples)


def main() -> None:
    N = 500_000
    REPEATS = 7

    print(f"Benchmark — n = {N:,} URLs, repeats = {REPEATS} (temps médian)\n")

    data = make_fake_data(N)

    # Filtre sur une plage de dates réaliste
    dates = list(data.values())
    dmin, dmax = min(dates), max(dates)
    span = dmax - dmin
    proc = UrlProcessor(newest=dmin + span * 0.75, oldest=dmin + span * 0.25, sort_order=UrlSortOrderEnum.E_MTIME_DESC)

    # Vérification : résultats identiques
    assert proc.original(data) == proc.optimized(data), "Les résultats diffèrent !"
    print("Cohérence : les deux versions renvoient un résultat identique.\n")

    # Préchauffage (évite de payer le coût du premier appel dans la mesure)
    proc.original(data)
    proc.optimized(data)

    t_orig = time_call(proc.original, data, REPEATS)
    t_opt = time_call(proc.optimized, data, REPEATS)
    speedup = t_orig / t_opt if t_opt else float("inf")
    gain = (1 - t_opt / t_orig) * 100 if t_orig else 0.0

    print(f"  original   : {t_orig:8.3f} ms")
    print(f"  optimized  : {t_opt:8.3f} ms")
    print(f"  -> accélération x{speedup:.2f}  ({gain:+.1f} %)")


if __name__ == "__main__":
    main()
