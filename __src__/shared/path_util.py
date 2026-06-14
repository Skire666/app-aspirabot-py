# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import string
from pathlib import Path

ALLOWED = set(string.ascii_letters + string.digits + "-_. ()")


def clean_filename_youtube(name: str) -> str:
    """Clean a string to be safe for use as a filename by removing or replacing invalid characters.

    Args:
        name: The original filename string to clean.

    Returns:
        A cleaned version of the filename string containing only allowed characters.
    """
    return "".join(c for c in name if c in ALLOWED)


def get_current_working_directory() -> Path:
    """Get the current working directory as a Path object.

    Returns:
        Path: The current working directory as a Path object.
    """
    return Path.cwd()


def make_all_folders_if_not_exists(path: Path | str, *, is_file_path: bool | None = None) -> None:
    """Create all folders for a directory path or a file path's parent.

    Args:
        path: Directory path to create, or file path whose parent folders should
            be created.
        is_file_path: Force file or directory behavior. When None, the function
            infers the intent from the existing path or file suffix. Set this to
            False for directory names that include dots.
    """
    target_path = Path(path)
    if is_file_path is True:
        # For file paths, we want to create the parent directory, not the file itself.
        target_path = target_path.parent
    elif is_file_path is False:
        # For directory paths, we use the path as-is.
        target_path = target_path
    elif target_path.exists():
        # If the path exists, we can check if it's a file or directory to determine the target.
        target_path = target_path if target_path.is_dir() else target_path.parent
    elif target_path.suffix:
        # If the path doesn't exist but has a suffix, we can infer it's meant to be a file.
        target_path = target_path.parent
    # If the path doesn't exist and has no suffix, we can infer it's meant to be a directory, so we use it as-is.
    target_path.mkdir(parents=True, exist_ok=True)


def folder_exists(path: Path | str) -> bool:
    """Check if a folder exists at the given path.

    Args:
        path: The path to check.

    Returns:
        bool: True if the folder exists, False otherwise.
    """
    return Path(path).is_dir()


def count_files_in_folder(path: Path | str, file_extension: str) -> int:
    """Count the number of files with a specific extension in a folder.

    Args:
        path: The path to the folder.
        file_extension: The file extension to count.

    Returns:
        int: The number of files with the specified extension.
    """
    folder_path = Path(path)
    if not folder_path.is_dir():
        return 0
    return len(list(folder_path.glob(f"*.{file_extension}")))


# EOF
