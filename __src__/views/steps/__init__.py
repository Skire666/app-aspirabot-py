"""View-layer step form definitions. Import this package to register all forms."""

from views.steps.click_element_form_def import ClickElementFormDef
from views.steps.close_tabs_form_def import CloseTabsFormDef
from views.steps.count_html_elements_form_def import CountHtmlElementsFormDef
from views.steps.count_html_images_form_def import CountHtmlImagesFormDef
from views.steps.download_image_form_def import DownloadImageFormDef
from views.steps.end_process_form_def import EndProcessFormDef
from views.steps.extract_text_form_def import ExtractTextFormDef
from views.steps.jump_to_step_form_def import JumpToStepFormDef
from views.steps.open_url_form_def import OpenUrlFormDef
from views.steps.refresh_page_form_def import RefreshPageFormDef
from views.steps.scroll_down_form_def import ScrollDownFormDef
from views.steps.wait_fixed_time_form_def import WaitFixedTimeFormDef
from views.steps.wait_html_elements_form_def import WaitHtmlElementsFormDef
from views.steps.wait_html_images_form_def import WaitHtmlImagesFormDef
from views.steps.wait_page_state_form_def import WaitPageStateFormDef
from views.steps.wait_rng_pause_form_def import WaitRngPauseFormDef
from views.steps.wait_user_action_form_def import WaitUserActionFormDef

__all__ = [
    "ClickElementFormDef",
    "CloseTabsFormDef",
    "CountHtmlElementsFormDef",
    "CountHtmlImagesFormDef",
    "DownloadImageFormDef",
    "EndProcessFormDef",
    "ExtractTextFormDef",
    "JumpToStepFormDef",
    "OpenUrlFormDef",
    "RefreshPageFormDef",
    "ScrollDownFormDef",
    "WaitFixedTimeFormDef",
    "WaitHtmlElementsFormDef",
    "WaitHtmlImagesFormDef",
    "WaitPageStateFormDef",
    "WaitRngPauseFormDef",
    "WaitUserActionFormDef",
]
