# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class ExtractTextHtmlEnum(Enum):
    """Enumerates the modes for extracting text from an element in an EXTRACT_TEXT step."""

    E_UNSET = "UNSET"
    E_INNER_TEXT = "innerText"
    E_TEXT_CONTENT = "textContent"
    E_OUTER_HTML = "outerHTML"
    E_INNER_HTML = "innerHTML"
    E_INPUT_VALUE = "value"
    E_UNKNOWN = "UNKNOWN"


# EOF
