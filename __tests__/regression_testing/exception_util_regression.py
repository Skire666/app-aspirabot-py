"""Regression tests — shared/exception_util.py.

Freezes the public contract of every custom exception class:
- Instantiation succeeds with the documented signature.
- str() produces a non-empty French message.
- isinstance checks confirm the inheritance chain (AspirabotBaseError + stdlib base).

These tests do NOT duplicate unit_testing; they act as a characterisation layer
so that renaming a message string or changing a constructor signature is caught.
"""

from __future__ import annotations

from shared.exception_util import (
    AspirabotBaseError,
    BlankStringError,
    BrowserAlreadyLaunchedError,
    BrowserLaunchFailedError,
    BrowserNotLaunchedError,
    ColumnNotFoundError,
    ConfigurationNotLoadedError,
    CountHtmlElementsConditionNotMetError,
    CountHtmlImagesConditionNotMetError,
    CurrentPageClosedUnexpectedlyError,
    DnsSolverTimeoutExceededError,
    DownloadNotDetectedError,
    DuplicateColumnKeyError,
    DuplicateItemError,
    ElementNotFoundForClickError,
    EmptyCustomUrlError,
    EmptyScenarioIdError,
    EmptyStringError,
    ExportFolderNotADirectoryError,
    ExportFolderNotConfiguredError,
    FailedToCreateRequiredDirectoriesDuringRuntimeError,
    FailedToInitializeLoggingDuringRuntimeError,
    FailedToLoadConfigurationDuringRuntimeError,
    ImageDownloadFailedError,
    ImageNotDownloadedError,
    ImageWaitTimeoutError,
    InvalidBooleanError,
    InvalidDurationError,
    InvalidFolderLogsError,
    InvalidFolderScenariosError,
    InvalidFolderScrapingError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
    InvalidLruCacheCapacityError,
    InvalidProfilesFolderPathError,
    InvalidRangeNumbersError,
    InvalidScenarioJsonContentError,
    InvalidScenariosFolderPathError,
    InvalidTimeUnitError,
    InvalidUrlSourceValueTypeError,
    JsonFileRepositoryError,
    LazyAttributeNotFoundError,
    ListEmptyError,
    ListTooLongError,
    LogFolderNotADirectoryError,
    LoggingNotInitializedError,
    MissingUrlFilterError,
    NoDataToExportError,
    NoMatchingImageFoundError,
    OpenUrlTooManyRetriesError,
    PageNotAvailableOrClosedError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    RepositoryWriteError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
    ScriptExecutionFailedError,
    StringTooLongError,
    StringTooShortError,
    UnknownUrlSourceTypeError,
    UnsupportedClickModeError,
    UnsupportedOperatingSystemError,
    UrlNavigationMismatchError,
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
    UrlSourceNotReadyError,
    UrlSourceNoUrlBufferedError,
    ValueMustBeNonNegativeError,
    ValueMustBePositiveAndEvenError,
    ValueMustBePositiveError,
    ValueTooLargeError,
    ValueTooSmallError,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _msg(exc: Exception) -> str:
    return str(exc)


# ---------------------------------------------------------------------------
# Value constraint errors
# ---------------------------------------------------------------------------


class TestValueConstraintErrors:
    def test_value_must_be_positive(self) -> None:
        exc = ValueMustBePositiveError()
        assert isinstance(exc, AspirabotBaseError)
        assert "0" in _msg(exc)

    def test_value_must_be_positive_and_even(self) -> None:
        exc = ValueMustBePositiveAndEvenError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0

    def test_value_must_be_non_negative(self) -> None:
        exc = ValueMustBeNonNegativeError()
        assert isinstance(exc, AspirabotBaseError)
        assert "0" in _msg(exc)

    def test_value_too_large(self) -> None:
        exc = ValueTooLargeError(100)
        assert "100" in _msg(exc)

    def test_value_too_small(self) -> None:
        exc = ValueTooSmallError(5)
        assert "5" in _msg(exc)

    def test_invalid_range_numbers(self) -> None:
        exc = InvalidRangeNumbersError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0


# ---------------------------------------------------------------------------
# String constraint errors
# ---------------------------------------------------------------------------


class TestStringConstraintErrors:
    def test_empty_string_error(self) -> None:
        exc = EmptyStringError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0

    def test_blank_string_error(self) -> None:
        exc = BlankStringError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0

    def test_string_too_long(self) -> None:
        exc = StringTooLongError(50)
        assert "50" in _msg(exc)

    def test_string_too_short(self) -> None:
        exc = StringTooShortError(3)
        assert "3" in _msg(exc)

    def test_invalid_boolean_error(self) -> None:
        exc = InvalidBooleanError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0


# ---------------------------------------------------------------------------
# List constraint errors
# ---------------------------------------------------------------------------


class TestListConstraintErrors:
    def test_list_empty_error(self) -> None:
        exc = ListEmptyError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0

    def test_list_too_long(self) -> None:
        exc = ListTooLongError(10)
        assert "10" in _msg(exc)

    def test_duplicate_item_error(self) -> None:
        exc = DuplicateItemError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class TestConfigurationErrors:
    def test_invalid_log_level(self) -> None:
        exc = InvalidLogLevelError(["DEBUG", "INFO", "WARNING"])
        assert "DEBUG" in _msg(exc)
        assert "INFO" in _msg(exc)

    def test_invalid_folder_logs(self) -> None:
        exc = InvalidFolderLogsError()
        assert isinstance(exc, AspirabotBaseError)

    def test_invalid_folder_scenarios(self) -> None:
        exc = InvalidFolderScenariosError()
        assert isinstance(exc, AspirabotBaseError)

    def test_invalid_folder_scraping(self) -> None:
        exc = InvalidFolderScrapingError()
        assert isinstance(exc, AspirabotBaseError)

    def test_invalid_gui_booting_size(self) -> None:
        exc = InvalidGuiBootingSizeError()
        assert isinstance(exc, AspirabotBaseError)
        assert "LARGEURxHAUTEUR" in _msg(exc) or "format" in _msg(exc).lower()

    def test_failed_to_load_configuration(self) -> None:
        exc = FailedToLoadConfigurationDuringRuntimeError()
        assert isinstance(exc, AspirabotBaseError)

    def test_failed_to_create_required_dirs(self) -> None:
        exc = FailedToCreateRequiredDirectoriesDuringRuntimeError()
        assert isinstance(exc, AspirabotBaseError)

    def test_failed_to_initialize_logging(self) -> None:
        exc = FailedToInitializeLoggingDuringRuntimeError()
        assert isinstance(exc, AspirabotBaseError)

    def test_configuration_not_loaded_without_action(self) -> None:
        exc = ConfigurationNotLoadedError()
        assert isinstance(exc, ValueError)
        assert isinstance(exc, AspirabotBaseError)

    def test_configuration_not_loaded_with_action(self) -> None:
        exc = ConfigurationNotLoadedError(action="run_scraping()")
        assert "run_scraping()" in _msg(exc)

    def test_logging_not_initialized(self) -> None:
        exc = LoggingNotInitializedError()
        assert isinstance(exc, ValueError)
        assert isinstance(exc, AspirabotBaseError)


# ---------------------------------------------------------------------------
# Scenario / profile data errors
# ---------------------------------------------------------------------------


class TestDataErrors:
    def test_invalid_scenario_json_content(self) -> None:
        exc = InvalidScenarioJsonContentError("my_scenario.json")
        assert isinstance(exc, ValueError)
        assert "my_scenario.json" in _msg(exc)

    def test_invalid_profiles_folder_path(self) -> None:
        exc = InvalidProfilesFolderPathError("/some/path")
        assert isinstance(exc, NotADirectoryError)
        assert "/some/path" in _msg(exc)

    def test_profile_not_found_without_context(self) -> None:
        exc = ProfileNotFoundError("prof_abc")
        assert isinstance(exc, FileNotFoundError)
        assert "prof_abc" in _msg(exc)

    def test_profile_not_found_with_context(self) -> None:
        exc = ProfileNotFoundError("prof_xyz", context="suppression")
        assert "suppression" in _msg(exc)
        assert "prof_xyz" in _msg(exc)

    def test_scenario_not_found_without_context(self) -> None:
        exc = ScenarioNotFoundError("scen_001")
        assert isinstance(exc, FileNotFoundError)
        assert "scen_001" in _msg(exc)

    def test_scenario_not_found_with_context(self) -> None:
        exc = ScenarioNotFoundError("scen_002", context="lecture")
        assert "lecture" in _msg(exc)

    def test_empty_scenario_id(self) -> None:
        exc = EmptyScenarioIdError()
        assert isinstance(exc, AspirabotBaseError)
        assert len(_msg(exc)) > 0

    def test_scenario_data_missing(self) -> None:
        exc = ScenarioDataMissingError("scen_missing")
        assert isinstance(exc, ValueError)
        assert "scen_missing" in _msg(exc)

    def test_profile_data_missing(self) -> None:
        exc = ProfileDataMissingError("prof_missing")
        assert isinstance(exc, ValueError)
        assert "prof_missing" in _msg(exc)

    def test_invalid_scenarios_folder_path(self) -> None:
        exc = InvalidScenariosFolderPathError("/bad/folder")
        assert isinstance(exc, NotADirectoryError)
        assert "/bad/folder" in _msg(exc)


# ---------------------------------------------------------------------------
# Folder path errors
# ---------------------------------------------------------------------------


class TestFolderPathErrors:
    def test_log_folder_not_a_directory(self) -> None:
        exc = LogFolderNotADirectoryError("/logs/path")
        assert isinstance(exc, NotADirectoryError)
        assert "/logs/path" in _msg(exc)

    def test_export_folder_not_a_directory(self) -> None:
        exc = ExportFolderNotADirectoryError("/export/path")
        assert isinstance(exc, NotADirectoryError)
        assert "/export/path" in _msg(exc)

    def test_unsupported_operating_system(self) -> None:
        exc = UnsupportedOperatingSystemError("PLAN9")
        assert isinstance(exc, OSError)
        assert "PLAN9" in _msg(exc)


# ---------------------------------------------------------------------------
# Browser / click errors
# ---------------------------------------------------------------------------


class TestBrowserErrors:
    def test_element_not_found_for_click(self) -> None:
        exc = ElementNotFoundForClickError(".btn", "forced")
        assert isinstance(exc, ValueError)
        assert ".btn" in _msg(exc)
        assert "forced" in _msg(exc)

    def test_unsupported_click_mode(self) -> None:
        exc = UnsupportedClickModeError("triple")
        assert isinstance(exc, ValueError)
        assert "triple" in _msg(exc)

    def test_current_page_closed_unexpectedly(self) -> None:
        exc = CurrentPageClosedUnexpectedlyError()
        assert isinstance(exc, ValueError)
        assert len(_msg(exc)) > 0


# ---------------------------------------------------------------------------
# Count / image errors
# ---------------------------------------------------------------------------


class TestCountAndImageErrors:
    def test_count_html_elements_condition_not_met(self) -> None:
        exc = CountHtmlElementsConditionNotMetError(count=3, operator="greater_than", value_ask="5")
        assert "3" in _msg(exc)
        assert "greater_than" in _msg(exc)

    def test_count_html_images_condition_not_met(self) -> None:
        exc = CountHtmlImagesConditionNotMetError(count=0, operator="equal", value_desc="2")
        assert "0" in _msg(exc)

    def test_no_matching_image_found(self) -> None:
        exc = NoMatchingImageFoundError()
        assert isinstance(exc, ValueError)
        assert len(_msg(exc)) > 0

    def test_image_download_failed(self) -> None:
        exc = ImageDownloadFailedError(status=404)
        assert "404" in _msg(exc)

    def test_image_not_downloaded(self) -> None:
        exc = ImageNotDownloadedError(found=2)
        assert "2" in _msg(exc)

    def test_image_wait_timeout(self) -> None:
        exc = ImageWaitTimeoutError(30.0)
        assert isinstance(exc, TimeoutError)
        assert isinstance(exc, AspirabotBaseError)
        assert "30" in _msg(exc)


# ---------------------------------------------------------------------------
# Browser state errors
# ---------------------------------------------------------------------------


class TestBrowserStateErrors:
    def test_browser_already_launched(self) -> None:
        exc = BrowserAlreadyLaunchedError()
        assert isinstance(exc, RuntimeError)
        assert isinstance(exc, AspirabotBaseError)

    def test_browser_launch_failed(self) -> None:
        exc = BrowserLaunchFailedError()
        assert isinstance(exc, RuntimeError)

    def test_browser_not_launched(self) -> None:
        exc = BrowserNotLaunchedError()
        assert isinstance(exc, RuntimeError)

    def test_page_not_available_or_closed(self) -> None:
        exc = PageNotAvailableOrClosedError()
        assert isinstance(exc, RuntimeError)

    def test_dns_solver_timeout_exceeded(self) -> None:
        exc = DnsSolverTimeoutExceededError()
        assert isinstance(exc, RuntimeError)
        assert "30" in _msg(exc)

    def test_url_navigation_mismatch(self) -> None:
        exc = UrlNavigationMismatchError("https://landed.com", "https://target.com")
        assert "https://landed.com" in _msg(exc)
        assert "https://target.com" in _msg(exc)


# ---------------------------------------------------------------------------
# Step execution errors
# ---------------------------------------------------------------------------


class TestStepExecutionErrors:
    def test_no_data_to_export(self) -> None:
        exc = NoDataToExportError()
        assert isinstance(exc, AspirabotBaseError)

    def test_export_folder_not_configured(self) -> None:
        exc = ExportFolderNotConfiguredError()
        assert isinstance(exc, AspirabotBaseError)

    def test_download_not_detected(self) -> None:
        exc = DownloadNotDetectedError()
        assert isinstance(exc, AspirabotBaseError)

    def test_missing_url_filter(self) -> None:
        exc = MissingUrlFilterError()
        assert isinstance(exc, ValueError)

    def test_empty_custom_url(self) -> None:
        exc = EmptyCustomUrlError()
        assert isinstance(exc, ValueError)

    def test_script_execution_failed(self) -> None:
        exc = ScriptExecutionFailedError("my_script")
        assert "my_script" in _msg(exc)

    def test_open_url_too_many_retries(self) -> None:
        exc = OpenUrlTooManyRetriesError()
        assert isinstance(exc, RuntimeError)


# ---------------------------------------------------------------------------
# URL source errors
# ---------------------------------------------------------------------------


class TestUrlSourceErrors:
    def test_unknown_urls_source_type(self) -> None:
        exc = UnknownUrlSourceTypeError("magic")
        assert "magic" in _msg(exc)

    def test_invalid_url_source_value_type(self) -> None:
        exc = InvalidUrlSourceValueTypeError("folder", "str", "list")
        assert "folder" in _msg(exc)
        assert "str" in _msg(exc)
        assert "list" in _msg(exc)

    def test_url_source_not_ready(self) -> None:
        exc = UrlSourceNotReadyError("not initialised")
        assert "not initialised" in _msg(exc)

    def test_url_source_files_not_discovered(self) -> None:
        exc = UrlSourceFilesNotDiscoveredError()
        assert isinstance(exc, UrlSourceNotReadyError)

    def test_url_source_no_url_buffered(self) -> None:
        exc = UrlSourceNoUrlBufferedError()
        assert isinstance(exc, UrlSourceNotReadyError)

    def test_url_source_exhausted(self) -> None:
        exc = UrlSourceExhaustedError()
        assert isinstance(exc, ValueError)

    def test_url_source_file_not_found(self) -> None:
        exc = UrlSourceFileNotFoundError("/missing/path")
        assert "/missing/path" in _msg(exc)


# ---------------------------------------------------------------------------
# Registry errors
# ---------------------------------------------------------------------------


class TestRegistryErrors:
    def test_executor_not_registered(self) -> None:
        from shared.exception_util import ExecutorNotRegisteredError

        exc = ExecutorNotRegisteredError("OPEN_URL")
        assert isinstance(exc, ValueError)
        assert "OPEN_URL" in _msg(exc)

    def test_no_executors_registered(self) -> None:
        from shared.exception_util import NoExecutorsRegisteredError

        exc = NoExecutorsRegisteredError()
        assert isinstance(exc, ValueError)

    def test_form_not_registered(self) -> None:
        from shared.exception_util import FormNotRegisteredError

        exc = FormNotRegisteredError("SCROLL_DOWN")
        assert "SCROLL_DOWN" in _msg(exc)

    def test_params_builder_not_registered(self) -> None:
        from shared.exception_util import ParamsBuilderNotRegisteredError

        exc = ParamsBuilderNotRegisteredError("SECTION")
        assert "SECTION" in _msg(exc)

    def test_lazy_attribute_not_found(self) -> None:
        exc = LazyAttributeNotFoundError("shared.enums", "NonExistent")
        assert "shared.enums" in _msg(exc)
        assert "NonExistent" in _msg(exc)

    def test_invalid_lru_cache_capacity(self) -> None:
        exc = InvalidLruCacheCapacityError(0)
        assert "0" in _msg(exc)


# ---------------------------------------------------------------------------
# Time util errors
# ---------------------------------------------------------------------------


class TestTimeUtilErrors:
    def test_invalid_time_unit(self) -> None:
        exc = InvalidTimeUnitError("ms")
        assert "ms" in _msg(exc)

    def test_invalid_time_unit_none(self) -> None:
        exc = InvalidTimeUnitError(None)
        assert isinstance(exc, ValueError)

    def test_invalid_duration(self) -> None:
        exc = InvalidDurationError(-1)
        assert "-1" in _msg(exc)


# ---------------------------------------------------------------------------
# Repository errors
# ---------------------------------------------------------------------------


class TestRepositoryErrors:
    def test_repository_write_error(self) -> None:
        exc = RepositoryWriteError()
        assert isinstance(exc, AspirabotBaseError)

    def test_json_file_repository_error(self) -> None:
        from pathlib import Path

        exc = JsonFileRepositoryError(Path("/some/file.json"), "disk full")
        assert "disk full" in _msg(exc)
        assert "file.json" in _msg(exc)


# ---------------------------------------------------------------------------
# UI widget errors
# ---------------------------------------------------------------------------


class TestUiWidgetErrors:
    def test_duplicate_column_key(self) -> None:
        exc = DuplicateColumnKeyError("name")
        assert isinstance(exc, ValueError)
        assert "name" in _msg(exc)

    def test_column_not_found(self) -> None:
        exc = ColumnNotFoundError("age")
        assert isinstance(exc, ValueError)
        assert "age" in _msg(exc)
