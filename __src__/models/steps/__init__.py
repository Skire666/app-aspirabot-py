"""Domain params models for all step types. Import this package to register all params classes."""

from models.steps.click_element_params import ClickElementParams
from models.steps.close_tabs_params import CloseTabsParams
from models.steps.count_element_params import CountElementsParams
from models.steps.download_image_params import DownloadImageParams
from models.steps.end_process_params import EndProcessParams
from models.steps.extract_text_params import ExtractTextParams
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.open_url_params import OpenUrlParams
from models.steps.random_pause_params import RandomPauseParams
from models.steps.refresh_page_params import RefreshPageParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.wait_element_params import WaitElementParams
from models.steps.wait_image_size_params import WaitImageSizeParams
from models.steps.wait_user_action_params import WaitUserActionParams
from models.steps.wait_x_time_params import WaitXTimeParams

__all__ = [
    "ClickElementParams",
    "CloseTabsParams",
    "CountElementsParams",
    "DownloadImageParams",
    "EndProcessParams",
    "ExtractTextParams",
    "JumpToStepParams",
    "OpenUrlParams",
    "RandomPauseParams",
    "RefreshPageParams",
    "ScrollDownParams",
    "WaitElementParams",
    "WaitImageSizeParams",
    "WaitUserActionParams",
    "WaitXTimeParams",
]
