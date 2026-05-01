import secrets

from shared.exception_util import ValueMustBePositiveAndEvenError, ValueMustBePositiveError

# forbidden characters: i, l, n, o, r, s, u, v, z AND 0, 1, 2 -> to avoid confusion with 0o, I1l, uv, AR...
# and ensure strings are easily distinguishable and less prone to errors when read or transcribed.
_ALPHABET_PATTERN = "abcdefghjkmpqtwxy3456789"


def generate_rng_string_list(size_list: int, nbr_char: int) -> list[str]:
    """Generates a list of unique random strings.

    Args:
        size_list: Number of unique strings to generate.
        nbr_char: Number of characters in each random string (must be even).

    Returns:
        List of unique random strings.

    Raises:
        ValueError: If nbr_char is not a positive even integer or if size_list is not a positive integer.
    """
    if size_list <= 0:
        raise ValueMustBePositiveError()
    if nbr_char <= 0 or (nbr_char % 2) != 0:
        raise ValueMustBePositiveAndEvenError()

    codes = set()
    while len(codes) < size_list:
        codes.add(secrets.token_hex(nbr_char // 2))
    return list(codes)


def generate_rng_string_x4() -> str:
    """Generates a unique random string of 4 characters.

    Returns:
        A unique random string of 4 characters.

    Raises:
        ValueError: If the generation fails.
    """
    return generate_rng_string_list(size_list=1, nbr_char=4)[0]


def generate_rng_string_x10() -> str:
    """Generates a unique random string of 10 characters.

    Returns:
        A unique random string of 10 characters.

    Raises:
        ValueError: If the generation fails.
    """
    return generate_rng_string_list(size_list=1, nbr_char=10)[0]
