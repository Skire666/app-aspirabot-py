# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from views.executor_view import ExecutorView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ExecutorPresenter:
    def __init__(self, view: ExecutorView) -> None:
        self._view = view
        self._logging = logging.getLogger(__name__)
