"""Convertisseur de modèles pour la liste des fournisseurs.

Ce module contient la classe `ProvidersListConverter` chargée de transformer
les données métier issues des `ProviderModel` en objets de type `ProviderItemViewModel`,
lesquels sont optimisés pour l'affichage dans l'interface liste Tkinter.

Exemples d'utilisation:
    >>> converter = ProvidersListConverter()
    >>> vm_rempli = converter.to_view_model([(provider1, "fichier1")], ViewModelVierge())
"""

from models.provider_model import ProviderModel
from view_models.providers_list_view_model import ProviderItemViewModel

class ProvidersListConverter:
    """Outil de conversion entre données métier et données de vue pour les fournisseurs.

    Agit comme une couche d'abstraction garantissant que l'UI (`ProvidersListViewModel`)
    ne manipule pas directement le modèle persistant `ProviderModel`, respectant
    ainsi l'architecture MVVM/MVC.
    """

    @staticmethod
    def to_item_view_model(provider: ProviderModel) -> ProviderItemViewModel:
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
        return ProviderItemViewModel(
            provider_guid=provider.provider_guid,
            provider_title=provider.provider_title,
            url=provider.url,
            created_date=provider.created_date,
            modified_date=provider.modified_date,
            version=provider.version
        )
