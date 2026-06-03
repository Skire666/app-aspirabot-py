"""Regression tests — LaunchModel.import_from_data_json url_source_value type preservation.

Regression for the bug where `str()` was applied unconditionally to
`url_source_value` during deserialization, turning a list of URLs into its
string representation (e.g. "['http://...']"), causing `isinstance(v, list)`
to return False downstream and silently producing an empty URL list.

Scope:
- import_from_data_json must preserve list type when url_source_value is a list.
- import_from_data_json must preserve str type when url_source_value is a string.
- Round-trip export_to_data_json → import_from_data_json must be lossless for both types.
"""

from __future__ import annotations

import pytest

from models.launcher_model import LaunchModel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_URLS = [
    "https://www.youtube.com/watch?v=oEjZUfpZ8dA",
    "https://www.youtube.com/watch?v=Szoeo4HBJ4c",
    "https://www.youtube.com/watch?v=huAwz_BR8WM",
]

_BASE_DATA: dict = {
    "id_profile": "abc123",
    "id_scenario": "my_scenario",
    "profile_name": "Mon profil",
    "export_folder": "/tmp/export",
    "url_source_type": "MANUAL",
    "emergency_stop_threshold": 5,
    "launch_count": 0,
    "used_date_profile": None,
    "url_sort_order": "",
    "emergency_stop_step_id": "",
    "emergency_stop_step_threshold": 0,
}


def _data(**overrides) -> dict:
    return {**_BASE_DATA, **overrides}


# ---------------------------------------------------------------------------
# Type preservation on import
# ---------------------------------------------------------------------------


class TestImportFromDataJsonUrlSourceValueType:
    def test_list_value_remains_list_when_source_type_is_manual(self) -> None:
        """url_source_value doit rester une liste après désérialisation (mode MANUAL)."""
        # Arrange
        data = _data(url_source_value=_URLS)

        # Act
        model = LaunchModel.import_from_data_json(data)

        # Assert
        assert isinstance(model.url_source_value, list), (
            "url_source_value doit être de type list après import — str() ne doit pas être appliqué"
        )

    def test_list_value_content_is_preserved_when_source_type_is_manual(self) -> None:
        """Les URLs contenues dans url_source_value doivent être intactes après désérialisation."""
        # Arrange
        data = _data(url_source_value=_URLS)

        # Act
        model = LaunchModel.import_from_data_json(data)

        # Assert
        assert model.url_source_value == _URLS, (
            "Le contenu de url_source_value doit être identique aux URLs d'origine"
        )

    def test_string_value_remains_str_when_source_type_is_folder(self) -> None:
        """url_source_value doit rester une chaîne après désérialisation (mode FOLDER)."""
        # Arrange
        path = "/data/images"
        data = _data(url_source_type="FOLDER", url_source_value=path)

        # Act
        model = LaunchModel.import_from_data_json(data)

        # Assert
        assert isinstance(model.url_source_value, str), (
            "url_source_value doit rester str quand la valeur stockée est un chemin"
        )
        assert model.url_source_value == path, (
            "Le chemin ne doit pas être altéré lors de l'import"
        )


# ---------------------------------------------------------------------------
# Round-trip losslessness
# ---------------------------------------------------------------------------


class TestRoundTripUrlSourceValue:
    def test_roundtrip_list_is_lossless(self) -> None:
        """export_to_data_json → import_from_data_json doit préserver la liste d'URLs."""
        # Arrange
        data = _data(url_source_value=_URLS)
        original = LaunchModel.import_from_data_json(data)

        # Act
        exported = original.export_to_data_json()
        restored = LaunchModel.import_from_data_json(exported)

        # Assert
        assert restored.url_source_value == _URLS, (
            "Le round-trip doit reproduire la liste de URLs à l'identique"
        )

    def test_roundtrip_string_is_lossless(self) -> None:
        """export_to_data_json → import_from_data_json doit préserver un chemin string."""
        # Arrange
        path = "/mnt/data/source"
        data = _data(url_source_type="FOLDER", url_source_value=path)
        original = LaunchModel.import_from_data_json(data)

        # Act
        exported = original.export_to_data_json()
        restored = LaunchModel.import_from_data_json(exported)

        # Assert
        assert restored.url_source_value == path, (
            "Le round-trip doit reproduire le chemin à l'identique"
        )


# ---------------------------------------------------------------------------
# Parametric — types of url_source_value accepted by import_from_data_json
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_value, expected_type",
    [
        (_URLS, list),
        ("/some/path", str),
        ("", str),
    ],
    ids=["list-of-urls", "path-string", "empty-string"],
)
def test_import_from_data_json_url_source_value_type_is_preserved(
    raw_value: list | str, expected_type: type
) -> None:
    """import_from_data_json doit préserver le type natif de url_source_value."""
    # Arrange
    data = _data(url_source_value=raw_value)

    # Act
    model = LaunchModel.import_from_data_json(data)

    # Assert
    assert isinstance(model.url_source_value, expected_type), (
        f"Attendu type {expected_type.__name__}, obtenu {type(model.url_source_value).__name__}"
    )
