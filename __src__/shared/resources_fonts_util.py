# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter.font as tkfont

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# TODO PCO
# on ne peut pas installer de font, donc faut prendre existant sur le système
# ou alors fournir une font dans les ressources et l'installer à l'exécution (mais c'est plus lourd)
# le mieux de ce que j'ai lu c'est de faire un rendering de la font via PIL et de l'afficher en image dans Tkinter
# mais c'est plus complexe à implémenter
# le seul truc simple c'est de faire un fallback sur une font classique du système (ex: Arial, Helvetica, etc.)
# et encore, quid de la taille de la police, l'empatement, etc.
# ça peut faire des différences d'affichage selon les systèmes...

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ResourcesFonts:
    """Centralized resource manager with singleton instance.

    This class provides a singleton instance for managing cached resources
    like fonts.

    Example:
        font_manager = Resources.get_instance()
        font = font_manager.get_font(family="Arial", size=12, weight="bold")
    """

    _instance: "ResourcesFonts" | None = None

    def __new__(cls) -> "ResourcesFonts":
        """Initialize a resource manager.

        Returns:
            Resources: Singleton instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        self._cache.clear()

    def get_font(
        self,
        family: str = "Segoe UI",
        size: int = 12,
        weight: str = "normal",
        slant: str = "roman",
        underline: bool = False,
        overstrike: bool = False,
        fallback_family: str = "TkDefaultFont",
    ) -> tkfont.Font:
        """Load and cache a Tkinter font.

        If the requested font family is not available on the system,
        a fallback font will be used.

        Args:
            family (str, optional): Font family name. Defaults to "Segoe UI".
            size (int, optional): Font size. Defaults to 12.
            weight (str, optional): "normal" or "bold". Defaults to "normal".
            slant (str, optional): "roman" or "italic". Defaults to "roman".
            underline (bool, optional): Underline text. Defaults to False.
            overstrike (bool, optional): Strike-through text. Defaults to False.
            fallback_family (str, optional): Fallback font family if unavailable.
                Defaults to "TkDefaultFont".

        Returns:
            tkfont.Font: Tkinter font instance.

        Example:
            font_manager = ResourcesFonts.get_instance()
            font = font_manager.get_font(family="Segoe UI", size=14, weight="bold")
        """
        key = (family, size, weight, slant, underline, overstrike)

        if key not in self._cache:
            available_fonts = set(tkfont.families())

            selected_family = family if family in available_fonts else fallback_family

            font = tkfont.Font(
                family=selected_family,
                size=size,
                weight=weight,
                slant=slant,
                underline=underline,
                overstrike=overstrike,
            )

            self._cache[key] = font

        return self._cache[key]


# END
