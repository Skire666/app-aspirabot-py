import datetime
import re

class StringHelper:
    @staticmethod
    def concat_datetime2_and_extension(base_string: str, extension: str) -> str:
        """
        Ajoute un horodatage (format yyyy_mm_dd_hh_mm_ss_sss) et une extension à une chaîne.
        
        Exemple:
            base_string = "logfile"
            extension = "txt"
            Résultat: "logfile_2024_06_01_15_30_45_123.txt"
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
        """
        Ajoute un horodatage (format yyyy) et une extension à une chaîne.
        
        Exemple:
            base_string = "logfile"
            extension = "txt"
            Résultat: "logfile_2024.txt"
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
        """
        Sécurise une chaîne pour qu'elle puisse être utilisée comme nom de fichier.
        Remplace les espaces par des underscores, supprime les caractères interdits, et convertit en minuscules.
        Exemple:
            name = "Mon Fournisseur: Version 1.0"
            Résultat: "mon_fournisseur_version_1.0"
        """
        safized_name = name.replace(" ", "_").replace("-", "").replace(":", "")
        safized_name = re.sub(r'[^a-zA-Z0-9_.\-]', '', safized_name.strip()).lower()
        return safized_name
