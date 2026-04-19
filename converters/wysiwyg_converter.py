"""Convertisseur pour le module WYSIWYG.

Ce module définit `WysiwygConverter`, responsable de la conversion
entre `ProviderModel` (domaine) et `WysiwygViewModel` (IHM).
"""

from typing import Optional

from models.provider_model import ProviderModel
from view_models.wysiwyg_view_model import WysiwygViewModel

class WysiwygConverter:
    """Convertit entre ProviderModel et WysiwygViewModel."""

    @staticmethod
    def to_view_model(model: ProviderModel, view_model: Optional[WysiwygViewModel] = None) -> WysiwygViewModel:
        """Convertit un ProviderModel en WysiwygViewModel."""
        tags_str: str = ", ".join(model.tags) if model.tags else ""
        
        if view_model is None:
            view_model = WysiwygViewModel()
            
        view_model.provider_name.set(model.provider_name)
        view_model.url.set(model.url)
        view_model.created_date.set(model.created_date)
        view_model.version.set(model.version)
        view_model.tags_str.set(tags_str)
        view_model.headless.set(bool(model.headless))
        import copy
        view_model.steps = copy.deepcopy(model.steps) if hasattr(model, 'steps') else []
        
        return view_model

    @staticmethod
    def update_model_from_view_model(model: ProviderModel, view_model: WysiwygViewModel) -> None:
        """Met à jour un ProviderModel à partir des données d'un WysiwygViewModel."""
        model.provider_name = view_model.provider_name.get()
        model.url = view_model.url.get()
        model.created_date = view_model.created_date.get()
        model.version = view_model.version.get()
        
        # Conversion de la chaîne de tags en liste
        tags_raw = view_model.tags_str.get().split(',')
        model.tags = [t.strip() for t in tags_raw if t.strip()]
        
        model.headless = view_model.headless.get()
        import copy
        model.steps = copy.deepcopy(view_model.steps)
