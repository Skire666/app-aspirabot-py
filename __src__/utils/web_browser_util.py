import logging
from typing import Any
from playwright.async_api import async_playwright, BrowserContext, Page
from shared.constants import CTK_BROWSER
from models.provider_model import ProviderModel

# Récupération du logger pour ce fichier/module spécifique
logger = logging.getLogger(__name__)

class WebBrowserUtil:
    """
    Classe gérant l'automatisation du navigateur Chromium via Playwright.
    """
    _provider: ProviderModel
    _url: str
    _headless: bool

    def __init__(self, provider: ProviderModel) -> None:
        """
        Initialise le gestionnaire de navigateur web avec la configuration fournie.

        :param provider: Modèle de fournisseur (URL, mode headless, étapes).
        """
        self._provider = provider
        self._url = self._provider.url or "https://google.com" # TODO PCO : Constante
        self._headless = self._provider.browser_displayed # TODO PCO : si case cochée dans IHM adapter le chromium
        
        # Dossier local pour sauvegarder la session, cookies et cache
        self.user_data_dir = CTK_BROWSER.DEFAULT_USER_DATA_DIR

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
        logger.info(f"Navigation vers {self._url}")
        await page.goto(self._url)
        
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
                    start_domain = urllib.parse.urlparse(self._url).netloc
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
    """
    Fonction principale appelée par l'IHM qui exécute la classe de scraping.
    
    :param provider: Modèle pour le lancement du scraper.
    """
    scraper = WebBrowserUtil(provider)
    await scraper.start()
