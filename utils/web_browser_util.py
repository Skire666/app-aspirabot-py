import asyncio
import logging
from typing import Any, Dict
from playwright.async_api import async_playwright, BrowserContext, Page
from constants import CTK_BROWSER

# Récupération du logger pour ce fichier/module spécifique
logger = logging.getLogger(__name__)

class WebBrowserUtil:
    """
    Classe gérant l'automatisation du navigateur Chromium via Playwright.
    """
    _config: Dict[str, Any]
    _url: str
    _headless: bool

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialise le gestionnaire de navigateur web avec la configuration fournie.

        :param config: Paramètres du gestionnaire (URL, mode headless, etc.).
        """
        self._config = config
        self._url = self._config.get("url", "https://google.com") # TODO PCO : Constante
        self._headless = self._config.get("headless", False) # TODO PCO : si case cochée dans IHM adapter le chromium
        
        # Dossier local pour sauvegarder la session, cookies et cache
        self.user_data_dir = CTK_BROWSER.USER_DATA_DIR

    async def start(self) -> None:
        """Lance l'ensemble du processus de scraping de manière asynchrone."""
        logger.info("Démarrage du moteur asynchrone Playwright...")
        
        async with async_playwright() as playwright_instance:
            context = await self._launch_browser(playwright_instance)
            await self._mask_webdriver(context)
            
            page = await self._get_or_create_page(context)
            await self._run_scraping_steps(page)
            
            logger.info("Fermeture de la session sécurisée.")
            await context.close()

    async def _launch_browser(self, playwright_instance: Any) -> BrowserContext:
        """
        Lance le contexte navigateur persistant (conserve cookies et cache).
        
        :param playwright_instance: Instance Playwright active.
        :return: Le contexte du navigateur ouvert.
        """
        logger.info(f"Lancement Chromium Persistant (headless={self._headless})...")
        return await playwright_instance.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self._headless, # True pour exécution invisible
            args=["--disable-blink-features=AutomationControlled"] # Réduit détection bot
        )

    async def _mask_webdriver(self, context: BrowserContext) -> None:
        """
        Masque le flag navigator.webdriver pour réduire la détection par les bots.
        
        :param context: Le contexte du navigateur actif.
        """
        
        # TODO PCO : si case cochée dans IHM adapter le chromium
        logger.debug("Masquage du flag webdriver (Anti-Bot)...")
        script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        await context.add_init_script(script)

    async def _get_or_create_page(self, context: BrowserContext) -> Page:
        """
        Récupère l'onglet actif ou en ouvre un nouveau s'il n'y en a pas.
        
        :param context: Le contexte du navigateur actif.
        :return: L'objet Page pour interagir.
        """
        pages = context.pages
        if len(pages) > 0:
            return pages[0]
        
        logger.debug("Ouverture d'un nouvel onglet...")
        return await context.new_page()

    async def _run_scraping_steps(self, page: Page) -> None:
        """
        Exécute la séquence d'actions de scraping sur la page cible.
        
        :param page: L'objet Page asynchrone manipulé par Playwright.
        """
        # TODO PCO : faire des steps que l'algorithme applique, penser au wysiwyg
        logger.info(f"Navigation vers {self._url}")
        await page.goto(self._url)
        
        logger.info("Récupération du titre de la page...")
        title = await page.title()
        logger.info(f"Résultat - Titre trouvé : '{title}'")
        
        # Pause simulant une activité utilisateur (pour éviter les détections)
        logger.info("Pause de 3 secondes pour simuler une action...")
        await asyncio.sleep(3)


async def run_scraping_task(config: Dict[str, Any]) -> None:
    """
    Fonction principale appelée par l'IHM qui exécute la classe de scraping.
    
    :param config: Configuration pour le lancement du scraper.
    """
    scraper = WebBrowserUtil(config)
    await scraper.start()
