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

from interfaces.i_urls_source_model import IUrlsSourceModel

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkflowRunConfigModel:
    """Immutable configuration for a single scraping workflow run.

    All fields are optional so callers that do not use URL injection or file
    export can omit them without breaking the interface.

    Attributes:
        urls_source_provider: An instance of a class implementing ``IUrlsSourceModel``.
        export_folder: Absolute path of the output directory where downloaded
            files and extracted data are written.  An empty string means no
            export folder is configured.
    """

    urls_source_provider: IUrlsSourceModel
    export_folder: str
    # Optional URL to navigate to before running steps; empty string disables warmup.
    warmup_url: str


# EOF
