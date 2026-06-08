"""Result model for the URL comparison algorithm in the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class LaunchComputedModel:
    """Result of comparing input and output URL sets in a Discover project.

    Attributes:
        input_urls: All URLs extracted from the input JSON files.
        output_urls: All URLs extracted from the output JSON files.
        new_entries: URLs present in the input but absent from the output,
            paired with how many times each appears in the input.
        existing_entries: URLs already present in the output,
            paired with how many times each appears there.
    """

    input_urls: list[str] = field(default_factory=list)
    output_urls: list[str] = field(default_factory=list)
    new_entries: list[tuple[str, int]] = field(default_factory=list)
    existing_entries: list[tuple[str, int]] = field(default_factory=list)

    @property
    def new_url_count(self) -> int:
        """Total number of distinct new URLs to be added."""
        return len(self.new_entries)

    @property
    def existing_url_count(self) -> int:
        """Total number of distinct URLs that already exist in the output."""
        return len(self.existing_entries)


# EOF
