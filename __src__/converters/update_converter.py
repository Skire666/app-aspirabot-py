from models.provider_model import ProviderModel
from view_models.update_view_model import UpdateViewModel

class UpdateConverter:
    """Classe de conversion entre Modèle et ViewModel."""

    def to_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> UpdateViewModel:
        """Convertit un ProviderModel en UpdateViewModel."""
        view_model.provider_alias.set(provider.provider_alias or "Nouveau Fournisseur")
        view_model.provider_filename.set(provider.provider_filename or "nouveau_fournisseur")
        view_model.url.set(provider.url or "https://")
        view_model.created_date.set(provider.created_date or "")
        view_model.version.set(provider.version or "1.0.0")
        
        view_model.headless.set(provider.headless)
        
        # Deep copy list
        import copy
        view_model.steps = copy.deepcopy(provider.steps)
        
        return view_model

    def update_model_from_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> ProviderModel:
        """Met à jour un ProviderModel à partir des données de l'UpdateViewModel."""
        provider.provider_filename = view_model.provider_filename.get()
        provider.provider_alias = view_model.provider_alias.get()
        provider.url = view_model.url.get()
        provider.created_date = view_model.created_date.get()
        provider.version = view_model.version.get()
            
        provider.headless = view_model.headless.get()
        
        import copy
        provider.steps = copy.deepcopy(view_model.steps)
        
        return provider
