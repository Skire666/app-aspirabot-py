"""Convertisseur pour l'outil de création ou modification des fournisseurs.

Ce module inclut la classe `UpdateConverter` dont l'objectif
est de traduire un `ProviderModel` (json asynchrone) en formulaire 
lisible (ViewModel de Tkinter variables) dans les deux directions.

Exemples d'utilisation:
    >>> controller = UpdateConverter()
    >>> vue = controller.to_view_model(modele, UpdateViewModel())
"""

import copy
from models.provider_model import ProviderModel
from view_models.update_view_model import UpdateViewModel

class ProviderModelConverter:
    """Classe de conversion entre entité Métier et Vue d'Édition Tkinter.

    Ce service de mapping bidirectionnel prend soin de copier les valeurs
    littérales tout en préservant l'intégrité des tableaux liés 
    aux listes d'étapes (en effectuant des deepcopies).
    """

    @staticmethod
    def to_view_model(provider: ProviderModel, view_model: UpdateViewModel) -> UpdateViewModel:
        """Transfère les données métier en objets UI Tkinter exploitables (Variables).

        Args:
            provider (ProviderModel): Le modèle métier racine.
            view_model (UpdateViewModel): Le modèle contenant des `tk.StringVar`/`BooleanVar`
                sur le point d'être injectées sur l'écran d'édition.

        Returns:
            UpdateViewModel: L'objet ViewModel mis à jour.
            
        Exemples d'utilisation:
            >>> vm_update = converter.to_view_model(p_model, UpdateViewModel())
        """
        view_model.provider_id.set(provider.provider_id)
        view_model.provider_title.set(provider.provider_title)
        view_model.url.set(provider.url)
        view_model.browser_displayed.set(provider.browser_displayed)
        view_model.automation_obfuscated.set(provider.automation_obfuscated)
        view_model.created_date.set(provider.created_date)
        view_model.modified_date.set(provider.modified_date)
        view_model.version.set(provider.version)
        
        # Deep copy pour éviter de conserver des références partagées
        view_model.steps = copy.deepcopy(provider.steps)
        
        return view_model
