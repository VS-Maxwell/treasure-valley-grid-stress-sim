import unittest

from tools.esri_gateway import (
    ALLOWED_ORIGINS,
    PUBLIC_IMAGERY_URL,
    STYLE_URL,
    authorized_headers,
    cors_origin,
    normalize_geocode_query,
    normalize_limit,
)


class EsriGatewaySecurityTests(unittest.TestCase):
    def test_credential_is_only_in_authorization_header(self) -> None:
        credential = "example-sensitive-value"
        headers = authorized_headers(credential)
        self.assertEqual(headers["Authorization"], f"Bearer {credential}")
        self.assertNotIn(credential, STYLE_URL)
        self.assertNotIn(credential, PUBLIC_IMAGERY_URL)

    def test_only_explicit_loopback_origins_receive_cors(self) -> None:
        for origin in ALLOWED_ORIGINS:
            self.assertEqual(cors_origin(origin), origin)
        self.assertIsNone(cors_origin("https://example.com"))
        self.assertIsNone(cors_origin(None))

    def test_geocode_input_is_bounded_and_normalized(self) -> None:
        self.assertEqual(normalize_geocode_query("  Boise   Idaho  "), "Boise Idaho")
        with self.assertRaisesRegex(RuntimeError, "2 to 160"):
            normalize_geocode_query("x")
        with self.assertRaisesRegex(RuntimeError, "2 to 160"):
            normalize_geocode_query("x" * 161)

    def test_result_limit_is_bounded(self) -> None:
        self.assertEqual(normalize_limit(None), 3)
        self.assertEqual(normalize_limit("5"), 5)
        for value in ["0", "6", "many"]:
            with self.assertRaises(RuntimeError):
                normalize_limit(value)


if __name__ == "__main__":
    unittest.main()
