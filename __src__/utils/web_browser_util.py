"""Module utilitaire pour l'automatisation du navigateur web.

Ce module gère l'interaction avec le navigateur Chromium via la bibliothèque
asynchrone Playwright. Il fournit la classe `WebBrowserUtil` capable d'imiter
un comportement utilisateur pour le scraping, tout en réduisant les risques
de détection (anti-bot) et en maintenant la persistance de session.

Exemples d'utilisation:
    >>> import asyncio
    >>> from models.provider_model import ProviderModel
    >>> from utils.web_browser_util import run_scraping_task
    >>> provider = ProviderModel("data/config.json")
    >>> asyncio.run(run_scraping_task(provider))
"""

import logging
from typing import Any
from playwright.async_api import async_playwright, BrowserContext, Page
from shared.constants import CTK_BROWSER
from models.provider_model import ProviderModel

# Récupération du logger pour ce fichier/module spécifique
logger = logging.getLogger(__name__)

class WebBrowserUtil:
    """Classe gérant l'automatisation du navigateur Chromium via Playwright.

    Cette classe encapsule la logique d'initialisation de Playwright, le lancement
    d'un contexte persistant (pour sauvegarder les cookies/cache) et l'exécution
    séquentielle des étapes de scraping définies dans le ProviderModel.

    Attributes:
        _provider (ProviderModel): Le modèle de configuration du scraping à utiliser.
        url_of_website (str): L'URL cible principale pour lancer le processus.
        _headless (bool): Détermine si le navigateur s'exécute en arrière-plan (True) ou s'il est visible.
        user_data_dir (str): Le chemin vers le répertoire stockant la session Chromium du bot.
    """
    _provider: ProviderModel
    url_of_website: str
    _headless: bool

    def __init__(self, provider: ProviderModel) -> None:
        """Initialise le gestionnaire de navigateur web avec la configuration fournie.

        Args:
            provider (ProviderModel): Modèle contenant l'URL, le mode d'affichage, et les étapes.

        Raises:
            ValueError: Si le provider fourni n'est pas valide ou mal initialisé.
            
        Exemples d'utilisation:
            >>> provider = ProviderModel("config.json")
            >>> browser_util = WebBrowserUtil(provider)
        """
        if not provider:
            raise ValueError("Un ProviderModel valide est requis.")
        
        self._provider = provider
        self.url_of_website = self._provider.url or "https://google.com" # TODO PCO : Constante
        self._headless = not self._provider.browser_displayed # Inverse logique: affiché dans GUI == not headless
        
        # Dossier local pour sauvegarder la session, cookies et cache
        self.user_data_dir = CTK_BROWSER.DEFAULT_USER_DATA_DIR

    async def start(self) -> None:
        """Lance l'ensemble du processus de scraping de manière asynchrone.

        Cette méthode est le point d'entrée principal. Elle initialise Playwright,
        ouvre le navigateur en mode persistant, masque le flag webdriver, ouvre
        la page cible et lance l'exécution des étapes.
        
        Returns:
            None
        """
        logger.info("Démarrage du moteur asynchrone Playwright...")
        
        async with async_playwright() as playwright_instance:
            context = await self.launch_browser(playwright_instance)
            
            if self._provider.automation_obfuscated:
                await self.mask_webdriver(context)
            
            page = await self.get_or_create_page(context)
            await self._run_scraping_steps(page)
            
            logger.info("Fermeture de la session sécurisée.")
            await context.close()

    async def launch_browser(self, playwright_instance: Any) -> BrowserContext:
        """Lance le contexte navigateur persistant Chromium.
        
        Le contexte persistant garantit que les sessions, cookies et le cache 
        sont réutilisés lors des lancements ultérieurs, ce qui peut empêcher 
        la réauthentification ou limiter la détection des comportements de bot.

        Args:
            playwright_instance (Any): Une instance validée du gestionnaire `async_playwright()`.

        Returns:
            BrowserContext: Le contexte de navigateur persistant actif.
            
        Raises:
            Exception: Si l'instance de Playwright ne peut pas lancer Chromium.
        """
        logger.info(f"Lancement Chromium Persistant (headless={self._headless})...")
        return await playwright_instance.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled"] # Réduit détection bot
        )

    async def mask_webdriver(self, context: BrowserContext) -> None:
        """Masque le flag `navigator.webdriver` pour réduire la détection.
        
        Injecte un script JavaScript s'exécutant à chaque initialisation de page
        pour redéfinir la propriété `webdriver` comme non définie, contournant
        les protections anti-bot basiques.

        Args:
            context (BrowserContext): Le contexte de navigateur concerné par l'injection.

        Returns:
            None
        """
        logger.debug("Masquage du flag webdriver (Anti-Bot)...")
        script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        await context.add_init_script(script)

    async def get_or_create_page(self, context: BrowserContext) -> Page:
        """Récupère l'onglet actif ou en ouvre un nouveau.
        
        Args:
            context (BrowserContext): Le contexte lié à la session navigateur en cours.

        Returns:
            Page: L'objet de page validée prête à recevoir des commandes.
        """
        pages = context.pages
        if len(pages) > 0:
            return pages[0]
        
        logger.debug("Ouverture d'un nouvel onglet...")
        return await context.new_page()

    async def _run_scraping_steps(self, page: Page) -> None:
        """Exécute la séquence d'actions de scraping sur la page cible.
        
        Navigue d'abord vers l'URL configurée, puis itère sur toutes
        les étapes fournies par le `ProviderModel` (cliques, attentes, lectures).

        Args:
            page (Page): L'objet Page asynchrone manipulé par Playwright.

        Returns:
            None
        """
        logger.info(f"Navigation vers {self.url_of_website}")
        
        try:
            await page.goto(self.url_of_website)
        except Exception as e:
            logger.error(f"Erreur de navigation vers {self.url_of_website} : {e}")
            return
            
        steps = self._provider.steps
        if not steps:
            logger.info("Aucune étape à exécuter.")
            return

        variables = {}
        for idx, step in enumerate(steps):
            action = step.get("type")
            logger.info(f"Exécution de l'étape {idx + 1}: {action}")
            
            try:
                if action == "FIND_ELEMENT":
                    sel = step.get("selector", "")
                    await page.wait_for_selector(sel, timeout=10000)
                    logger.info(f"Element {sel} trouvé.")
                    
                elif action == "CLICK":
                    sel = step.get("selector", "")
                    await page.click(sel)
                    logger.info(f"Clic sur {sel}.")
                    
                elif action == "DOWNLOAD_IMAGE":
                    images = await page.locator("img").all()
                    largest = None
                    max_area = 0
                    for img in images:
                        box = await img.bounding_box()
                        if box:
                            area = box["width"] * box["height"]
                            if area > max_area:
                                max_area = area
                                largest = img
                    if largest:
                        src = await largest.get_attribute("src")
                        logger.info(f"Plus grande image a télécharger: {src}")
                        import urllib.parse
                        if src:
                            src_url = urllib.parse.urljoin(page.url, src)
                            logger.info(f"-> A télécharger: {src_url}")
                            # TODO PCO : Downloading can be implemented with requests or playwright download
                    else:
                        logger.info("Aucune image trouvée.")
                        
                elif action == "WAIT":
                    if "timeout" in step:
                        ms = step["timeout"]
                        await page.wait_for_timeout(ms)
                        logger.info(f"Attente de {ms}ms terminée.")
                    elif "selector" in step:
                        sel = step["selector"]
                        await page.wait_for_selector(sel)
                        logger.info(f"Attente du sélecteur {sel} terminée.")
                        
                elif action == "EXTRACT_TEXT":
                    sel = step.get("selector", "")
                    var_name = step.get("variable_name", "var1")
                    text = await page.locator(sel).inner_text()
                    variables[var_name] = text
                    logger.info(f"Texte extrait pour {var_name} : {text}")
                    
                elif action == "CLOSE_OTHER_TABS":
                    import urllib.parse
                    start_domain = urllib.parse.urlparse(self.url_of_website).netloc
                    context = page.context
                    for p in context.pages:
                        if p != page:
                            p_domain = urllib.parse.urlparse(p.url).netloc
                            if p_domain != start_domain:
                                await p.close()
                    logger.info("Onglets fermés hors du domaine.")
                    
            except Exception as e:
                logger.error(f"Erreur à l'étape {idx + 1} ({action}): {e}")


async def run_scraping_task(provider: ProviderModel) -> None:
    """Fonction principale pour exécuter la tâche de scraping asynchrone.
    
    Instancie la classe `WebBrowserUtil` à partir d'un fournisseur
    et lance le proxy asynchrone complet. Principalement conçu pour 
    être invoqué depuis l'UI dans un thread asyncio dédié.

    Args:
        provider (ProviderModel): Modèle contenant les directives de scraping.

    Returns:
        None

    Exemples d'utilisation:
        >>> provider = ProviderModel("config.json")
        >>> asyncio.run(run_scraping_task(provider))
    """
    scraper = WebBrowserUtil(provider)
    await scraper.start()
