"""Presenter wiring ExecutorView to ScrapingService.

The presenter starts the workflow in a daemon thread, forwards step outcomes
to the view (journal + progress), and exposes cancellation through threading
events. No business logic lives here — only orchestration.

Example:
    >>> presenter = ScrapingPresenter(panel, service_scraping, service_scenario)
    >>> presenter.load_scenario("abc123")
    >>> # The Lancer button in the view then drives the rest.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from views.scraping_view import ScrapingView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScrapingPresenter:
    def __init__(self, view: ScrapingView) -> None:
        self._view = view
        self._logging = logging.getLogger(__name__)
