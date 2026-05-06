import secrets

from shared.exception_util import ValueMustBePositiveAndEvenError

# forbidden characters: i, l, n, o, r, s, u, v, z AND 0, 1, 2 -> to avoid confusion with 0o, I1l, uv, AR...
# and ensure strings are easily distinguishable and less prone to errors when read or transcribed.
_ALPHABET_PATTERN = "aAbBcCdDeEFgGHkmpPqtxyZY23456789"


def generate_rng_hexastring_with_alphabet(nbr_char: int) -> str:
    """Generates a random string using a custom alphabet.

    Args:
        nbr_char: Number of characters in the random string (must be positive).

    Returns:
        A random string of the specified length.

    Example:
        >>> generate_rng_hexastring_with_alphabet(8)
        'g5k3m8p2'  # Example output, actual result will vary each time.

    Raises:
        ValueError: If nbr_char is not a positive integer.
    """
    if nbr_char <= 0:
        raise ValueMustBePositiveAndEvenError()

    return "".join(secrets.choice(_ALPHABET_PATTERN) for _ in range(nbr_char))


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
