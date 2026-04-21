"""Convertisseur de modèles pour la liste des fournisseurs.

Ce module contient la classe `ProvidersListConverter` chargée de transformer
les données métier issues des `ProviderModel` en objets de type `ProviderItemViewModel`,
lesquels sont optimisés pour l'affichage dans l'interface liste Tkinter.

Exemples d'utilisation:
    >>> converter = ProvidersListConverter()
    >>> vm_rempli = converter.to_view_model([(provider1, "fichier1")], ViewModelVierge())
"""

from typing import List, Tuple
from models.provider_model import ProviderModel
from view_models.providers_list_view_model import ProviderItemViewModel, ProvidersListViewModel

class ProvidersListConverter:
    """Outil de conversion entre données métier et données de vue pour les fournisseurs.

    Agit comme une couche d'abstraction garantissant que l'UI (`ProvidersListViewModel`)
    ne manipule pas directement le modèle persistant `ProviderModel`, respectant
    ainsi l'architecture MVVM/MVC.
    """

    def to_item_view_model(self, provider: ProviderModel, stem: str) -> ProviderItemViewModel:
        """Transforme un fournisseur métier en un élément de vue individuel.

        Args:
            provider (ProviderModel): L'instance métier du fournisseur.
            stem (str): Le nom du fichier de ce fournisseur sans extension.

        Returns:
            ProviderItemViewModel: Une instance de données prêtes pour l'affichage UI,
            avec des valeurs de repli (fallback) lorsque champs vides.

        Exemples d'utilisation:
            >>> item_vm = converter.to_item_view_model(provider, "mon_site")
        """
        provider_filename = provider.provider_filename or stem
        return ProviderItemViewModel(
            provider_filename=provider_filename,
            provider_title=provider.provider_title or provider_filename,
            url=provider.url or "",
            created_date=provider.created_date or "",
            modified_date=provider.modified_date or "",
            version=provider.version or "1.0.0"
        )

    def to_view_model(self, providers_tuples: List[Tuple[ProviderModel, str]], view_model: ProvidersListViewModel) -> ProvidersListViewModel:
        """Remplit ou actualise un ViewModel de liste à partir d'un groupe métier.

        Args:
            providers_tuples (List[Tuple[ProviderModel, str]]): Une liste de paires
                contenant le modèle du fournisseur et le nom de son fichier.
            view_model (ProvidersListViewModel): L'instance ViewModel existante à alimenter.

        Returns:
            ProvidersListViewModel: L'objet ViewModel mis à jour de ses éléments
            et dont le compteur textuel a été recalculé.
            
        Exemples d'utilisation:
            >>> converter.to_view_model([(prov, "prov")], global_vm)
        """
        view_model.providers = [self.to_item_view_model(p[0], p[1]) for p in providers_tuples]
        view_model.update_count()
        return view_model
