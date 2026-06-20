"""View-layer step form definitions. Import this package to register all forms."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from views.steps.check_url_page_form_def import CheckUrlPageFormDef
from views.steps.click_for_download_form_def import ClickForDownloadFormDef
from views.steps.click_on_element_form_def import ClickOnElementFormDef
from views.steps.close_tabs_form_def import CloseTabsFormDef
from views.steps.count_html_elements_form_def import CountHtmlElementsFormDef
from views.steps.count_html_images_form_def import CountHtmlImagesFormDef
from views.steps.download_image_form_def import DownloadImageFormDef
from views.steps.export_data_to_js_form_def import ExportDataToJsFormDef
from views.steps.extract_links_form_def import ExtractLinksFormDef
from views.steps.extract_texts_form_def import ExtractTextsFormDef
from views.steps.extract_variable_form_def import ExtractVariableFormDef
from views.steps.jump_to_step_form_def import JumpToStepFormDef
from views.steps.kill_browser_form_def import KillBrowserFormDef
from views.steps.open_url_form_def import OpenUrlFormDef
from views.steps.refresh_page_form_def import RefreshPageFormDef
from views.steps.restart_to_beginning_form_def import RestartToBeginningFormDef
from views.steps.scroll_down_form_def import ScrollDownFormDef
from views.steps.section_form_def import SectionFormDef
from views.steps.wait_fixed_time_form_def import WaitFixedTimeFormDef
from views.steps.wait_html_elements_form_def import WaitHtmlElementsFormDef
from views.steps.wait_html_images_form_def import WaitHtmlImagesFormDef
from views.steps.wait_page_state_form_def import WaitPageStateFormDef
from views.steps.wait_user_action_form_def import WaitUserActionFormDef
from views.steps.youtube_transcripts_form_def import YoutubeTranscriptsFormDef

__all__ = [
    "CheckUrlPageFormDef",
    "ClickForDownloadFormDef",
    "ClickOnElementFormDef",
    "CloseTabsFormDef",
    "CountHtmlElementsFormDef",
    "CountHtmlImagesFormDef",
    "DownloadImageFormDef",
    "ExportDataToJsFormDef",
    "ExtractLinksFormDef",
    "ExtractTextsFormDef",
    "ExtractVariableFormDef",
    "JumpToStepFormDef",
    "KillBrowserFormDef",
    "OpenUrlFormDef",
    "RefreshPageFormDef",
    "RestartToBeginningFormDef",
    "ScrollDownFormDef",
    "SectionFormDef",
    "WaitFixedTimeFormDef",
    "WaitHtmlElementsFormDef",
    "WaitHtmlImagesFormDef",
    "WaitPageStateFormDef",
    "WaitUserActionFormDef",
    "YoutubeTranscriptsFormDef",
]


# EOF
