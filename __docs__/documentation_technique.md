# Documentation Technique

## 1. Architecture du Système

L'application est développée en **Python 3** et suit une architecture modulaire séparant l'interface graphique du moteur de scraping.

### Structure des dossiers :
- `main.py` : Point d'entrée de l'application. Instancie et lance l'IHM.
- `gui/` : Module contenant le code relatif à l'interface graphique.
  - `app.py` : Contient la classe `ScraperApp` héritée de `tkinter.Tk`.
- `scraper/` : Module contenant le moteur de navigation et d'extraction de données.
  - `engine.py` : Contient la classe `ChromiumScraper` pilotant Playwright.
- `doc/` : Dossier contenant la documentation du projet.
- `chromium_session/` : (Généré automatiquement) Dossier de profil contenant les cookies et le cache de Playwright.

## 2. Technologies et Bibliothèques Utilisées

- **Tkinter** : Bibliothèque GUI standardisée de Python pour créer l'interface. Utilisée avec sa surcouche `ttk` pour un rafraîchissement visuel.
- **Playwright (Async API)** : Moteur d'automatisation de test / scraping utilisé pour instancier et piloter Chromium.
- **Asyncio** : Bibliothèque standard Python pour exécuter le code asynchrone exigé par Playwright (gestion des temps d'attente d'E/S réseau sans bloquer les autres processus).
- **Threading** : Bibliothèque standard Python pour isoler la boucle asynchrone du scraping sur un thread séparé (Worker Thread), afin de ne pas bloquer la boucle d'événements principale du thread de l'IHM (Main Thread).

## 3. Détails d'implémentation

### 3.1. Gestion Concurrente (IHM + Asynchrone)
La librairie `Playwright` dans sa version `async` requiert une boucle d'évènements `asyncio.run()`. Si cette boucle tourne dans le thread principal, `Tkinter` (qui possède sa propre fonction bloquante `mainloop()`) va se geler (freeze).

**Solution :**
Dans `app.py`, la méthode `start_scraping()` lance un thread de la manière suivante :
```python
thread = threading.Thread(target=self._run_async_scraper, args=(config,), daemon=True)
thread.start()
```
Ce thread secondaire accueille la boucle `asyncio` liée à Playwright.

### 3.2. Transmission des Logs
Afin que le thread du scraper asynchrone puisse écrire dans la fenêtre Tkinter (thread principal) sans provoquer de conditions de course (Race Conditions), une fonction `log_callback` (`self.log` dans `app.py`) est passée en argument au moteur de scraping. Tkinter est nativement _Thread-Safe_ pour des opérations basiques d'insertion de texte (`Text.insert()`).

### 3.3. Contournement Anti-Bot (Playwright)
La classe `ChromiumScraper` (`scraper/engine.py`) implémente plusieurs mécanismes natifs pour contourner les WAF (Web Application Firewalls) :

1.  **Lancement Persistant :**
    ```python
    await p.chromium.launch_persistent_context(user_data_dir="./chromium_session", ...)
    ```
    L'utilisation d'un `user_data_dir` simule le comportement naturel d'un utilisateur régulier qui sauvegarde son historique et ses cookies au lieu de relancer une session totalement vierge et suspecte.

2.  **Drapeaux (Flags) Chromium :**
    ```python
    args=["--disable-blink-features=AutomationControlled"]
    ```
    Désactive un marqueur interne du moteur Blink signalant que l'instance est contrôlée de façon programmatique.

3.  **Spoofing Javascript du `navigator.webdriver` :**
    ```python
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    ```
    Modifie les propriétés JS du navigateur avant chaque chargement de document web (inject script), écrasant le booléen `true` qui dénoncerait la présence d'un driver automatisé.

## 4. Évolutivité
Pour étendre le projet, il convient d'ajouter de nouvelles méthodes dans la classe `ChromiumScraper` (`scraper/engine.py`) correspondantes aux interactions spécifiques envisagées (ex: `await page.click('#login-btn')`, `await page.fill('input[name="user"]', 'test')`).
