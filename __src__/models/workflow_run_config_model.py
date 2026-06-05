"""Immutable configuration snapshot for a single scraping workflow run.

Groups the three caller-supplied values that define *what* to scrape and
*where* to write results.  Separates source/export concerns from the
threading signals and callbacks defined in ``WorkflowRunHandlers``.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkflowRunConfigModel:
    """Immutable configuration for a single scraping workflow run.

    All fields are optional so callers that do not use URL injection or file
    export can omit them without breaking the interface.

    Attributes:
        url_source_type: One of ``"manual"``,  ``"folder"``, or
            ``""`` to disable URL injection entirely.
        url_source_value: Matching value for the given type — a list of
            explicit URLs (manual) or a path string (folder).
            Ignored when ``url_source_type`` is empty.
        export_folder: Absolute path of the output directory where downloaded
            files and extracted data are written.  An empty string means no
            export folder is configured.
    """

    url_source_type: str = ""
    url_source_value: list[str] | str | None = None
    export_folder: str = ""
    # Sort order for folder/json sources — matches UrlSortOrderEnum.value strings.
    url_sort_order: str = ""
    # Optional URL to navigate to before running steps; empty string disables warmup.
    warmup_url: str = ""


# EOF
