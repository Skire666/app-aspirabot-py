"""Tests for shared/exception_util.py — all custom exception classes."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.exception_util import (
    AspirabotBaseError,
    BrowserAlreadyLaunchedError,
    BrowserLaunchFailedError,
    BrowserNotLaunchedError,
    BlankStringError,
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
    ExecutorNotRegisteredError,
    ExportFolderNotADirectoryError,
    ExportFolderNotConfiguredError,
    FailedToCreateRequiredDirectoriesDuringRuntimeError,
    FailedToInitializeLoggingDuringRuntimeError,
    FailedToLoadConfigurationDuringRuntimeError,
    FormNotRegisteredError,
    ImageDownloadFailedError,
    ImageNotDownloadedError,
    ImageWaitTimeoutError,
    InvalidBooleanError,
    InvalidBrowserEngineError,
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
    NoExecutorsRegisteredError,
    NoMatchingImageFoundError,
    OpenUrlTooManyRetriesError,
    PageNotAvailableOrClosedError,
    ParamsBuilderNotRegisteredError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    RepositoryWriteError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
    ScriptExecutionFailedError,
    StringTooLongError,
    StringTooShortError,
    UnknownUrlSourceTypeError,
    UnsupportedBrowserEngineError,
    UnsupportedClickModeError,
    UnsupportedOperatingSystemError,
    UrlNavigationMismatchError,
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
    UrlSourceNoUrlBufferedError,
    UrlSourceNotReadyError,
    ValueMustBeNonNegativeError,
    ValueMustBePositiveAndEvenError,
    ValueMustBePositiveError,
    ValueTooLargeError,
    ValueTooSmallError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _raises(exc_class: type[Exception], *args: object) -> Exception:
    """Instantiate and return an exception, asserting it does not blow up."""
    return exc_class(*args)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class TestAspirabotBaseError:
    def test_is_exception(self) -> None:
        assert issubclass(AspirabotBaseError, Exception)

    def test_instantiate_with_message(self) -> None:
        err = AspirabotBaseError("oops")
        assert "oops" in str(err)


# ---------------------------------------------------------------------------
# Simple zero-arg exceptions (message baked in)
# ---------------------------------------------------------------------------


class TestZeroArgExceptions:
    @pytest.mark.parametrize(
        "cls",
        [
            ValueMustBePositiveError,
            ValueMustBePositiveAndEvenError,
            ValueMustBeNonNegativeError,
            EmptyStringError,
            BlankStringError,
            InvalidBooleanError,
            ListEmptyError,
            DuplicateItemError,
            InvalidRangeNumbersError,
            InvalidFolderLogsError,
            InvalidFolderScenariosError,
            InvalidFolderScrapingError,
            InvalidGuiBootingSizeError,
            FailedToLoadConfigurationDuringRuntimeError,
            FailedToCreateRequiredDirectoriesDuringRuntimeError,
            FailedToInitializeLoggingDuringRuntimeError,
            EmptyScenarioIdError,
            LoggingNotInitializedError,
            CurrentPageClosedUnexpectedlyError,
            NoMatchingImageFoundError,
            BrowserAlreadyLaunchedError,
            BrowserLaunchFailedError,
            BrowserNotLaunchedError,
            DnsSolverTimeoutExceededError,
            PageNotAvailableOrClosedError,
            NoExecutorsRegisteredError,
            OpenUrlTooManyRetriesError,
            UrlSourceExhaustedError,
            UrlSourceFilesNotDiscoveredError,
            UrlSourceNoUrlBufferedError,
            NoDataToExportError,
            ExportFolderNotConfiguredError,
            DownloadNotDetectedError,
            MissingUrlFilterError,
            EmptyCustomUrlError,
            RepositoryWriteError,
        ],
    )
    def test_subclass_of_aspirabot_base(self, cls: type[AspirabotBaseError]) -> None:
        assert issubclass(cls, AspirabotBaseError)

    @pytest.mark.parametrize(
        "cls",
        [
            ValueMustBePositiveError,
            ValueMustBePositiveAndEvenError,
            ValueMustBeNonNegativeError,
            EmptyStringError,
            BlankStringError,
            InvalidBooleanError,
            ListEmptyError,
            DuplicateItemError,
            InvalidRangeNumbersError,
            InvalidFolderLogsError,
            InvalidFolderScenariosError,
            InvalidFolderScrapingError,
            InvalidGuiBootingSizeError,
            FailedToLoadConfigurationDuringRuntimeError,
            FailedToCreateRequiredDirectoriesDuringRuntimeError,
            FailedToInitializeLoggingDuringRuntimeError,
            EmptyScenarioIdError,
            LoggingNotInitializedError,
            CurrentPageClosedUnexpectedlyError,
            NoMatchingImageFoundError,
            BrowserAlreadyLaunchedError,
            BrowserLaunchFailedError,
            BrowserNotLaunchedError,
            DnsSolverTimeoutExceededError,
            PageNotAvailableOrClosedError,
            NoExecutorsRegisteredError,
            OpenUrlTooManyRetriesError,
            UrlSourceExhaustedError,
            UrlSourceFilesNotDiscoveredError,
            UrlSourceNoUrlBufferedError,
            NoDataToExportError,
            ExportFolderNotConfiguredError,
            DownloadNotDetectedError,
            MissingUrlFilterError,
            EmptyCustomUrlError,
            RepositoryWriteError,
        ],
    )
    def test_non_empty_message(self, cls: type[AspirabotBaseError]) -> None:
        err = cls()
        assert str(err)


# ---------------------------------------------------------------------------
# Parameterized exceptions (message depends on args)
# ---------------------------------------------------------------------------


class TestParameterizedExceptions:
    def test_value_too_large_contains_max(self) -> None:
        err = ValueTooLargeError(100)
        assert "100" in str(err)

    def test_value_too_small_contains_min(self) -> None:
        err = ValueTooSmallError(5)
        assert "5" in str(err)

    def test_string_too_long_contains_max_length(self) -> None:
        err = StringTooLongError(255)
        assert "255" in str(err)

    def test_string_too_short_contains_min_length(self) -> None:
        err = StringTooShortError(3)
        assert "3" in str(err)

    def test_list_too_long_contains_max_length(self) -> None:
        err = ListTooLongError(50)
        assert "50" in str(err)

    def test_invalid_log_level_contains_valid_options(self) -> None:
        err = InvalidLogLevelError(["DEBUG", "INFO"])
        assert "DEBUG" in str(err)
        assert "INFO" in str(err)

    def test_invalid_browser_engine_contains_options(self) -> None:
        err = InvalidBrowserEngineError(["Playwright", "Chromium"])
        assert "Playwright" in str(err)

    def test_unsupported_browser_engine_contains_engine(self) -> None:
        err = UnsupportedBrowserEngineError("Firefox")
        assert "Firefox" in str(err)

    def test_invalid_scenario_json_content_contains_filename(self) -> None:
        err = InvalidScenarioJsonContentError("my_file.json")
        assert "my_file.json" in str(err)

    def test_invalid_profiles_folder_path_contains_path(self) -> None:
        err = InvalidProfilesFolderPathError("/some/path")
        assert "/some/path" in str(err)

    def test_invalid_profiles_folder_path_with_path_object(self) -> None:
        err = InvalidProfilesFolderPathError(Path("/some/path"))
        assert "some" in str(err)

    def test_profile_not_found_without_context(self) -> None:
        err = ProfileNotFoundError("abc123")
        assert "abc123" in str(err)

    def test_profile_not_found_with_context(self) -> None:
        err = ProfileNotFoundError("abc123", "suppression")
        assert "abc123" in str(err)
        assert "suppression" in str(err)

    def test_scenario_not_found_without_context(self) -> None:
        err = ScenarioNotFoundError("xyz789")
        assert "xyz789" in str(err)

    def test_scenario_not_found_with_context(self) -> None:
        err = ScenarioNotFoundError("xyz789", "lecture")
        assert "lecture" in str(err)

    def test_scenario_data_missing_contains_id(self) -> None:
        err = ScenarioDataMissingError("scen_42")
        assert "scen_42" in str(err)

    def test_profile_data_missing_contains_id(self) -> None:
        err = ProfileDataMissingError("prof_7")
        assert "prof_7" in str(err)

    def test_invalid_scenarios_folder_path_contains_path(self) -> None:
        err = InvalidScenariosFolderPathError("/bad/path")
        assert "/bad/path" in str(err)

    def test_log_folder_not_a_directory_contains_path(self) -> None:
        err = LogFolderNotADirectoryError("/log/path")
        assert "/log/path" in str(err)

    def test_export_folder_not_a_directory_contains_path(self) -> None:
        err = ExportFolderNotADirectoryError("/export/path")
        assert "/export/path" in str(err)

    def test_unsupported_operating_system_contains_enum(self) -> None:
        err = UnsupportedOperatingSystemError("Windows95")
        assert "Windows95" in str(err)

    def test_configuration_not_loaded_without_action(self) -> None:
        err = ConfigurationNotLoadedError()
        assert str(err)

    def test_configuration_not_loaded_with_action(self) -> None:
        err = ConfigurationNotLoadedError("start_scraping")
        assert "start_scraping" in str(err)

    def test_element_not_found_for_click_contains_selector_and_mode(self) -> None:
        err = ElementNotFoundForClickError(".btn", "normal")
        assert ".btn" in str(err)
        assert "normal" in str(err)

    def test_unsupported_click_mode_contains_mode(self) -> None:
        err = UnsupportedClickModeError("double_click")
        assert "double_click" in str(err)

    def test_count_html_elements_condition_not_met(self) -> None:
        err = CountHtmlElementsConditionNotMetError(5, ">=", "10")
        assert "5" in str(err)
        assert ">=" in str(err)

    def test_count_html_images_condition_not_met(self) -> None:
        err = CountHtmlImagesConditionNotMetError(2, "==", "3")
        assert "2" in str(err)

    def test_image_download_failed_contains_status(self) -> None:
        err = ImageDownloadFailedError(404)
        assert "404" in str(err)

    def test_image_not_downloaded_contains_found(self) -> None:
        err = ImageNotDownloadedError(3)
        assert "3" in str(err)

    def test_image_wait_timeout_contains_seconds(self) -> None:
        err = ImageWaitTimeoutError(30.0)
        assert "30" in str(err)

    def test_executor_not_registered_contains_step_type(self) -> None:
        err = ExecutorNotRegisteredError("OPEN_URL")
        assert "OPEN_URL" in str(err)

    def test_form_not_registered_contains_step_type(self) -> None:
        err = FormNotRegisteredError("CLICK_ON_ELEMENT")
        assert "CLICK_ON_ELEMENT" in str(err)

    def test_params_builder_not_registered_contains_step_type(self) -> None:
        err = ParamsBuilderNotRegisteredError("EXTRACT_TEXTS")
        assert "EXTRACT_TEXTS" in str(err)

    def test_lazy_attribute_not_found_contains_module_and_attr(self) -> None:
        err = LazyAttributeNotFoundError("my_module", "my_attr")
        assert "my_module" in str(err)
        assert "my_attr" in str(err)

    def test_invalid_lru_cache_capacity_contains_capacity(self) -> None:
        err = InvalidLruCacheCapacityError(0)
        assert "0" in str(err)

    def test_invalid_time_unit_contains_unit(self) -> None:
        err = InvalidTimeUnitError("zs")
        assert "zs" in str(err)

    def test_invalid_time_unit_with_none(self) -> None:
        err = InvalidTimeUnitError(None)
        assert str(err)

    def test_invalid_duration_contains_value(self) -> None:
        err = InvalidDurationError(-5)
        assert "-5" in str(err)

    def test_unknown_url_source_type_contains_type(self) -> None:
        err = UnknownUrlSourceTypeError("csv")
        assert "csv" in str(err)

    def test_invalid_url_source_value_type_contains_details(self) -> None:
        err = InvalidUrlSourceValueTypeError("manual", "list[str]", "str")
        assert "manual" in str(err)
        assert "list[str]" in str(err)

    def test_url_source_not_ready_contains_reason(self) -> None:
        err = UrlSourceNotReadyError("not initialized")
        assert "not initialized" in str(err)

    def test_url_source_file_not_found_contains_path(self) -> None:
        err = UrlSourceFileNotFoundError("/some/folder")
        assert "/some/folder" in str(err)

    def test_url_navigation_mismatch_contains_urls(self) -> None:
        err = UrlNavigationMismatchError("http://actual.com", "http://target.com")
        assert "actual.com" in str(err)
        assert "target.com" in str(err)

    def test_script_execution_failed_contains_name(self) -> None:
        err = ScriptExecutionFailedError("inject_js")
        assert "inject_js" in str(err)

    def test_json_file_repository_error_contains_path_and_reason(self) -> None:
        err = JsonFileRepositoryError(Path("/foo/bar.json"), "permission denied")
        assert "bar.json" in str(err)
        assert "permission denied" in str(err)

    def test_duplicate_column_key_contains_key(self) -> None:
        err = DuplicateColumnKeyError("name")
        assert "name" in str(err)

    def test_column_not_found_contains_key(self) -> None:
        err = ColumnNotFoundError("email")
        assert "email" in str(err)


# ---------------------------------------------------------------------------
# Inheritance chains
# ---------------------------------------------------------------------------


class TestInheritanceChains:
    def test_invalid_scenario_json_inherits_value_error(self) -> None:
        assert issubclass(InvalidScenarioJsonContentError, ValueError)

    def test_profile_not_found_inherits_file_not_found(self) -> None:
        assert issubclass(ProfileNotFoundError, FileNotFoundError)

    def test_scenario_not_found_inherits_file_not_found(self) -> None:
        assert issubclass(ScenarioNotFoundError, FileNotFoundError)

    def test_browser_already_launched_inherits_runtime_error(self) -> None:
        assert issubclass(BrowserAlreadyLaunchedError, RuntimeError)

    def test_url_source_files_not_discovered_inherits_not_ready(self) -> None:
        assert issubclass(UrlSourceFilesNotDiscoveredError, UrlSourceNotReadyError)

    def test_url_source_no_url_buffered_inherits_not_ready(self) -> None:
        assert issubclass(UrlSourceNoUrlBufferedError, UrlSourceNotReadyError)

    def test_image_wait_timeout_inherits_timeout_error(self) -> None:
        assert issubclass(ImageWaitTimeoutError, TimeoutError)

    def test_unsupported_operating_system_inherits_os_error(self) -> None:
        assert issubclass(UnsupportedOperatingSystemError, OSError)

    def test_duplicate_column_key_inherits_value_error(self) -> None:
        assert issubclass(DuplicateColumnKeyError, ValueError)

    def test_json_file_repository_inherits_aspirabot_base(self) -> None:
        assert issubclass(JsonFileRepositoryError, AspirabotBaseError)

    def test_invalid_lru_cache_capacity_inherits_value_error(self) -> None:
        assert issubclass(InvalidLruCacheCapacityError, ValueError)
