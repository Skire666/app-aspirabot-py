# Projet de Web Scraping avec Playwright (Python)

But : Web scraping ou de l'automatisation de navigateur en utilisant Playwright avec Python.

## Prérequis

- [Python 3.8+](https://www.python.org/downloads/) installé sur votre machine.
- Un terminal (PowerShell, Command Prompt, bash, ou zsh).

## Installation et Configuration

Pour éviter de polluer votre système avec des dépendances globales, il est recommandé de tout installer dans un environnement virtuel.

*Ce mettre à la racine du projet (dossier 'src' visible)*

### 1. Créer l'environnement virtuel

Ouvrez votre terminal, placez-vous dans le dossier du projet, puis exécutez :

```bash
python -m venv venv
```

### 2. Activer l'environnement virtuel

L'activation varie selon votre système d'exploitation.

IMPORTANT :
Ce mettre à la racine du projet (dossier 'src' visible)


**Sur Windows (PowerShell / Invite de commandes) :**
```powershell
.\venv\Scripts\activate
```
*(Note : Si PowerShell bloque l'exécution des scripts avec un message d'erreur rouge, utilisez la commande `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` au préalable).*

**Sur macOS et Linux :**
```bash
source venv/bin/activate
```

Une fois activé, vous devriez voir `(venv)` apparaître au début de votre ligne de commande.

### 3. Installer les dépendances Python

Installez `playwright` (et autres paquets éventuels) à l'aide du fichier `requirements.txt` :

```bash
pip install -r './__src__/requirements.txt'
```

### 4. Installer les navigateurs pour Playwright

Contrairement à d'autres outils (comme Selenium ou BeautifulSoup), Playwright télécharge et utilise ses propres binaires pour garantir la compatibilité.

Pour installer uniquement **Chromium** (le moteur utilisé dans le code d'exemple) :
```bash
playwright install chromium
```

*(Si vous souhaitez installer tous les moteurs (Webkit, Firefox, Chromium), tapez juste `playwright install`)*.

### 5. Déployer avec toml

pip install -e .

*(N'oubliez pas le point . à la fin, qui signifie "installer le projet situé dans le répertoire courant" en mode "editable" -e).*
*Execution depuis n'importe où : Une fois installé dans le venv, vous pouvez lancer python __src__/main.py ou python -m __src__.main sans erreurs ModuleNotFoundError.*

---

## Utilisation

Pour lancer le script de scraping, assurez-vous que votre environnement virtuel est toujours activé `(venv)`, puis lancez :

```bash
python __src__/main.py
```

## Nettoyage du projet

```bash
python -m pip install pyclean
python -m pyclean ./ -v
```

Dossier généré :
./tmp_logs
./tmp_chromium_session
./user_providers
./user_brokens
