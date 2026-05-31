"""Per-step presenter modules. Import this package to register all params builders."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from presenters.steps.click_for_download_step_presenter import _build as _b_click_for_dl  # noqa: F401
from presenters.steps.click_on_element_step_presenter import _build as _b_click_on_el  # noqa: F401
from presenters.steps.close_tabs_step_presenter import _build as _b_close_tabs  # noqa: F401
from presenters.steps.count_html_elements_step_presenter import _build as _b_count_html_el  # noqa: F401
from presenters.steps.count_html_images_step_presenter import _build as _b_count_html_img  # noqa: F401
from presenters.steps.download_image_step_presenter import _build as _b_dl_image  # noqa: F401
from presenters.steps.export_data_to_js_step_presenter import _build as _b_export_js  # noqa: F401
from presenters.steps.export_variable_step_presenter import _build as _b_export_var  # noqa: F401
from presenters.steps.extract_links_step_presenter import _build as _b_extract_links  # noqa: F401
from presenters.steps.extract_texts_step_presenter import _build as _b_extract_texts  # noqa: F401
from presenters.steps.jump_to_step_step_presenter import _build as _b_jump_to_step  # noqa: F401
from presenters.steps.kill_browser_step_presenter import _build as _b_kill_browser  # noqa: F401
from presenters.steps.open_url_step_presenter import _build as _b_open_url  # noqa: F401
from presenters.steps.refresh_page_step_presenter import _build as _b_refresh_page  # noqa: F401
from presenters.steps.scroll_down_step_presenter import _build as _b_scroll_down  # noqa: F401
from presenters.steps.section_step_presenter import _build as _b_section  # noqa: F401
from presenters.steps.wait_fixed_time_step_presenter import _build as _b_wait_fixed  # noqa: F401
from presenters.steps.wait_html_elements_step_presenter import _build as _b_wait_html_el  # noqa: F401
from presenters.steps.wait_html_images_step_presenter import _build as _b_wait_html_img  # noqa: F401
from presenters.steps.wait_page_state_step_presenter import _build as _b_wait_page_state  # noqa: F401
from presenters.steps.wait_user_action_step_presenter import _build as _b_wait_user  # noqa: F401
from presenters.steps.youtube_transcripts_step_presenter import _build as _b_yt_transcripts  # noqa: F401


# EOF
