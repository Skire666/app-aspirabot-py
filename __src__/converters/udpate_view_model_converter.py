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

    def to_provider_model(view_model: UpdateViewModel) -> ProviderModel:
        """Rétablit les modifications saisies du formulaire vers le modèle métier.

        Ceci représente le retour depuis l'écran et s'exécute généralement
        avant d'appliquer `save_to_file()` dans le repository du fournisseur.
        
        Args:
            view_model (UpdateViewModel): Les valeurs extraites du formulaire Tkinter.

        Returns:
            ProviderModel: Le modèle dont les attributs correspondent dorénavant à 
                la sauvegarde requise.
        """
        return ProviderModel(
            provider_guid=view_model.provider_guid.get(),
            provider_title=view_model.provider_title.get(),
            url=view_model.url.get(),
            browser_displayed=view_model.browser_displayed.get(),
            automation_obfuscated=view_model.automation_obfuscated.get(),
            created_date=view_model.created_date.get(),
            modified_date=view_model.modified_date.get(),
            version=view_model.version.get(),
            steps=copy.deepcopy(view_model.steps)
        )
