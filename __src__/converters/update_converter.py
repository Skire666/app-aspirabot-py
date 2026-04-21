from models.provider_model import ProviderModel
from view_models.update_view_model import UpdateViewModel

class UpdateConverter:
    """Classe de conversion entre Modèle et ViewModel."""

    def to_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> UpdateViewModel:
        """Convertit un ProviderModel en UpdateViewModel."""
        view_model.provider_title.set(provider.provider_title or "Nouv. Fournisseur")
        view_model.provider_filename.set(provider.provider_filename or "nouv_fournisseur")
        view_model.url.set(provider.url or "https://")
        view_model.created_date.set(provider.created_date or "")
        view_model.modified_date.set(provider.modified_date or "")
        view_model.version.set(provider.version or "1.0.0")
        
        view_model.browser_displayed.set(provider.browser_displayed)
        view_model.automation_obfuscated.set(provider.automation_obfuscated)
        
        # Deep copy list
        import copy
        view_model.steps = copy.deepcopy(provider.steps)
        
        return view_model

    def update_model_from_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> ProviderModel:
        """Met à jour un ProviderModel à partir des données de l'UpdateViewModel."""
        provider.provider_filename = view_model.provider_filename.get()
        provider.provider_title = view_model.provider_title.get()
        provider.url = view_model.url.get()
        provider.created_date = view_model.created_date.get()
        provider.modified_date = view_model.modified_date.get()
        provider.version = view_model.version.get()
            
        provider.browser_displayed = view_model.browser_displayed.get()
        provider.automation_obfuscated = view_model.automation_obfuscated.get()
        
        import copy
        provider.steps = copy.deepcopy(view_model.steps)
        
        return provider
