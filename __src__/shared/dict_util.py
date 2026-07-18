# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import json
from typing import Any

from shared.constants import (
    C_CSV_BEST_EXTRACTOR,
    C_CSV_FIRST_CREATED,
    C_CSV_LAST_MODIFIED,
    C_CSV_PRIMARY_KEY,
    C_CSV_QUALITY_2_ROW,
    C_JS_PRIMARY_KEY,
    C_SUB_COLUMN_DATE_CREATED,
    C_SUB_COLUMN_DATE_MODIFIED,
)
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from shared.enums.level_extractor_enum import LevelExtractorEnum


def count_items_with_value(dc: dict[str, Any]) -> int:
    """Count the number of items in a dict that have a non-empty value."""
    cells_filled_count = 0
    for value in dc.values():
        if value is not None and value != "":
            cells_filled_count += 1
    return cells_filled_count


def prepare_dict_json_to_dict_csv(
    data: dict[str, Any], lvl_extractor: LevelExtractorEnum, is_found: bool
) -> dict[str, str]:
    """Flatten a top-level JSON dict into a single CSV row.

    Args:
        data: A dict whose top-level keys become column names. Values may
            be str, int, float, bool, None, dict or list.
        lvl_extractor: The level of the extractor.
        is_found: Whether the data was found.

    Returns:
        A dict[str, str] suitable for CsvTable.add_row / replace_row.
    """
    date_now = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

    # préfixe
    transform = {
        (f"{lvl_extractor.value}.{k}" if not k.endswith(C_JS_PRIMARY_KEY) else C_CSV_PRIMARY_KEY): v
        for k, v in data.items()
    }

    # metadata
    if not is_found:  # creation...
        transform[f"{lvl_extractor.value}.{C_SUB_COLUMN_DATE_CREATED}"] = date_now
    transform[f"{lvl_extractor.value}.{C_SUB_COLUMN_DATE_MODIFIED}"] = date_now
    return transform


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


def set_quality_count_filled(row: dict[str, str]) -> None:
    """Count the number of non-empty cells in *row*."""
    cells_filled_count = 1
    for value in row.values():
        if value and len(value) >= 1:
            cells_filled_count += 1
    row[C_CSV_QUALITY_2_ROW] = str(cells_filled_count)


def set_last_date_modified_and_extractor(row: dict[str, str]) -> None:
    """Get the last modified date from *row*."""
    # ordre important !!!! E5 -> E1
    date_modified: list[str] = [
        # pas de E6 -> agrégation des sources, car on ne sait pas si c'est le meilleur extracteur
        LevelExtractorEnum.E_E5_API_INFO.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
        LevelExtractorEnum.E_E4_EXTEND_INFO.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
        LevelExtractorEnum.E_E3_BASIC_INFO.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
        LevelExtractorEnum.E_E2_DISCOVER.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
        LevelExtractorEnum.E_E1_LIST_LINKS.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
        LevelExtractorEnum.E_E0_MANUAL_ENTRY.value + "." + C_SUB_COLUMN_DATE_MODIFIED,
    ]

    for dt_header in date_modified:
        if dt_header in row and row.get(dt_header):
            row[C_CSV_LAST_MODIFIED] = row[dt_header]
            extractor_digram = dt_header.split(".")[0]
            row[C_CSV_BEST_EXTRACTOR] = extractor_digram
            return

    row[C_CSV_LAST_MODIFIED] = "1900-01-01 00:00:00"  # default value
    row[C_CSV_BEST_EXTRACTOR] = "e0"  # undefined ?


def set_first_date_created(row: dict[str, str]) -> None:
    """Get the first created date from *row*."""
    # ordre important !!!! E1 -> E3
    date_created: list[str] = [
        # pas de E6 -> agrégation des sources, car on ne sait pas si c'est le meilleur extracteur
        LevelExtractorEnum.E_E0_MANUAL_ENTRY.value + "." + C_SUB_COLUMN_DATE_CREATED,
        LevelExtractorEnum.E_E1_LIST_LINKS.value + "." + C_SUB_COLUMN_DATE_CREATED,
        LevelExtractorEnum.E_E2_DISCOVER.value + "." + C_SUB_COLUMN_DATE_CREATED,
        LevelExtractorEnum.E_E3_BASIC_INFO.value + "." + C_SUB_COLUMN_DATE_CREATED,
        LevelExtractorEnum.E_E4_EXTEND_INFO.value + "." + C_SUB_COLUMN_DATE_CREATED,
        LevelExtractorEnum.E_E5_API_INFO.value + "." + C_SUB_COLUMN_DATE_CREATED,
    ]

    for dt_header in date_created:
        if dt_header in row and row.get(dt_header):
            row[C_CSV_FIRST_CREATED] = row[dt_header]
            return

    row[C_CSV_FIRST_CREATED] = "1900-01-01 00:00:00"  # default value
    row[C_CSV_BEST_EXTRACTOR] = "e0"  # undefined ?


# EOF
