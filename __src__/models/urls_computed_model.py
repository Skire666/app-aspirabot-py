"""Result model for the URL comparison algorithm in the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class UrlsComputedModel:
    """Result of comparing input and output URL sets in a Discover project.

    Counts are stored as plain integers so the full URL lists do not stay in
    memory after computation.  The caller of ``compute_new_launches`` owns the
    lists and they are freed as soon as the caller's frame returns.

    Attributes:
        input_total_count: Total number of input URLs including duplicates.
        output_total_count: Total number of output URLs including duplicates.
        output_unique_count_stored: Number of distinct output URLs, precomputed
            from the output set during ``compute_new_launches``.
        new_entries: URLs present in the input but absent from the output,
            mapped to how many times each appears in the input.
        existing_entries: URLs already present in the output,
            mapped to how many times each appears there.
    """

    input_total_count: int = 0
    output_total_count: int = 0
    output_unique_count_stored: int = 0
    input_entries: dict[str, int] = field(default_factory=dict)
    output_entries: dict[str, int] = field(default_factory=dict)
    new_entries: dict[str, int] = field(default_factory=dict)

    @property
    def new_url_count(self) -> int:
        """Total number of distinct new URLs to be added."""
        return len(self.new_entries)

    @property
    def existing_url_count(self) -> int:
        """Number of IN URLs that were already present in the output."""
        return len(self.input_entries) - len(self.new_entries)

    @property
    def input_unique_count(self) -> int:
        """Number of distinct input URLs."""
        return len(self.input_entries)

    @property
    def input_duplicate_count(self) -> int:
        """Number of duplicate occurrences in the input list."""
        return self.input_total_count - self.input_unique_count

    @property
    def output_unique_count(self) -> int:
        """Number of distinct output URLs."""
        return self.output_unique_count_stored

    @property
    def output_duplicate_count(self) -> int:
        """Number of duplicate occurrences in the output list."""
        return self.output_total_count - self.output_unique_count_stored


# EOF
