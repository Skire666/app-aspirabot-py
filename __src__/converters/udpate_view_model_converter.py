"""Convertisseur pour l'outil de création ou modification des fournisseurs.

Ce module inclut la classe `UpdateConverter` dont l'objectif
est de traduire un `ProviderModel` (json asynchrone) en formulaire 
lisible (ViewModel de Tkinter variables) dans les deux directions.
"""

import copy
from models.provider_model import ProviderModel
from view_models.update_view_model import UpdateViewModel

class UpdateViewModelConverter:
    """Classe de conversion entre entité Métier et Vue d'Édition Tkinter.
    
    Ce service de mapping bidirectionnel prend soin de copier les valeurs
    littérales tout en préservant l'intégrité des tableaux liés
    """

    @staticmethod

    def to_provider_model(view_model: UpdateViewModel, provider_model: ProviderModel) -> ProviderModel:
        """Rétablit les modifications saisies du formulaire vers le modèle métier.

        Ceci représente le retour depuis l'écran et s'exécute généralement
        avant d'appliquer `save_to_file()` dans le repository du fournisseur.
        
        Args:
            provider (ProviderModel): Le modèle métier d'origine à muter.
            view_model (UpdateViewModel): Les valeurs extraites du formulaire Tkinter.

        Returns:
            ProviderModel: Le modèle dont les attributs correspondent dorénavant à 
                la sauvegarde requise.
        """
        provider_model.provider_guid = view_model.provider_guid.get()
        provider_model.provider_title = view_model.provider_title.get()

        provider_model.url = view_model.url.get()
        provider_model.browser_displayed = view_model.browser_displayed.get()
        provider_model.automation_obfuscated = view_model.automation_obfuscated.get()

        provider_model.created_date = view_model.created_date.get()
        provider_model.modified_date = view_model.modified_date.get()

        provider_model.version = view_model.version.get()
        provider_model.steps = copy.deepcopy(view_model.steps)
        
        return provider_model
