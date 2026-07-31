from __future__ import annotations

import unittest

from shared.canonical import (
    CanonicalizationError,
    DuplicateKeyError,
    NonNFCError,
    UnsafeNumberError,
    canonical_bytes,
    canonical_decimal_string,
    canonical_hash,
    decimal_string,
    scoped_address_fingerprint,
    strict_loads,
    strict_loads_bytes,
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

    def test_raw_bytes_must_match_the_canonical_profile(self) -> None:
        value = {"b": 1, "a": 2}
        raw = canonical_bytes(value)
        self.assertEqual(strict_loads_bytes(raw), {"a": 2, "b": 1})
        with self.assertRaises(CanonicalizationError):
            strict_loads_bytes(b'{"b":1,"a":2}')
        with self.assertRaises(CanonicalizationError):
            strict_loads_bytes(b"\xef\xbb\xbf" + raw)

    def test_object_keys_use_utf16_code_unit_order(self) -> None:
        value = {"\ue000": 1, "\U00010000": 2}
        self.assertEqual(
            canonical_bytes(value),
            '{"𐀀":2,"":1}'.encode("utf-8"),
        )

    def test_default_ignorable_and_bidi_controls_fail(self) -> None:
        for raw in ('{"name":"a\\u200db"}', '{"name":"a\\u202eb"}'):
            with self.subTest(raw=raw), self.assertRaises(CanonicalizationError):
                strict_loads(raw)

    def test_decimal_aliases_are_rejected_by_signer_profile(self) -> None:
        self.assertEqual(canonical_decimal_string("500", scale=6), 500)
        for value in ("500.0", "500.00"):
            with self.subTest(value=value), self.assertRaises(CanonicalizationError):
                canonical_decimal_string(value, scale=6)

    def test_address_fingerprint_is_scoped_by_network(self) -> None:
        address = "0x" + "1" * 40
        self.assertNotEqual(
            scoped_address_fingerprint("eip155:42161", address),
            scoped_address_fingerprint("eip155:421614", address),
        )

    def test_mixed_script_confusable_alias_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_alias("paypaл")
