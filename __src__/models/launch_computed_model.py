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
            mapped to how many times each appears in the input.
        existing_entries: URLs already present in the output,
            mapped to how many times each appears there.
    """

    input_urls: list[str] = field(default_factory=list)
    output_urls: list[str] = field(default_factory=list)
    new_entries: dict[str, int] = field(default_factory=dict)
    existing_entries: dict[str, int] = field(default_factory=dict)

    @property
    def new_url_count(self) -> int:
        """Total number of distinct new URLs to be added."""
        return len(self.new_entries)

    @property
    def existing_url_count(self) -> int:
        """Total number of distinct URLs that already exist in the output."""
        return len(self.existing_entries)

    @property
    def input_total_count(self) -> int:
        """Total number of input URLs including duplicates."""
        return len(self.input_urls)

    @property
    def input_unique_count(self) -> int:
        """Number of distinct input URLs."""
        return len(self.new_entries) + len(self.existing_entries)

    @property
    def input_duplicate_count(self) -> int:
        """Number of duplicate occurrences in the input list."""
        return self.input_total_count - self.input_unique_count

    @property
    def output_total_count(self) -> int:
        """Total number of output URLs including duplicates."""
        return len(self.output_urls)

    @property
    def output_unique_count(self) -> int:
        """Number of distinct output URLs."""
        return len(set(self.output_urls))

    @property
    def output_duplicate_count(self) -> int:
        """Number of duplicate occurrences in the output list."""
        return self.output_total_count - self.output_unique_count


# EOF
