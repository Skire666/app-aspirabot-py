from typing import List
from models.provider_model import ProviderModel
from view_models.providers_list_view_model import ProviderItemViewModel, ProvidersListViewModel

class ProvidersListConverter:
    """Convertisseur pour la liste des fournisseurs."""

    def to_item_view_model(self, provider: ProviderModel, stem: str) -> ProviderItemViewModel:
        provider_filename = provider.provider_filename or stem
        return ProviderItemViewModel(
            provider_filename=provider_filename,
            provider_title=provider.provider_title or provider_filename,
            url=provider.url or "",
            created_date=provider.created_date or "",
            modified_date=provider.modified_date or "",
            version=provider.version or "1.0.0"
        )

    def to_view_model(self, providers_tuples: List[tuple[ProviderModel, str]], view_model: ProvidersListViewModel) -> ProvidersListViewModel:
        """Remplit le ViewModel avec une liste de ProviderModels."""
        view_model.providers = [self.to_item_view_model(p[0], p[1]) for p in providers_tuples]
        view_model.update_count()
        return view_model
