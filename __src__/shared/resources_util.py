## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter.font as tkfont
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# icons
RESS_ICONS = {
    "LOGS": "./__ress__/icons/black_logs.png",
    "OPTIONS": "./__ress__/icons/black_options.png",
    "PROVIDERS": "./__ress__/icons/black_providers.png",
    "WORKFLOW": "./__ress__/icons/black_workflow.png",
    "SCRAPPING": "./__ress__/icons/black_scrapping.png",
}

C_RESS_ICON_LOGS = "./__ress__/icons/black_logs.png"
C_RESS_ICON_OPTIONS = "./__ress__/icons/black_options.png"
C_RESS_ICON_PROVIDERS = "./__ress__/icons/black_providers.png"
C_RESS_ICON_WORKFLOW = "./__ress__/icons/black_workflow.png"
C_RESS_ICON_SCRAPPING = "./__ress__/icons/black_scrapping.png"

# fonts
C_RESS_FONT_NOTO_REGULAR = "./__ress__/fonts/noto_sans_regular.ttf"
C_RESS_FONT_NOTO_BOLD = "./__ress__/fonts/noto_sans_bold.ttf"

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


# super wrapper
def get_resource_icon_16px(path: str) -> ImageTk.PhotoImage:
    """Load and cache an icon image (resize to 16x16).

    If the file cannot be loaded, a fallback placeholder image is returned.

    Args:
        path (str): Path to the image file.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image.
    """
    return ResourcesIcons.get_instance("WHITE_THEME").get_icon(path, (16, 16))


def get_resource_icon_32px(path: str) -> ImageTk.PhotoImage:
    """Load and cache an icon image (resize to 32x32).

    If the file cannot be loaded, a fallback placeholder image is returned.

    Args:
        path (str): Path to the image file.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image.
    """
    return ResourcesIcons.get_instance("WHITE_THEME").get_icon(path, (32, 32))


class ResourcesIcons:
    """Centralized resource manager with singleton instances per resource type.

    This class provides a registry of singleton instances identified by a
    resource type key (e.g., "ICON"). Each instance maintains its own cache.

    Example:
        icon_manager = ResourcesIcons.get_instance("WHITE_THEME")
        icon = icon_manager.get_icon("icon.png", (24, 24))
    """

    _instances: dict[str, "ResourcesIcons"] = {}

    def __init__(self, resource_type: str) -> None:
        """Initialize a resource manager.

        Args:
            resource_type (str): Type identifier (e.g., "ICON").
        """
        self._resource_type = resource_type
        self._cache: dict[tuple[Path, tuple[int, int]], ImageTk.PhotoImage] = {}

    @classmethod
    def get_instance(cls, resource_type: str) -> "ResourcesIcons":
        """Return a singleton instance for a given resource type.

        Args:
            resource_type (str): Resource category key.

        Returns:
            ResourcesIcons: Singleton instance associated with the key.
        """
        if resource_type not in cls._instances:
            cls._instances[resource_type] = cls(resource_type)
        return cls._instances[resource_type]

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        self._cache.clear()

    def get_icon(self, path: str, size: tuple[int, int] = (24, 24)) -> ImageTk.PhotoImage:
        """Load and cache an icon image.

        If the file cannot be loaded, a fallback placeholder image is returned.

        Args:
            path (str): Path to the image file.
            size (Tuple[int, int], optional): Desired icon size (width, height).
                Defaults to (24, 24).

        Returns:
            ImageTk.PhotoImage: Tkinter-compatible image.
        """
        resolved_path = Path(path).resolve()
        key = (resolved_path, size)

        if key not in self._cache:
            try:
                img = Image.open(resolved_path)
                img = img.resize(size, Image.LANCZOS)
            except Exception:
                img = self._create_fallback(size)

            self._cache[key] = ImageTk.PhotoImage(img)

        return self._cache[key]

    @staticmethod
    def _create_fallback(size: tuple[int, int]) -> Image.Image:
        """Create a fallback image (pink square).

        Args:
            size (Tuple[int, int]): Size of the image.

        Returns:
            Image.Image: Generated placeholder image.
        """
        img = Image.new("RGB", size, "#FA25CB")
        draw = ImageDraw.Draw(img)

        # Optional: draw a border for visibility
        draw.rectangle([(0, 0), (size[0] - 1, size[1] - 1)], outline="black")

        return img


## ---------------------------------------------------------------------------


class Resources:
    """Centralized resource manager with singleton instances per resource type.

    This class provides a registry of singleton instances identified by a
    resource type key (e.g., "ICON", "FONT"). Each instance maintains its own
    cache.

    Example:
        font_manager = Resources.get_instance("FONT")
        font = font_manager.get_font(family="Arial", size=12, weight="bold")
    """

    _instances: dict[str, "Resources"] = {}

    def __init__(self, resource_type: str) -> None:
        """Initialize a resource manager.

        Args:
            resource_type (str): Type identifier (e.g., "FONT").
        """
        self._resource_type = resource_type
        self._cache: dict[tuple, tkfont.Font] = {}

    @classmethod
    def get_instance(cls, resource_type: str) -> "Resources":
        """Return a singleton instance for a given resource type.

        Args:
            resource_type (str): Resource category key.

        Returns:
            Resources: Singleton instance associated with the key.
        """
        if resource_type not in cls._instances:
            cls._instances[resource_type] = cls(resource_type)
        return cls._instances[resource_type]

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
            font_manager = Resources.get_instance("FONT")
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


## END
