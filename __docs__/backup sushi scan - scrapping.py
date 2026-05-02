import time
import random
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# =========================
# CONFIGURATION (CONSTANTES)
# =========================

# URL de départ pour le scraping
START_URL = "https://sushiscan.net/spriggan-volume-1/"  

# Sélecteur CSS du bouton "next" pour passer à la page suivante
NEXT_BUTTON_SELECTOR = ".ch-next-btn"  # équivalent de : class="ch-next-btn"

# Sélecteur CSS pour les images à récupérer
IMAGE_SELECTOR = "img"  

# Attente initiale pour laisser la page se charger correctement (en secondes)
INITIAL_WAIT_STARTING = 10  

# Pause aléatoire minimum et maximum entre actions (simuler comportement humain)
LOOP_DELAY_MIN = 0.8  
LOOP_DELAY_MAX = 2.0  

# Paramètres pour le mouvement de souris simulé
MOUSE_MOVE_STEPS_MIN = 10  
MOUSE_MOVE_STEPS_MAX = 25  

# Paramètres pour le scroll aléatoire sur la page
SCROLL_MIN = 200  
SCROLL_MAX = 800  


# =========================
# FONCTIONS UTILITAIRES
# =========================

def human_delay(min_s=LOOP_DELAY_MIN, max_s=LOOP_DELAY_MAX):
    """
    Pause aléatoire pour simuler un comportement humain.
    Utilise random.uniform pour varier le temps entre actions.
    """
    time.sleep(random.uniform(min_s, max_s))


def get_largest_image(page):
    """
    Sélectionne l'image la plus grande affichée à l'écran.
    Récupère toutes les images via le sélecteur, puis calcule la surface de chaque image.
    Retourne le src de l'image ayant la plus grande surface.
    """
    images = page.query_selector_all(IMAGE_SELECTOR)

    max_area = 0
    best_src = None

    for img in images:
        try:
            # Récupération de la taille affichée (bounding box)
            box = img.bounding_box()
            if not box:
                continue

            area = box["width"] * box["height"]
            src = img.get_attribute("src")

            # Garder l'image avec la plus grande surface
            if src and area > max_area:
                max_area = area
                best_src = src
        except:
            continue

    return best_src


def download_image(context, page, url, filename, retries=3):
    """
    Télécharge une image via le réseau Playwright.
    
    Args:
        context: Playwright BrowserContext (pour conserver cookies/session)
        page: page principale (pour récupérer le referer et user-agent)
        url: URL de l'image
        filename: nom du fichier de sortie
        retries: nombre de tentatives si échec
    """
    for attempt in range(retries):
        try:
            # Utilisation du réseau du navigateur pour récupérer l'image
            response = context.request.get(
                url,
                headers={
                    "Referer": page.url,  # Referer = page actuelle
                    "User-Agent": page.evaluate("() => navigator.userAgent")  # Même user-agent
                }
            )
            if response.ok:
                with open(filename, "wb") as f:
                    f.write(response.body())
                print(f"✅ Téléchargé : {filename}")
                return True
            else:
                print(f"⚠️ HTTP {response.status}, tentative {attempt+1}")
        except Exception as e:
            print(f"⚠️ Erreur tentative {attempt+1}: {e}")
        time.sleep(1)

    print("❌ Échec téléchargement")
    return False


def click_next(page):
    """
    Clique sur le bouton 'next' de manière robuste.
    Méthodes utilisées :
        1. Click normal
        2. Click forcé (force=True)
        3. Click via JavaScript
    Retourne True si clic réussi, False sinon.
    """
    try:
        # Attente que le bouton existe dans le DOM
        page.wait_for_selector(NEXT_BUTTON_SELECTOR, timeout=5000)
        btn = page.query_selector(NEXT_BUTTON_SELECTOR)
        if not btn:
            print("❌ Bouton 'next' introuvable")
            return False

        # Scroll vers le bouton pour qu'il soit visible
        btn.scroll_into_view_if_needed()
        time.sleep(0.5)

        # Tentative 1 : click normal
        try:
            btn.click(timeout=3000)
            return True
        except:
            pass
        # Tentative 2 : click forcé
        try:
            btn.click(force=True, timeout=3000)
            return True
        except:
            pass
        # Tentative 3 : JS click direct
        page.evaluate(f"document.querySelector('{NEXT_BUTTON_SELECTOR}')?.click();")
        return True
    except Exception as e:
        print(f"❌ Erreur clic : {e}")
        return False


def handle_new_tabs_after_click(context, main_page, wait_time=1.0):
    """
    Vérifie si un nouvel onglet (popup) a été ouvert après un clic.
    Si oui, le ferme et remet le focus sur la page principale.

    Args:
        context: Playwright BrowserContext
        main_page: page principale
        wait_time: temps d'attente pour que le popup apparaisse
    """
    try:
        # Pages ouvertes avant le clic
        existing_pages = context.pages.copy()
        time.sleep(wait_time)
        # Pages après le clic
        current_pages = context.pages
        for page in current_pages:
            if page not in existing_pages:
                print("🧹 Popup détectée → fermeture")
                try:
                    page.close()
                except Exception as e:
                    print(f"⚠️ Erreur fermeture popup : {e}")
        # Revenir sur la page principale
        main_page.bring_to_front()
    except Exception as e:
        print(f"❌ Erreur gestion onglets : {e}")


# =========================
# SCRIPT PRINCIPAL
# =========================

with sync_playwright() as p:

    # Lancement du navigateur Chromium
    browser = p.chromium.launch(
        headless=False,  # True pour exécution invisible
        args=["--disable-blink-features=AutomationControlled"]  # Réduit détection bot
    )

    # Création d'une nouvelle session (conserve cookies et cache)
    context = browser.new_context()

    # Ouvre un nouvel onglet
    page = context.new_page()

    # Masque le flag webdriver pour réduire la détection bot
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # -------------------------
    # INITIALISATION
    # -------------------------
    print("🌐 Ouverture de la page...")
    page.goto(START_URL)

    print(f"⏳ Attente {INITIAL_WAIT_STARTING} secondes...")
    time.sleep(INITIAL_WAIT_STARTING)

    print("🔄 Rafraîchissement de la page...")
    page.reload()

    # Vérification URL après refresh
    if page.url == START_URL:
        print("✅ URL confirmée après refresh")
    else:
        print(f"⚠️ URL différente : {page.url}")

    counter = 1  # Compteur pour nommer les fichiers images

    # -------------------------
    # BOUCLE PRINCIPALE
    # -------------------------
    while True:
        # Pause aléatoire entre actions
        human_delay()

        # Scroll aléatoire pour simuler comportement humain
        page.mouse.wheel(0, random.randint(SCROLL_MIN, SCROLL_MAX))

        # Récupération de la plus grande image visible
        img_src = get_largest_image(page)
        if img_src:
            full_url = urljoin(page.url, img_src)
            filename = f"image_{counter:03d}.jpg"
            download_image(context, page, full_url, filename)
            counter += 1
        else:
            print("⚠️ Aucune image trouvée")

        # -------------------------
        # CLIC NEXT + GESTION POPUP
        # -------------------------
        if not click_next(page):
            print("⚠️ Impossible de cliquer sur next → fin boucle")
            break

        handle_new_tabs_after_click(context, page)