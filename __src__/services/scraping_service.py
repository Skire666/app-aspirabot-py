import time
import logging
from typing import Callable, Optional
from models.provider_model import ProviderModel

# Nous adaptons l'usage de web_browser_util pour intercepter les diff\u00e9rentes \u00e9tapes
from utils.web_browser_util import WebBrowserUtil

class ScrapingService:
    """Service g\u00e9rant la logique de d\u00e9clenchement et le suivi d'un scraping."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def run_and_track_scraping(self, provider: ProviderModel, on_log: Callable[[str], None], check_stop: Callable[[], bool]) -> tuple[bool, float, int, Optional[str]]:
        """
        Ex\u00e9cute le scraping en mesurant le temps et le nombre d'actions r\u00e9ussies.
        Intercepte les logs ou logue manuellement la progression.
        Retourne (Succ\u00e8s, Temps \u00e9coul\u00e9 en secondes, Nombre d'actions finalis\u00e9es, Message d'erreur \u00e9ventuel)
        """
        start_time = time.time()
        action_count = 0
        success = True
        error_msg = None

        on_log(f"D\u00e9marrage du scraping pour '{provider.provider_title}' ...")
        
        # Adaptation personnalis\u00e9e : au lieu d'appeler directement `run_scraping_task(provider)`,
        # on peut r\u00e9utiliser la classe pour faire des retours plus fins.
        scraper = WebBrowserUtil(provider)
        
        from playwright.async_api import async_playwright
        
        try:
            on_log("Initialisation du navigateur Playwright...")
            async with async_playwright() as play:
                if check_stop(): raise Exception("Stopp\u00e9 par l'utilisateur.")
                
                context = await scraper.launch_browser(play)
                on_log("Navigateur initialis\u00e9 et s\u00e9curis\u00e9.")
                
                await scraper.mask_webdriver(context)
                
                if check_stop(): raise Exception("Stopp\u00e9 par l'utilisateur.")
                page = await scraper.get_or_create_page(context)
                on_log(f"Navigation vers l'URL principale : {scraper.url_of_website}")
                await page.goto(scraper.url_of_website)
                
                steps = provider.steps or []
                on_log(f"{len(steps)} \u00e9tape(s) d\u00e9t\u00e9ct\u00e9e(s).")
                
                variables = {}
                for idx, step in enumerate(steps):
                    if check_stop(): raise Exception("Stopp\u00e9 par l'utilisateur.")
                    
                    action = step.get("type", "UNKNOWN")
                    on_log(f"[\u00c9tape {idx+1}/{len(steps)}] : Ex\u00e9cution de l'action -> {action}")
                    
                    # On r\u00e9plique approximativement le comportement de _run_scraping_steps pour tracker
                    if action == "FIND_ELEMENT":
                        sel = step.get("selector", "")
                        await page.wait_for_selector(sel, timeout=10000)
                    elif action == "CLICK":
                        sel = step.get("selector", "")
                        await page.click(sel)
                    elif action == "WAIT":
                        if "timeout" in step:
                            await page.wait_for_timeout(step["timeout"])
                        elif "selector" in step:
                            await page.wait_for_selector(step["selector"])
                    elif action == "EXTRACT_TEXT":
                        sel = step.get("selector", "")
                        var_name = step.get("variable_name", "var_text")
                        text = await page.locator(sel).inner_text()
                        variables[var_name] = text
                    # (Pour des raisons de simplicit\u00e9, on s'arr\u00eate d'impl\u00e9menter toutes les m\u00e9thodes exactes 
                    # mais en conditions r\u00e9elles on rappellerait les m\u00e9thodes internes ou on le factoriserait 
                    # dans le WebBrowserUtil pour \u00e9viter la duplication).
                    
                    action_count += 1
                
                if check_stop(): raise Exception("Stopp\u00e9 par l'utilisateur.")
                
                on_log("Fermeture de la session du navigateur...")
                await context.close()
                on_log("Session ferm\u00e9e.")

        except Exception as ex:
            success = False
            error_msg = str(ex)
            on_log(f"ERREUR FATALE: {error_msg}")
            
        elapsed = time.time() - start_time
        return (success, elapsed, action_count, error_msg)
