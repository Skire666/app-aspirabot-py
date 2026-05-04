"""Domain params models for all step types. Import this package to register all params classes."""
from models.steps.open_url_params import OpenUrlParams
from models.steps.refresh_page_params import RefreshPageParams
from models.steps.sleep_x_time_params import SleepXTimeParams
from models.steps.random_pause_params import RandomPauseParams
from models.steps.download_image_params import DownloadImageParams
from models.steps.wait_image_size_params import WaitImageSizeParams
from models.steps.wait_element_params import WaitElementParams
from models.steps.count_element_params import CountElementParams
from models.steps.click_element_params import ClickElementParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.extract_text_params import ExtractTextParams
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.close_tabs_params import CloseTabsParams
from models.steps.end_process_params import EndProcessParams
from models.steps.wait_user_action_params import WaitUserActionParams

__all__ = [
    "OpenUrlParams", "RefreshPageParams", "SleepXTimeParams", "RandomPauseParams",
    "DownloadImageParams", "WaitImageSizeParams", "WaitElementParams", "CountElementParams",
    "ClickElementParams", "ScrollDownParams", "ExtractTextParams", "JumpToStepParams",
    "CloseTabsParams", "EndProcessParams", "WaitUserActionParams",
]
