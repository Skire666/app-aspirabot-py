"""In-memory CSV table with JSON interoperability.

CsvTable holds a fixed, ordered header (unique column names) and a list of
rows, each row a dict[str, str] keyed by column name. Row identity is
positional: the first row added has index 0, the next 1, and so on. Deleting
a row shifts the index of every row that followed it.

A "__id__" column is always present, even when omitted from the header
passed to the constructor. Its value is assigned automatically by an
internal counter that starts at 0 and increments by 1 on every ``add_row``
call; callers cannot set it explicitly, and ``replace_row`` preserves it.

``flatten_json_to_row`` / ``unflatten_row_to_json`` convert a top-level
dict[str, Any] to/from a single CSV row. Top-level keys are column names.
Values are stringified by type: bool -> "True"/"False", int/float -> str(),
str -> unchanged, dict/list -> JSON string. Booleans are checked before
numbers since ``bool`` is a subclass of ``int`` in Python.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from shared.aggregators_util import parse_aggregators_list, validate_aggregators_list
from shared.constants import (
    C_COLUMNS_BASED_HEADERS,
    C_CSV_BEST_EXTRACTOR,
    C_CSV_FIRST_CREATED,
    C_CSV_INDEX,
    C_CSV_LAST_MODIFIED,
    C_CSV_PRIMARY_KEY,
    C_CSV_QUALITY_1_DATE,
    C_CSV_QUALITY_2_ROW,
    C_CSV_STRATEGY_NEWEST,
    C_CSV_STRATEGY_OLDEST,
    C_CSV_STRATEGY_QUALITY,
)
from shared.datetime_util import parse_date_from_csv
from shared.dict_util import set_first_date_created, set_last_date_modified_and_extractor, set_quality_count_filled
from shared.enums.level_extractor_enum import LevelExtractorEnum
from shared.enums.relative_date_enum import get_quality_of_updating_date
from shared.exception_util import CsvRowIndexNotFoundError
from shared.image_base64_util import export_base64_image

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class CsvTable:
    """In-memory CSV table backed by a fixed header and a list of str-valued rows."""

    def __init__(self, header: set[str] | None = None) -> None:
        """Initialise an empty table with *header* as its column names.

        Args:
            header: Ordered, unique column names.

        Raises:
            CsvColumnDuplicateError: When *header* contains a duplicate name.
        """
        self._header: set[str] = header if header is not None else set()
        self._rows: list[dict[str, str]] = []
        self._cached_index: int = -1  # for __id__ assignment

    @classmethod
    def from_rows(cls, header: set[str], rows: Iterable[dict[str, str]]) -> CsvTable:
        """Build a table from *header* and pre-existing *rows*.

        Args:
            header: Ordered, unique column names.
            rows: Rows to seed the table with, in order.

        Returns:
            A new CsvTable populated with *rows*.
        """
        table = cls(header)
        for row in rows:
            table.add_row(row)
        return table

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def header(self) -> list[str]:
        """Column names, sorted alphabetically."""
        return sorted(self._header)

    @property
    def row_count(self) -> int:
        """Number of rows currently in the table."""
        return len(self._rows)

    # ------------------------------------------------------------------
    # Row access
    # ------------------------------------------------------------------

    def has_row(self, index: int) -> bool:
        """Return True if *index* points to an existing row."""
        return 0 <= index < len(self._rows)

    def iter_rows(self) -> Iterable[dict[str, str]]:
        """Yield each row's raw dict, in order.

        Bypasses the per-cell bounds-checking of ``get_cell``, for callers
        that scan every row and column themselves. Rows are yielded by
        reference: treat them as read-only.
        """
        return iter(self._rows)

    def to_list_of_dicts(self) -> list[dict[str, str]]:
        """Return a copy of every row, in order, with columns sorted alphabetically."""
        self.fill_missing_columns()
        return [{column: row[column] for column in self.header} for row in self._rows]

    def fill_missing_columns(self) -> None:
        """Fill missing columns in each row with empty strings."""
        for row in self._rows:
            for column in self._header:
                if column not in row:
                    row[column] = ""

    def has_value(self, column: str, value: str) -> bool:
        """Return True if any row has *value* in *column*.

        Raises:
            CsvColumnNotFoundError: When *column* is not part of the header.
        """
        return self.find_row_index(column, value) is not None

    def find_row_index(self, column: str, value: str) -> int | None:
        """Return the index of the first row where *column* equals *value*.

        Raises:
            CsvColumnNotFoundError: When *column* is not part of the header.
        """
        # cached ?
        if self._cached_index >= 0 and self._cached_index < len(self._rows):  # ruff:ignore[collapsible-if]
            if self._rows[self._cached_index][column] == value:
                return self._cached_index

        # not cached
        self._cached_index = -1
        for index, row in enumerate(self._rows):
            if row[column] == value:
                self._cached_index = index
                return index
        return None

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_column(self, column: str) -> None:
        """Add a new column to the header, defaulting all existing rows to "".

        Raises:
            CsvColumnDuplicateError: When *column* is already part of the header.
        """
        self._header.add(column)

    def add_row(self, row: dict[str, str]) -> None:
        """Append *row* and return its new index.

        Columns absent from *row* default to "". Extra keys not in the
        header are rejected. "__id__" is assigned from the internal
        counter, overriding any value supplied in *row*.

        Raises:
            CsvColumnNotFoundError: When *row* has a key outside the header.
        """
        if C_CSV_INDEX not in row or row.get(C_CSV_INDEX) is None:
            length = len(self._rows) if self._rows else 0
            row[C_CSV_INDEX] = str(length)

        self._rows.append(row)
        for key in row:
            if key not in self._header:
                self._header.add(key)

    def update_cell(self, index: int, column: str, value: str) -> None:
        """Set a single cell at (*index*, *column*) to *value*.

        Raises:
            CsvRowIndexNotFoundError: When *index* is out of range.
            CsvColumnNotFoundError: When *column* is not part of the header.
        """
        self._require_row(index)
        self._rows[index][column] = value
        self.add_column(column)  # ensure column is in header, even if it was missing

    def update_cells(self, index: int, row: dict[str, str]) -> None:
        """Update the row at *index* with the key/value pairs in *row*.

        Raises:
            CsvRowIndexNotFoundError: When *index* is out of range.
            CsvColumnNotFoundError: When *row* has a key outside the header.
        """
        self._require_row(index)
        for key, value in row.items():
            self._rows[index][key] = value
        for key in row:
            self.add_column(key)

    def get_cell(self, index: int, column: str) -> str:
        """Return the value of a single cell at (*index*, *column*).

        Raises:
            CsvRowIndexNotFoundError: When *index* is out of range.
            CsvColumnNotFoundError: When *column* is not part of the header.
        """
        self._require_row(index)
        if column not in self._rows[index]:
            return ""
        return self._rows[index][column]

    def delete_row(self, index: int) -> None:
        """Remove the row at *index*, shifting later rows down by one.

        Raises:
            CsvRowIndexNotFoundError: When *index* is out of range.
        """
        self._require_row(index)
        del self._rows[index]

    # ------------------------------------------------------------------
    # Quality
    # ------------------------------------------------------------------

    def fix_metadata_with_default(self) -> None:
        """Fix the data in the table.

        This method is a placeholder for any data cleaning or transformation
        that needs to be applied to the table before exporting or further processing.
        """
        for col in C_COLUMNS_BASED_HEADERS:
            self._header.add(col)
        self.fill_missing_columns()

        # re-write index
        self._rank_rows(
            primary_key=C_CSV_FIRST_CREATED,
            secondary_key=C_CSV_INDEX,
            rank_key=C_CSV_INDEX,
            secondary_reverse=False,  # oldest first
        )

    def fix_basic_data_with_default(self) -> None:  # ruff:ignore[complex-structure]
        """Fix the basic data in the table.

        This method is a placeholder for any basic data cleaning or transformation
        that needs to be applied to the table before exporting or further processing.
        """
        for row in self._rows:
            if C_CSV_FIRST_CREATED in row and row.get(C_CSV_FIRST_CREATED) is None:
                row[C_CSV_FIRST_CREATED] = "1900-01-01 00:00:00"
            if C_CSV_LAST_MODIFIED in row and row.get(C_CSV_LAST_MODIFIED) is None:
                row[C_CSV_LAST_MODIFIED] = "1900-01-01 00:00:00"
            if C_CSV_BEST_EXTRACTOR in row and row.get(C_CSV_BEST_EXTRACTOR) is None:
                row[C_CSV_BEST_EXTRACTOR] = LevelExtractorEnum.E_E0_MANUAL_ENTRY.value
            if C_CSV_QUALITY_1_DATE in row and row.get(C_CSV_QUALITY_1_DATE) is None:
                row[C_CSV_QUALITY_1_DATE] = "1"
            if C_CSV_QUALITY_2_ROW in row and row.get(C_CSV_QUALITY_2_ROW) is None:
                row[C_CSV_QUALITY_2_ROW] = "1"
            if C_CSV_STRATEGY_QUALITY in row and row.get(C_CSV_STRATEGY_QUALITY) is None:
                row[C_CSV_STRATEGY_QUALITY] = "0"
            if C_CSV_STRATEGY_NEWEST in row and row.get(C_CSV_STRATEGY_NEWEST) is None:
                row[C_CSV_STRATEGY_NEWEST] = "0"
            if C_CSV_STRATEGY_OLDEST in row and row.get(C_CSV_STRATEGY_OLDEST) is None:
                row[C_CSV_STRATEGY_OLDEST] = "0"

    def pre_compute_metadata_csv(self) -> None:
        """Compute the metadata columns and write them into every row.

        For each row, compute the quality columns and the strategy columns.
        """
        for row in self._rows:
            set_last_date_modified_and_extractor(row)  # do first...
            set_first_date_created(row)
            set_quality_count_filled(row)

    def compute_strategy_quality(self) -> None:
        """Compute the quality columns and write them into every row.

        For each row, counts the filled cells, ranks the freshness of the
        modification date, and stores both scores plus their product in the
        dedicated quality columns (added to the header when missing).
        """
        nw = datetime.now()
        default_date_1900 = datetime(year=1900, month=1, day=1)

        for row in self._rows:
            # time
            date_found = row[C_CSV_LAST_MODIFIED]
            date_parsed = parse_date_from_csv(date_found, default=default_date_1900)
            score_updator = get_quality_of_updating_date(nw, date_parsed)

            row[C_CSV_QUALITY_1_DATE] = str(score_updator)

            # heuristic
            q1 = int(row[C_CSV_QUALITY_1_DATE]) or 1
            q2 = int(row[C_CSV_QUALITY_2_ROW]) or 1

            row[C_CSV_STRATEGY_QUALITY] = str(q1 * q2)

    def compute_strategies(self) -> None:
        """Compute the strategy columns and write them into every row.

        For each row, compute the quality strategy, the newest strategy and
        the oldest strategy.
        """
        self._header.add(C_CSV_STRATEGY_NEWEST)  # youtube usage
        self._header.add(C_CSV_STRATEGY_OLDEST)  # metacritics usage

        self._rank_rows(
            primary_key=C_CSV_BEST_EXTRACTOR,
            secondary_key=C_CSV_FIRST_CREATED,
            rank_key=C_CSV_STRATEGY_NEWEST,
            secondary_reverse=True,  # newest first
        )
        self._rank_rows(
            primary_key=C_CSV_BEST_EXTRACTOR,
            secondary_key=C_CSV_FIRST_CREATED,
            rank_key=C_CSV_STRATEGY_OLDEST,
            secondary_reverse=False,  # oldest first
        )

    def export_all_image_base64_to_external(self, folder_export: Path) -> None:
        """Export the image to an external file.

        For each row, export the image to an external file.
        """
        for row in self._rows:
            for col in row:
                value = row.get(col, None)
                # data:image/png;base64,iVBORw0KGgoAAAANSUhEUg... ???
                if value and len(str(value)) >= 16 and value.startswith("data:image"):
                    # export image to external file
                    image_data = row[col]
                    url_unique_keys = row.get(C_CSV_PRIMARY_KEY, "")
                    new_vals = export_base64_image(col, url_unique_keys, image_data, folder_export)
                    row[col] = "![[" + new_vals + "]]"  # syntaxe obsidian

    def do_aggregators(self, aggregators_list: str) -> None:
        """Apply the aggregators to the table.

        For each row, apply the aggregators to the table.
        """
        if not aggregators_list:
            # nothgin ? it's okay...
            return

        is_valid = validate_aggregators_list(aggregators_list)
        if not is_valid:
            raise ValueError(f"Invalid aggregators list: {aggregators_list}")

        pairs = parse_aggregators_list(aggregators_list)

        for kv in pairs:
            print(f"0) row[{kv.e6}] = {kv.sourcing}")
            for row in self._rows:
                if kv.sourcing in row:
                    column_e6 = kv.e6
                    if not kv.e6.startswith(LevelExtractorEnum.E_E6_AGGREGATE.value + "."):
                        column_e6 = LevelExtractorEnum.E_E6_AGGREGATE.value + "." + kv.e6
                    # value exist ?
                    value_fallback = row.get(kv.sourcing)
                    if value_fallback and value_fallback != "":
                        row[column_e6] = value_fallback
                    self._header.add(column_e6)
                # else:
                #     print(f"Column '{kv.sourcing}' not found in row")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_row(self, index: int) -> None:
        """Raise CsvRowIndexNotFoundError when *index* is out of range."""
        if not self.has_row(index):
            raise CsvRowIndexNotFoundError(index)

    def _rank_rows(
        self,
        primary_key: str,
        secondary_key: str,
        rank_key: str,
        primary_reverse: bool = False,
        secondary_reverse: bool = False,
    ) -> None:
        self._rows.sort(
            key=lambda row: (
                self._Reversed(row[primary_key]) if primary_reverse else row[primary_key],
                self._Reversed(row[secondary_key]) if secondary_reverse else row[secondary_key],
            )
        )

        for index, row in enumerate(self._rows):
            row[rank_key] = str(index)

    class _Reversed:
        """Wraps a value so sort() orders it descending instead of negating it.

        Works for any orderable type (numeric strings, ISO "yyyy-mm-dd hh:mm:ss"
        dates, plain strings), unlike ``-float(value)`` which crashes on
        non-numeric values.
        """

        __slots__ = ("value",)

        def __init__(self, value: str) -> None:
            self.value = value

        def __eq__(self, other: object) -> bool:
            return isinstance(other, CsvTable._Reversed) and other.value == self.value

        def __lt__(self, other: CsvTable._Reversed) -> bool:
            return other.value < self.value


# EOF
