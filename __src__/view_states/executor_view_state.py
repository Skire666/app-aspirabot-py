"""ViewState DTOs for the executor module.

Immutable snapshots built by ExecutorPresenter and consumed by ExecutorView.
No business logic, no Model or Service imports.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass


# -----------------------------------------------------------------------------
# Item-level states (list entries)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioItemViewState:
    """One scenario entry in the scenario combobox.

    Attributes:
        id_file: Unique file identifier of the scenario.
        scenario_name: Display name shown in the primary combobox column.
        scenario_desc: Short description shown in the secondary column.
    """

    id_file: str
    scenario_name: str
    scenario_desc: str


@dataclass(frozen=True)
class ProfileItemViewState:
    """One profile entry in the profile listbox.

    Attributes:
        id_profile: Unique identifier of the launch profile.
        profile_name: Display name shown in the listbox row.
    """

    id_profile: str
    profile_name: str


@dataclass(frozen=True)
class StepItemViewState:
    """One step entry in the per-step emergency-stop combobox.

    Attributes:
        step_id: Unique identifier of the step.
        label: Formatted display label (e.g. ``"1. click_on_element — abc123"``).
    """

    step_id: str
    label: str


# -----------------------------------------------------------------------------
# URL source sub-state
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class UrlSourceViewState:
    """Snapshot of the URL-source configuration section.

    The three ``is_*`` flags let the View enable or disable widgets without
    comparing domain enum values itself.

    Attributes:
        source_type: Raw ``UrlSourceTypeEnum`` value string.
        source_path: Path string for folder/json sources; empty for manual.
        manual_urls: Ordered URL list for manual source; empty for others.
        sort_order: Raw ``UrlSortOrderEnum`` value string.
        is_path_entry_enabled: Whether the path entry and browse button are active.
        is_sort_order_enabled: Whether the sort-order radio buttons are active.
        is_preview_editable: Whether the URL preview text area accepts typing.
    """

    source_type: str
    source_path: str
    manual_urls: tuple[str, ...]
    sort_order: str
    is_path_entry_enabled: bool
    is_sort_order_enabled: bool
    is_preview_editable: bool


# -----------------------------------------------------------------------------
# Full form state
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ProfileFormViewState:
    """Snapshot of all launch-profile form fields for display.

    Attributes:
        used_date: Formatted last-used date string, or the empty placeholder.
        launch_count: Number of times the profile has been launched.
        export_folder: Absolute path of the export destination folder.
        url_source: Full URL-source configuration snapshot.
        global_threshold: Global error-count threshold (raw integer).
        step_threshold: Per-step error-count threshold (raw integer).
        step_id_selected: Step ID pre-selected in the emergency-stop combobox.
        steps: Ordered tuple of step entries for the emergency-stop combobox.
    """

    used_date: str
    launch_count: int
    export_folder: str
    url_source: UrlSourceViewState
    global_threshold: int
    step_threshold: int
    step_id_selected: str
    steps: tuple[StepItemViewState, ...]
