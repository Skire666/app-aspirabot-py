"""Tests for shared/random_util.py."""

from __future__ import annotations

import pytest

from shared.exception_util import ValueMustBePositiveAndEvenError
from shared.random_util import generate_rng_hexastring, generate_rng_id_step


class TestGenerateRngHexastring:
    def test_returns_string(self) -> None:
        result = generate_rng_hexastring(4)
        assert isinstance(result, str)

    def test_length_matches_nbr_char(self) -> None:
        for nbr_char in (2, 4, 8, 16, 32):
            result = generate_rng_hexastring(nbr_char)
            assert len(result) == nbr_char, f"Expected len {nbr_char}, got {len(result)}"

    def test_result_is_hexadecimal(self) -> None:
        result = generate_rng_hexastring(16)
        int(result, 16)  # raises if not valid hex

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(0)

    def test_odd_number_raises(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(3)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueMustBePositiveAndEvenError):
            generate_rng_hexastring(-2)

    def test_two_calls_differ(self) -> None:
        # With 8 hex chars, collision probability is 1/2^32 — negligible.
        a = generate_rng_hexastring(8)
        b = generate_rng_hexastring(8)
        assert a != b


class TestGenerateRngIdStep:
    def test_returns_string(self) -> None:
        result = generate_rng_id_step()
        assert isinstance(result, str)

    def test_length_is_four_or_six(self) -> None:
        # Normal path returns 4-char IDs; fallback returns 6-char.
        result = generate_rng_id_step()
        assert len(result) in {4, 6}

    def test_uses_allowed_alphabet(self) -> None:
        alphabet = set("aAbBcCdDeEFgGHkNpPqtTxyZY23456789")
        result = generate_rng_id_step()
        for char in result:
            assert char in alphabet, f"Unexpected char {char!r} in {result!r}"

    def test_registered_in_global_set(self) -> None:
        import shared.random_util as ru

        before = len(ru.g_unique_list_id_step)
        generate_rng_id_step()
        after = len(ru.g_unique_list_id_step)
        assert after > before
