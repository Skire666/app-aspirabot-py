"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
"""

from dataclasses import dataclass


@dataclass
class StepScrappingModel:
    """Represents one executable step in a scraping workflow."""
