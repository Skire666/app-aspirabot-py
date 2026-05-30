"""Domain params models for all step types. Import this package to register all params classes."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.steps.click_for_download_params import ClickForDownloadParams
from models.steps.click_on_element_params import ClickOnElementParams
from models.steps.close_tabs_params import CloseTabsParams
from models.steps.count_html_elements_params import CountHtmlElementsParams
from models.steps.count_html_images_params import CountHtmlImagesParams
from models.steps.download_image_params import DownloadImageParams
from models.steps.export_data_to_js_params import ExportDataToJsParams
from models.steps.extract_links_params import ExtractLinksParams
from models.steps.extract_texts_params import ExtractTextsParams
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.kill_browser_params import KillBrowserParams
from models.steps.open_url_params import OpenUrlParams
from models.steps.refresh_page_params import RefreshPageParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from models.steps.wait_page_state_params import WaitPageStateParams
from models.steps.wait_rng_pause_params import WaitRngPauseParams
from models.steps.wait_user_action_params import WaitUserActionParams

__all__ = [
    "ClickForDownloadParams",
    "ClickOnElementParams",
    "CloseTabsParams",
    "CountHtmlElementsParams",
    "CountHtmlImagesParams",
    "DownloadImageParams",
    "ExportDataToJsParams",
    "ExtractLinksParams",
    "ExtractTextsParams",
    "JumpToStepParams",
    "KillBrowserParams",
    "OpenUrlParams",
    "RefreshPageParams",
    "ScrollDownParams",
    "WaitFixedTimeParams",
    "WaitHtmlElementsParams",
    "WaitHtmlImagesParams",
    "WaitPageStateParams",
    "WaitRngPauseParams",
    "WaitUserActionParams",
]


# EOF
