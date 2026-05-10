"""View-layer step form definitions. Import this package to register all form defs."""

from views.steps.click_element_form_def import ClickElementFormDef
from views.steps.close_tabs_form_def import CloseTabsFormDef
from views.steps.count_element_form_def import CountElementFormDef
from views.steps.download_image_form_def import DownloadImageFormDef
from views.steps.end_process_form_def import EndProcessFormDef
from views.steps.extract_text_form_def import ExtractTextFormDef
from views.steps.jump_to_step_form_def import JumpToStepFormDef
from views.steps.open_url_form_def import OpenUrlFormDef
from views.steps.refresh_page_form_def import RefreshPageFormDef
from views.steps.scroll_down_form_def import ScrollDownFormDef
from views.steps.wait_element_form_def import WaitElementFormDef
from views.steps.wait_image_size_form_def import WaitImageSizeFormDef
from views.steps.wait_rng_pause_form_def import WaitRandomPauseFormDef
from views.steps.wait_user_action_form_def import WaitUserActionFormDef
from views.steps.wait_x_time_form_def import WaitXTimeFormDef

__all__ = [
    "ClickElementFormDef",
    "CloseTabsFormDef",
    "CountElementFormDef",
    "DownloadImageFormDef",
    "EndProcessFormDef",
    "ExtractTextFormDef",
    "JumpToStepFormDef",
    "OpenUrlFormDef",
    "RefreshPageFormDef",
    "ScrollDownFormDef",
    "WaitElementFormDef",
    "WaitImageSizeFormDef",
    "WaitRandomPauseFormDef",
    "WaitUserActionFormDef",
    "WaitXTimeFormDef",
]
