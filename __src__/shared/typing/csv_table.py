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

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from shared.constants import (
    C_COLUMN_DATE_MODIFIED,
    C_COLUMN_QUALITY_1_DATE,
    C_COLUMN_QUALITY_2_ROW,
    C_COLUMN_QUALITY_12_GLOBAL,
)
from shared.datetime_util import parse_date_from_csv
from shared.enums.relative_date_enum import get_quality_of_updating_date
from shared.exception_util import CsvRowIndexNotFoundError

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
        if self._cached_index >= 0 and self._cached_index < len(self._rows):  # noqa: SIM102
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

    def add_row(self, row: dict[str, str]) -> int:
        """Append *row* and return its new index.

        Columns absent from *row* default to "". Extra keys not in the
        header are rejected. "__id__" is assigned from the internal
        counter, overriding any value supplied in *row*.

        Raises:
            CsvColumnNotFoundError: When *row* has a key outside the header.
        """
        self._rows.append(row)
        for key in row:
            if key not in self._header:
                self._header.add(key)
        return len(self._rows) - 1

    def replace_row(self, index: int, row: dict[str, str]) -> None:
        """Replace the row at *index* with *row*, keeping its "__id__".

        Raises:
            CsvRowIndexNotFoundError: When *index* is out of range.
            CsvColumnNotFoundError: When *row* has a key outside the header.
        """
        self._require_row(index)
        self._rows[index] = row
        for key, _ in row:
            self.add_column(key)

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

    def compute_qualities(self) -> None:
        """Compute the quality columns and write them into every row.

        For each row, counts the filled cells, ranks the freshness of the
        modification date, and stores both scores plus their product in the
        dedicated quality columns (added to the header when missing).
        """
        nw = datetime.now()
        default_date_1900 = datetime(year=1900, month=1, day=1)
        self._header.add(C_COLUMN_QUALITY_2_ROW)
        self._header.add(C_COLUMN_QUALITY_1_DATE)
        self._header.add(C_COLUMN_QUALITY_12_GLOBAL)

        for row in self._rows:
            # line

            # quantity
            cells_filled_count = 1
            for value in row.values():
                if value and len(value) >= 1:
                    cells_filled_count += 1

            row[C_COLUMN_QUALITY_2_ROW] = str(cells_filled_count)

            # time
            date_parsed = parse_date_from_csv(row.get(C_COLUMN_DATE_MODIFIED), default=default_date_1900)
            score_updator = get_quality_of_updating_date(nw, date_parsed)

            row[C_COLUMN_QUALITY_1_DATE] = str(score_updator)

            # heuristic
            row[C_COLUMN_QUALITY_12_GLOBAL] = str(cells_filled_count * score_updator)

    # ------------------------------------------------------------------
    # JSON interoperability
    # ------------------------------------------------------------------

    @staticmethod
    def flatten_json_to_row(data: dict[str, Any]) -> dict[str, str]:
        """Flatten a top-level JSON dict into a single CSV row.

        Args:
            data: A dict whose top-level keys become column names. Values may
                be str, int, float, bool, None, dict or list.

        Returns:
            A dict[str, str] suitable for CsvTable.add_row / replace_row.
        """
        return {key: CsvTable.flatten_value(value) for key, value in data.items()}

    @staticmethod
    def unflatten_row_to_json(row: dict[str, str]) -> dict[str, Any]:
        """Convert a CSV row back into a JSON-ready dict.

        Best-effort type inference: each cell is tried as bool, int, float,
        then JSON (for values starting with "{" or "["), falling back to the
        raw string.

        Args:
            row: A CSV row as produced by CsvTable.get_row.

        Returns:
            A dict[str, Any] with inferred value types.
        """
        return {key: CsvTable._unflatten_value(value) for key, value in row.items()}

    def to_json(self) -> list[dict[str, Any]]:
        """Return every row converted to a JSON-ready dict, in order."""
        return [self.unflatten_row_to_json(row) for row in self._rows]

    @staticmethod
    def flatten_value(value: object) -> str:
        """Stringify a single JSON value for storage in a CSV cell."""
        if value is None:
            return ""
        # bool must be checked before int/float: bool is a subclass of int in Python.
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _unflatten_value(value: str) -> object:
        """Infer the original JSON type of a single CSV cell, best-effort."""
        if value in {"True", "False"}:
            return value == "True"
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if value[:1] in {"{", "["}:
            try:
                return json.loads(value)
            except ValueError:
                pass
        return value

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_row(self, index: int) -> None:
        """Raise CsvRowIndexNotFoundError when *index* is out of range."""
        if not self.has_row(index):
            raise CsvRowIndexNotFoundError(index)


# EOF
