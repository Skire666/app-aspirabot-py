from pathlib import Path


def get_current_working_directory() -> Path:
    """Get the current working directory as a Path object.

    Returns:
        Path: The current working directory as a Path object.

    Example:
        ## python ./_src_/main.py
        cwd = get_current_working_directory()
        print(cwd)  # Output: Path('./')
    """
    return Path.cwd()


def make_all_folders_if_not_exists(path: Path | str) -> None:
    """Create all parent folders for the given path if they do not exist.

    Args:
        path (Path): The file path for which to create parent folders.

    Example:
        make_all_folders_if_not_exists(Path('./data_providers/provider1.json'))
        # This will create the 'data_providers' folder if it does not exist.
    """
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


## END
