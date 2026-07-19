"""memory_monitor.py
Utilitaire pour diagnostiquer les fuites memoire dans une appli Tkinter.

Usage rapide :

    from memory_monitor import MemoryMonitor
    mon = MemoryMonitor(root=root, interval=10, log_file="memleak.log")
    mon.start()

Il tourne via root.after() (aucun thread requis) et affiche
periodiquement :
  - les lignes de code dont l'allocation memoire augmente le plus
    (diff tracemalloc depuis le dernier rapport)
  - le nombre de widgets Tk actuellement vivants, par type

Si le nombre de widgets ne redescend jamais apres fermeture de
fenetres, ou si les memes lignes de code reapparaissent en tete
du diff a chaque rapport, tu tiens ta fuite.
"""

import gc
import pathlib
import threading
import time
import tracemalloc
from collections import Counter


class MemoryMonitor:
    def __init__(self, root=None, interval=10, top_n=10, log_file=None):
        """Root      : instance Tk racine. Si fournie, le monitoring
                    s'integre a la boucle Tkinter via after().
                    Sinon, tourne dans un thread daemon separe.
        interval  : secondes entre deux rapports.
        top_n     : nombre de lignes/types affiches par rapport.
        log_file  : chemin optionnel pour aussi ecrire les rapports
                    dans un fichier (utile pour laisser tourner
                    longtemps et comparer apres coup).
        """
        self.root = root
        self.interval = interval
        self.top_n = top_n
        self.log_file = log_file
        self._snapshot = None
        self._running = False
        self._thread = None

    def start(self):
        tracemalloc.start(25)  # garde 25 frames de pile par allocation
        self._snapshot = tracemalloc.take_snapshot()
        self._running = True
        if self.root is not None:
            self.root.after(self.interval * 1000, self._tick_tk)
        else:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False

    def _tick_tk(self):
        if not self._running:
            return
        self._report()
        self.root.after(self.interval * 1000, self._tick_tk)

    def _loop(self):
        while self._running:
            time.sleep(self.interval)
            self._report()

    def _report(self):
        gc.collect()
        snap = tracemalloc.take_snapshot()
        stats = snap.compare_to(self._snapshot, "lineno")

        lines = [f"--- Rapport memoire ({time.strftime('%H:%M:%S')}) ---"]
        lines.append("Top allocations (diff depuis le dernier rapport) :")
        for stat in stats[: self.top_n]:
            lines.append(f"  {stat}")

        # Widgets Tk actuellement vivants -> reperer ceux qui ne sont
        # jamais detruits (fenetres, boutons, images, etc.)
        try:
            import tkinter as tk

            widgets = [o for o in gc.get_objects() if isinstance(o, tk.Widget)]
            counts = Counter(type(w).__name__ for w in widgets)
            lines.append(f"Widgets Tk vivants : {sum(counts.values())}")
            for name, n in counts.most_common(self.top_n):
                lines.append(f"  {name}: {n}")

            images = [o for o in gc.get_objects() if isinstance(o, (tk.PhotoImage, tk.BitmapImage))]
            lines.append(f"Images Tk vivantes : {len(images)}")
        except Exception as exc:
            lines.append(f"(inspection widgets impossible : {exc})")

        # Threads actifs : un thread qui ne se termine jamais (boucle
        # infinie, IO bloquante sans timeout...) n'est jamais garbage
        # collecte, et empeche aussi la liberation de tout ce qu'il
        # reference dans sa closure (widgets, callbacks, donnees...).
        # Si ce nombre grossit sans jamais redescendre, c'est souvent
        # la vraie source de la fuite plutot que les widgets eux-memes.
        threads = threading.enumerate()
        lines.append(f"Threads actifs : {len(threads)}")
        thread_counts = Counter(t.name.rsplit("-", 1)[0] if t.name else "Thread" for t in threads)
        for name, n in thread_counts.most_common(self.top_n):
            lines.append(f"  {name}: {n}")

        text = "\n".join(lines)
        print(text)
        if self.log_file:
            with pathlib.Path(self.log_file).open("a", encoding="utf-8") as f:
                f.write(text + "\n")

        # Le prochain diff se fait par rapport a CE snapshot, pas au tout
        # premier : ca montre la croissance recente, pas la croissance
        # cumulee depuis le lancement (les deux sont utiles ; commente
        # la ligne suivante si tu preferes le cumule depuis le debut).
        self._snapshot = snap


if __name__ == "__main__":
    # Petit exemple autonome : cree/detruit des Toplevel en boucle
    # pour voir si le monitor detecte une fuite volontaire.
    import tkinter as tk

    leaked_refs = []  # simule une fuite en gardant des references

    root = tk.Tk()
    mon = MemoryMonitor(root=root, interval=5)
    mon.start()

    def spawn_leaky_window():
        top = tk.Toplevel(root)
        tk.Label(top, text="fenetre jetable").pack()
        leaked_refs.append(top)  # <-- volontairement pas de destroy()
        root.after(300, spawn_leaky_window)

    root.after(300, spawn_leaky_window)
    root.mainloop()
