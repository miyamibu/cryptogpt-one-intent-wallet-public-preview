from __future__ import annotations

import unittest

from shared.canonical import (
    DuplicateKeyError,
    NonNFCError,
    UnsafeNumberError,
    canonical_hash,
    decimal_string,
    strict_loads,
    validate_alias,
)


class CanonicalTests(unittest.TestCase):
    def test_duplicate_keys_fail(self) -> None:
        with self.assertRaises(DuplicateKeyError):
            strict_loads('{"a":1,"a":2}')

    def test_non_nfc_fails_without_silent_normalization(self) -> None:
        with self.assertRaises(NonNFCError):
            strict_loads('{"name":"e\\u0301"}')

    def test_float_and_exponent_fail(self) -> None:
        with self.assertRaises(UnsafeNumberError):
            strict_loads('{"amount":1e2}')
        with self.assertRaises(UnsafeNumberError):
            strict_loads('{"amount":9007199254740992}')

    def test_negative_zero_and_decimal_scale_fail(self) -> None:
        with self.assertRaises(UnsafeNumberError):
            strict_loads('{"amount":-0}')
        with self.assertRaises(ValueError):
            decimal_string("1.001", scale=2)

    def test_hash_is_domain_separated(self) -> None:
        self.assertNotEqual(canonical_hash("a", {"x": 1}), canonical_hash("b", {"x": 1}))

    def test_mixed_script_confusable_alias_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_alias("paypaл")
