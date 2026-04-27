"""Factory creating step-specific form views."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, TypeGuard

from interfaces.base_step_form_view import BaseStepFormView
from models.step_scrapping_model import StepType, StepValue
from views.step_forms.check_if_image_here_step_form_view import CheckIfImageHereStepFormView
from views.step_forms.click_element_step_form_view import ClickElementStepFormView
from views.step_forms.download_image_step_form_view import DownloadImageStepFormView
from views.step_forms.open_url_step_form_view import OpenUrlStepFormView
from views.step_forms.refresh_page_step_form_view import RefreshPageStepFormView
from views.step_forms.wait_seconds_step_form_view import WaitSecondsStepFormView


def _is_step_type(value: str) -> TypeGuard[StepType]:
    return value in {
        "open_url", "wait_seconds", "refresh_page",
        "download_image", "check_if_image_here", "click_element",
    }


class StepFormViewFactory:
    """Creates form sub-views by step type without leaking mapping into parent views."""

    _FORM_TYPES: dict[StepType, Callable[..., BaseStepFormView]] = {
        "open_url": OpenUrlStepFormView,
        "wait_seconds": WaitSecondsStepFormView,
        "refresh_page": RefreshPageStepFormView,
        "download_image": DownloadImageStepFormView,
        "check_if_image_here": CheckIfImageHereStepFormView,
        "click_element": ClickElementStepFormView,
    }

    def create(self, parent: tk.Widget, step_type: str, initial_value: StepValue = None) -> BaseStepFormView | None:
        """Returns a form view instance for a supported type, otherwise None."""
        if not _is_step_type(step_type):
            return None
        form_cls = self._FORM_TYPES[step_type]
        return form_cls(parent=parent, initial_value=initial_value)
