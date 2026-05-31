# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# black big buttons
C_RESS_ICON_BLACK_LOGS = "./__ress__/icons/b_128_logs.png"
C_RESS_ICON_BLACK_PROFILES = "./__ress__/icons/b_128_profiles.png"
C_RESS_ICON_BLACK_SCENARIOS = "./__ress__/icons/b_128_scenarios.png"
C_RESS_ICON_BLACK_EDITOR = "./__ress__/icons/b_128_editor.png"
C_RESS_ICON_BLACK_EXECUTOR = "./__ress__/icons/b_128_executor.png"
C_RESS_ICON_BLACK_SCRAPING = "./__ress__/icons/b_128_scraping.png"
C_RESS_ICON_BLACK_FAQ = "./__ress__/icons/b_128_faq.png"
C_RESS_ICON_BLACK_CONFIG = "./__ress__/icons/b_128_options.png"
C_RESS_ICON_BLACK_DEBUG = "./__ress__/icons/b_128_debug.png"

# white big buttons
C_RESS_ICON_WHITE_LOGS = "./__ress__/icons/w_128_logs.png"
C_RESS_ICON_WHITE_PROFILES = "./__ress__/icons/w_128_profiles.png"
C_RESS_ICON_WHITE_SCENARIOS = "./__ress__/icons/w_128_scenarios.png"
C_RESS_ICON_WHITE_EDITOR = "./__ress__/icons/w_128_editor.png"
C_RESS_ICON_WHITE_EXECUTOR = "./__ress__/icons/w_128_executor.png"
C_RESS_ICON_WHITE_SCRAPING = "./__ress__/icons/w_128_scraping.png"
C_RESS_ICON_WHITE_FAQ = "./__ress__/icons/w_128_faq.png"
C_RESS_ICON_WHITE_CONFIG = "./__ress__/icons/w_128_options.png"
C_RESS_ICON_WHITE_DEBUG = "./__ress__/icons/w_128_debug.png"

# white small icons
C_RESS_ICON_WHITE_COPY = "./__ress__/icons/w_128_copy.png"
C_RESS_ICON_WHITE_DELETE = "./__ress__/icons/w_128_delete.png"
C_RESS_ICON_WHITE_DOWN = "./__ress__/icons/w_128_down.png"
C_RESS_ICON_WHITE_EDIT = "./__ress__/icons/w_128_edit.png"
C_RESS_ICON_WHITE_UP = "./__ress__/icons/w_128_up.png"
C_RESS_ICON_WHITE_TOGGLE_ON = "./__ress__/icons/w_128_toggle_on.png"
C_RESS_ICON_WHITE_TOGGLE_OFF = "./__ress__/icons/w_128_toggle_off.png"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


# super wrapper
def get_resource_icon_24px(path: str) -> ImageTk.PhotoImage:
    """Load and cache an icon image (resize to 24x24).

    If the file cannot be loaded, a fallback placeholder image is returned.

    Args:
        path (str): Path to the image file.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image.
    """
    return ResourcesIcons().get_icon(path, (24, 24))


def get_resource_icon_32px(path: str) -> ImageTk.PhotoImage:
    """Load and cache an icon image (resize to 32x32).

    If the file cannot be loaded, a fallback placeholder image is returned.

    Args:
        path (str): Path to the image file.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible image.
    """
    return ResourcesIcons().get_icon(path, (32, 32))


def get_resource_icon_32px_disabled(path: str) -> ImageTk.PhotoImage:
    """Load and cache a faded 32x32 icon for use in a disabled state.

    Applies a 40 % opacity mask so the icon reads as visually inactive
    against the sidebar's normal background without altering its colour.

    Args:
        path: Path to the source icon file.

    Returns:
        ImageTk.PhotoImage: Tkinter-compatible faded icon.
    """
    return ResourcesIcons().get_icon_disabled(path, (32, 32))


class ResourcesIcons:
    """Centralized resource manager with singleton instances per resource type.

    This class provides a registry of singleton instances identified by a
    resource type key (e.g., "ICON"). Each instance maintains its own cache.
    """

    _instance: ResourcesIcons | None = None

    def __new__(cls) -> ResourcesIcons:
        """Initialize a resource manager.

        Args:
            resource_type (str): Type identifier (e.g., "ICON").
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = {}
        return cls._instance

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
                img = img.resize(size, Image.BILINEAR)
            except Exception:  # noqa: BLE001
                img = self._create_fallback(size)

            self._cache[key] = ImageTk.PhotoImage(img)

        return self._cache[key]

    def get_icon_disabled(self, path: str, size: tuple[int, int]) -> ImageTk.PhotoImage:
        """Load, resize, and cache an icon with a faded disabled appearance.

        Uses a dedicated cache key so the normal and disabled variants coexist
        without evicting each other.

        Args:
            path: Path to the image file.
            size: Desired icon dimensions (width, height).

        Returns:
            ImageTk.PhotoImage: Tkinter-compatible faded image.
        """
        resolved_path = Path(path).resolve()
        key = (resolved_path, size, "disabled")

        if key not in self._cache:
            try:
                img = Image.open(resolved_path).resize(size, Image.BILINEAR)
            except Exception:  # noqa: BLE001
                img = self._create_fallback(size)
            self._cache[key] = ImageTk.PhotoImage(self._apply_disabled_effect(img))

        return self._cache[key]

    @staticmethod
    def _apply_disabled_effect(img: Image.Image) -> Image.Image:
        """Return a copy of img with 40 % opacity to signal a disabled state.

        The image is converted to RGBA so the alpha channel can be scaled
        without altering colour information, regardless of the source mode.

        Args:
            img: Source PIL image (any mode).

        Returns:
            Image.Image: RGBA image with reduced opacity.
        """
        img = img.convert("RGBA")
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * 0.4))
        return Image.merge("RGBA", [r, g, b, a])

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


# EOF
