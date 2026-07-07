"""URL transformation helpers shared across layers.

Pure-Python utilities with no Tkinter dependency — safe to import from any layer.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import re

from shared.exception_util import EmptyStringError

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def transformer_url(
    url: str, transformer_url_regexp: str, transformer_url_base: str, transformer_url_trailing_slash: bool
) -> str:
    """Rewrite *url* by extracting a regexp capture and re-basing it under a new prefix.

    Args:
        url: The source URL to transform.
        transformer_url_regexp: Regexp applied to *url*. Its first capturing group is
            kept, or the whole match when the pattern has no group.
        transformer_url_base: Prefix prepended in front of the captured part.
        transformer_url_trailing_slash: When True, ensures the result ends with a '/'.

    Returns:
        The transformed URL, or the original *url* unchanged when the pattern is
        invalid or does not match.

    Raises:
        AspirabotBaseError: If *transformer_url_regexp* or *transformer_url_base* is empty.
    """
    if not transformer_url_regexp.strip() or not transformer_url_base.strip():
        raise EmptyStringError()
    try:
        match = re.search(transformer_url_regexp, url)
    except re.error:
        return url
    if not match:
        return url
    captured = match.group(1) if match.groups() else match.group(0)
    result = transformer_url_base + captured
    if transformer_url_trailing_slash and not result.endswith("/"):
        result += "/"
    return result


# EOF
