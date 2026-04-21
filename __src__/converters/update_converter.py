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

class UpdateConverter:
    """Classe de conversion entre entité Métier et Vue d'Édition Tkinter.

    Ce service de mapping bidirectionnel prend soin de copier les valeurs
    littérales tout en préservant l'intégrité des tableaux liés 
    aux listes d'étapes (en effectuant des deepcopies).
    """

    def to_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> UpdateViewModel:
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
        view_model.provider_title.set(provider.provider_title or "Nouv. Fournisseur")
        view_model.provider_filename.set(provider.provider_filename or "nouv._fournisseur.json")
        view_model.url.set(provider.url or "https://")
        view_model.created_date.set(provider.created_date or "")
        view_model.modified_date.set(provider.modified_date or "")
        view_model.version.set(provider.version or "1.0.0")
        
        view_model.browser_displayed.set(provider.browser_displayed)
        view_model.automation_obfuscated.set(provider.automation_obfuscated)
        
        # Deep copy pour éviter de conserver des références partagées
        view_model.steps = copy.deepcopy(provider.steps)
        
        return view_model

    def update_model_from_view_model(self, provider: ProviderModel, view_model: UpdateViewModel) -> ProviderModel:
        """Rétablit les modifications saisies du formulaire vers le modèle métier.

        Ceci représente le retour depuis l'écran et s'exécute généralement
        avant d'appliquer `save_to_file()` dans le repository du fournisseur.
        
        Args:
            provider (ProviderModel): Le modèle métier d'origine à muter.
            view_model (UpdateViewModel): Les valeurs extraites du formulaire Tkinter.

        Returns:
            ProviderModel: Le modèle dont les attributs correspondent dorénavant à 
                la sauvegarde requise.
                
        Exemples d'utilisation:
            >>> model_savable = converter.update_model_from_view_model(prov_orig, form_vm)
            >>> model_savable._repository.save_to_file()
        """
        provider.provider_filename = view_model.provider_filename.get()
        provider.provider_title = view_model.provider_title.get()
        provider.url = view_model.url.get()
        provider.created_date = view_model.created_date.get()
        provider.modified_date = view_model.modified_date.get()
        provider.version = view_model.version.get()
            
        provider.browser_displayed = view_model.browser_displayed.get()
        provider.automation_obfuscated = view_model.automation_obfuscated.get()
        
        provider.steps = copy.deepcopy(view_model.steps)
        
        return provider
