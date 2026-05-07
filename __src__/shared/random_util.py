## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import secrets

from shared.exception_util import ValueMustBePositiveAndEvenError

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# forbidden characters: i, l, n, o, r, s, u, v, z AND 0, 1, 2 -> to avoid confusion with 0o, I1l, uv, AR...
# and ensure strings are easily distinguishable and less prone to errors when read or transcribed.
_ALPHABET_PATTERN = "aAbBcCdDeEFgGHkNpPqtTxyZY23456789"

## ---------------------------------------------------------------------------
## Classes & Functions
## ---------------------------------------------------------------------------

g_unique_list_id_step = set()


def merge_unique_list_id_step(new_ids: set[str]) -> None:
    """Merges a new set of IDs into the global unique ID set.

    Args:
        new_ids: A set of new IDs to merge.
    """
    if len(new_ids) <= 0:
        return
    g_unique_list_id_step.union(new_ids)


def generate_rng_id_step() -> str:
    """Generates a random string using a custom alphabet.

    Args:
        nbr_char: Number of characters in the random string (must be positive).

    Returns:
        A random string of the specified length.

    Example:
        >>> generate_rng_id_step()
        'g5k3'  # Example output, actual result will vary each time.

    Raises:
        ValueError: If nbr_char is not a positive integer.
    """
    max_retry_wtf = 99999
    while max_retry_wtf > 0:
        max_retry_wtf -= 1
        value = "".join(secrets.choice(_ALPHABET_PATTERN) for _ in range(4))
        if value not in g_unique_list_id_step:
            g_unique_list_id_step.add(value)
            return value

    ## +2 char ?
    return "".join(secrets.choice(_ALPHABET_PATTERN) for _ in range(6))


def generate_rng_hexastring(nbr_char: int) -> str:
    """Generates a list of unique random strings.

    Args:
        size_list: Number of unique strings to generate.
        nbr_char: Number of characters in each random string (must be even).

    Returns:
        List of unique random strings.

    Example:
        >>> generate_rng_hexastring(8)
        'a3f5c9b2'  # Example output, actual result will vary each time.

    Raises:
        ValueError: If nbr_char is not a positive even integer or if size_list is not a positive integer.
    """
    if nbr_char <= 0 or (nbr_char % 2) != 0:
        raise ValueMustBePositiveAndEvenError()

    return secrets.token_hex(nbr_char // 2)  # Generates a random string of length


## EOF
