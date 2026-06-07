"""Computed result of comparing input URL values against output URL keys."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class LaunchComputedModel:
    """Holds the result of matching input values against output URL keys.

    Produced by :meth:`~services.discover_service.DiscoverService.compute_profile_list`
    after applying the two normalisation regexps.

    Attributes:
        input_entries: All raw ``values`` strings collected from the input
            :class:`~models.scraping_context_model.ExtractedData` files.
        output_entries: All URL keys collected from the output
            :class:`~models.scraping_context_model.ExtractedData` files.
        new_items: Tuples of (raw_value, occurrence_count) for input values
            whose normalised form was **not** found in the output set.
            These are the entries to add to the launch profile.
        already_found_items: Tuples of (raw_value, occurrence_count) for input
            values whose normalised form **was** already present in the output.
    """

    input_entries: list[str] = field(default_factory=list)
    output_entries: list[str] = field(default_factory=list)
    new_items: list[tuple[str, int]] = field(default_factory=list)
    already_found_items: list[tuple[str, int]] = field(default_factory=list)

    def get_new_urls(self) -> list[str]:
        """Return the deduplicated list of new URLs to add, without occurrence counts.

        Returns:
            Unique URL strings that are absent from the output set.
        """
        seen: set[str] = set()
        result: list[str] = []
        for url, _ in self.new_items:
            if url not in seen:
                seen.add(url)
                result.append(url)
        return result


# EOF
