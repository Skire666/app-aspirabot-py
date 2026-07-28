"""Per-step presenter modules. Import this package to register all params builders."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from presenters.steps.check_url_page_step_presenter import _build as _b_check_url_page  # ruff: ignore[unused-import]
from presenters.steps.click_for_download_step_presenter import _build as _b_click_for_dl  # ruff: ignore[unused-import]
from presenters.steps.click_on_element_step_presenter import _build as _b_click_on_el  # ruff: ignore[unused-import]
from presenters.steps.close_tabs_step_presenter import _build as _b_close_tabs  # ruff: ignore[unused-import]
from presenters.steps.count_html_elements_step_presenter import (
    _build as _b_count_html_el,  # ruff: ignore[unused-import]
)
from presenters.steps.count_html_images_step_presenter import _build as _b_count_html_img  # ruff: ignore[unused-import]
from presenters.steps.download_image_step_presenter import _build as _b_dl_image  # ruff: ignore[unused-import]
from presenters.steps.export_data_to_js_step_presenter import _build as _b_export_js  # ruff: ignore[unused-import]
from presenters.steps.extract_js_custom_presenter import _build as _b_extract_js_custom  # ruff: ignore[unused-import]
from presenters.steps.extract_links_step_presenter import _build as _b_extract_links  # ruff: ignore[unused-import]
from presenters.steps.extract_texts_step_presenter import _build as _b_extract_texts  # ruff: ignore[unused-import]
from presenters.steps.extract_variable_step_presenter import _build as _b_export_var  # ruff: ignore[unused-import]
from presenters.steps.jump_to_step_step_presenter import _build as _b_jump_to_step  # ruff: ignore[unused-import]
from presenters.steps.kill_browser_step_presenter import _build as _b_kill_browser  # ruff: ignore[unused-import]
from presenters.steps.open_url_step_presenter import _build as _b_open_url  # ruff: ignore[unused-import]
from presenters.steps.refresh_page_step_presenter import _build as _b_refresh_page  # ruff: ignore[unused-import]
from presenters.steps.restart_to_beginning_step_presenter import (
    _build as _b_restart_to_beginning,  # ruff: ignore[unused-import]
)
from presenters.steps.scroll_down_step_presenter import _build as _b_scroll_down  # ruff: ignore[unused-import]
from presenters.steps.section_step_presenter import _build as _b_section  # ruff: ignore[unused-import]
from presenters.steps.wait_fixed_time_step_presenter import _build as _b_wait_fixed  # ruff: ignore[unused-import]
from presenters.steps.wait_html_elements_step_presenter import _build as _b_wait_html_el  # ruff: ignore[unused-import]
from presenters.steps.wait_html_images_step_presenter import _build as _b_wait_html_img  # ruff: ignore[unused-import]
from presenters.steps.wait_page_state_step_presenter import _build as _b_wait_page_state  # ruff: ignore[unused-import]
from presenters.steps.wait_user_action_step_presenter import _build as _b_wait_user  # ruff: ignore[unused-import]
from presenters.steps.youtube_infos_video_presenter import (
    _build as _b_youtube_infos_video,  # ruff: ignore[unused-import]
)
from presenters.steps.youtube_subtitles_presenter import _build as _b_youtube_subtitles  # ruff: ignore[unused-import]


# EOF
