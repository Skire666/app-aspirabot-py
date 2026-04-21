# Documentation Technique

## 1. Architecture du Système

L'application est développée en **Python 3** avec typage fort explicite, en respectant un pattern de conception MVC / MVVM afin de séparer la vue Tkinter, les données métier JSON et la logique asynchrone Playwright.

### Structure des dossiers (`__src__/`) :
- `main.py` : Point d'entrée de l'application. Initialise la configuration (`ConfigAspirabotModel`) et assemble la fenêtre Tkinter.
- `views/` : Composants `Tkinter` modulaires (`RootFrameView`, `MultiTabsPanel`, tab panels...) gérant uniquement la logique de rafraichissement de l'interface homme-machine.
- `view_models/` et `converters/` : Classes de conteneurs (`tk.StringVar`, etc.) servant d'intermédiaire pour éviter que `views` n'interagisse trop directement avec `models`, grâce à des méthodes de traduction de listes et d'états réactifs.
- `controllers/` : Logique d'orchestration (`UpdateController`, `ScrapingController`). Pilote les actions issues de l'UI (ex. suppression, sauvegarde) en sollicitant les repository ou services backend.
- `models/` : Entités métier pures abstraites (ex: `ProviderModel`) qui symbolisent la donnée pure.
- `repositories/` : Couche d'accès aux fichiers, spécialisée dans la lecture, l'écriture et la validation des schémas de données du format persistant JSON (vers ou depuis les objects `models`).
- `services/` : Contient `scraping_service.py` traitant l'intégration fine entre l'IHM et le moteur asynchrone `Playwright`.
- `utils/` : Outils partagés tels que la configuration du logger (via `queue.Queue` pour assurer le mode `Thread-Safe`) et la surcouche interne `WebBrowserUtil` utilisant Playwright.

## 2. Technologies et Bibliothèques Utilisées

- **Tkinter** : Bibliothèque GUI standardisée de Python pour créer l'interface. Utilisée avec sa surcouche `ttk` (`ttk.Notebook`, `ttk.Treeview`/`Listbox`...) pour un rendu plus moderne.
- **Playwright (Async API)** : Moteur d'automatisation et de requêtage pilotant Chromium, remplaçant performant à Selenium.
- **Asyncio** : Bibliothèque standard employée dans la boucle exclusive du worker thread de `WebBrowserUtil`.
- **Threading** : Maintient Tkinter (`mainloop`) actif dans le *Main Thread* alors qu'un *Worker Thread* s'occupe de résoudre le processus asynchrone `Playwright`.

## 3. Détails d'implémentation

### 3.1. Gestion Concurrente (IHM + Asynchrone)
La librairie `Playwright` en version `async` exige une boucle bloquante `asyncio.run()`, provoquant un gel visuel de `Tkinter` s'ils partagent le même Thread d'application.

**Pattern de résolution implémenté :**
Dans `services/scraping_service.py`, le contrôleur orchestre le fractionnement vers `threading.Thread(target=run_async_wrapper, daemon=True)`. Le traitement asynchrone tourne sur son îlot séparé, pendant que l'IHM affiche ses boutons "Loader".

### 3.2. Transmission des événements (Thread-Safe inter-thread)
1. **Les Logs Console :** Utilisent `queue.Queue` combiné à la méthode native `Tk.after(...)` (via `utils/logging_util.py` et `views/logs_panel_view.py`) pour vider correctement le buffer textuel de log généré par le moteur vers le champ `scrolledtext.ScrolledText`.
2. **Le Retour d'Opération (UI Update) :** Des fonctions de callback `ui_logger` et `on_finish` sont passées de la vue au service pour remonter la fin de traitement ou les retours contextuels sans jamais toucher nativement à l'état de la fenêtre depuis le mauvais thread.

### 3.3. Contournement Anti-Bot (Obfuscation avec Playwright)
Le singleton de contexte navigateur `WebBrowserUtil` (`utils/web_browser_util.py`) utilise nativement des astuces lorsque le `ProviderModel` le requiert (`automation_obfuscated`):
- **Drapeaux (Flags) Chromium :**
  Désactive l'option `--enable-automation` native souvent repérée par les capteurs d'empreinte.
- **Spoofing Javascript (`navigator.webdriver`) :**
  Injecte un payload javascript natif cachant l'objet `webdriver = true` permettant de berner CloudFlare, Datadome, ou autres WAF lors d'un test simple de reconnaissance de robot.

## 4. Évolutivité & Modèle de données (JSON)
L'intelligence du programme est centralisée dans la définition ouverte des étapes JSON. Ajouter une fonctionnalité de scraping ne demande pas de développer des méthodes Playwright sur mesure, mais d'enrichir le `Enum` `WorkflowAction` (dans les vues et modèles) et son interpréteur Python `_execute_step()` de `WebBrowserUtil` (exemples actuels : FIND_ELEMENT, CLICK, EXTRACT_TEXT...).
