"""Module d'assistance pour le traitement des chaînes de caractères.

Ce module fournit des méthodes statiques dans la classe `StringHelper` 
pour la manipulation avancée des chaînes, notamment l'ajout d'horodatages
et la sanitarisation pour une utilisation sûre dans les chemins de fichiers.
"""

import datetime
import re

class StringHelper:
    """Classe utilitaire pour la manipulation de chaînes de caractères.
    
    Cette classe regroupe des méthodes statiques qui ne nécessitent pas
    d'instanciation de la classe. Elle facilite le renommage sécurisé de fichiers
    et l'ajout d'horodatages.
    """

    @staticmethod
    def concat_datetime2_and_extension(base_string: str, extension: str) -> str:
        """Ajoute un horodatage précis et une extension à une chaîne de base.
        
        L'horodatage utilisé a le format suivant : aaaa_mm_jj_hh_mm_ss_sss
        (année, mois, jour, heures, minutes, secondes, millisecondes).

        Args:
            base_string (str): La chaîne de base (par exemple, un nom de fichier sans extension).
            extension (str): L'extension du fichier (avec ou sans le point initial).

        Returns:
            str: La chaîne concaténée avec l'horodatage et l'extension.

        Raises:
            ValueError: Si `base_string` ou `extension` sont vides ou évalués à Faux après nettoyage.
            RuntimeError: Si une erreur inattendue se produit lors du calcul de la date.

        Exemples d'utilisation:
            >>> StringHelper.concat_datetime2_and_extension("logfile", "txt")
            'logfile_2024_06_01_15_30_45_123.txt'
        """
        base_string = base_string.strip()
        extension = extension.strip()
        
        ## Validation des entrées
        if not base_string:
            raise ValueError("Le paramètre 'base_string' ne peut pas être vide.")
        if not extension:
            raise ValueError("Le paramètre 'extension' ne peut pas être vide.")
            
        # Supprimer le point de l'extension s'il est présent
        if extension.startswith('.'):
            extension = extension[1:]
            
        try:
            now = datetime.datetime.now()
            # %f donne les microsecondes (6 chiffres). On divise par 1000 pour avoir les millisecondes (3 chiffres).
            timestamp = now.strftime("%Y_%m_%d_%H_%M_%S") + f"_{now.microsecond // 1000:03d}"
            
            return f"{base_string}_{timestamp}.{extension}"
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la génération de la chaîne avec horodatage : {e}")

    @staticmethod
    def concat_yyyy_and_extension(base_string: str, extension: str) -> str:
        """Ajoute l'année courante en cours comme horodatage et une extension à une chaîne.
        
        L'horodatage utilisé est formaté en année (aaaa).

        Args:
            base_string (str): La chaîne de base (ex: nom de fichier).
            extension (str): L'extension de fichier à ajouter.

        Returns:
            str: La nouvelle chaîne incluant l'année et l'extension.

        Raises:
            ValueError: Si `base_string` ou `extension` sont manquants.
            RuntimeError: En cas d'échec de la récupération ou de la création de la nouvelle chaîne.

        Exemples d'utilisation:
            >>> StringHelper.concat_yyyy_and_extension("logfile", "txt")
            'logfile_2024.txt'
        """
        base_string = base_string.strip()
        extension = extension.strip()
        
        ## Validation des entrées
        if not base_string:
            raise ValueError("Le paramètre 'base_string' ne peut pas être vide.")
        if not extension:
            raise ValueError("Le paramètre 'extension' ne peut pas être vide.")
            
        # Supprimer le point de l'extension s'il est présent
        if extension.startswith('.'):
            extension = extension[1:]
            
        try:
            now = datetime.datetime.now()
            # %f donne les microsecondes (6 chiffres). On divise par 1000 pour avoir les millisecondes (3 chiffres).
            timestamp = now.strftime("%Y")
            
            return f"{base_string}_{timestamp}.{extension}"
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la génération de la chaîne avec horodatage : {e}")

    @staticmethod
    def mega_safized_string_for_futur_path(name: str) -> str:
        """Sécurise et normalise une chaîne de caractères pour un chemin de fichier.
        
        Remplace les espaces par des underscores, supprime les caractères potentiellement 
        dangereux ou interdits sur la plupart des systèmes de fichiers, et convertit tout en minuscules.

        Args:
            name (str): La chaîne originale à nettoyer.

        Returns:
            str: La chaîne nettoyée et prête à être utilisée comme nom de fichier ou chemin.

        Exemples d'utilisation:
            >>> StringHelper.mega_safized_string_for_futur_path("Mon Fournisseur: Version 1.0")
            'mon_fournisseur_version_1.0'
        """
        safized_name = name.replace(" ", "_").replace("-", "").replace(":", "")
        safized_name = re.sub(r'[^a-zA-Z0-9_.\-]', '', safized_name.strip()).lower()
        return safized_name
