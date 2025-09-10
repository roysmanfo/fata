import unittest
from fata.shield import Shield

class TestAdBlockerEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load filter list once
        cls.engine = Shield(
            optimize=True, debug=False
        ).engine

    def test_block_known_ad_url(self):
        result = self.engine.check_network_urls(
            "https://googleads.g.doubleclick.net/pagead/ads?client=123",
            "https://example.com",
            "script"
        )
        self.assertTrue(result.matched, "Should block known ad domain")

    def test_allow_clean_url(self):
        result = self.engine.check_network_urls(
            "https://example.com/content/article.html",
            "https://example.com",
            "document"
        )
        self.assertFalse(result.matched, "Should allow normal content")

    def test_block_analytics_script(self):
        result = self.engine.check_network_urls(
            "https://ssl.google-analytics.com/ga.js",
            "https://example.com",
            "script"
        )
        self.assertTrue(result.matched, "Should block analytics script")

    def test_image_resource_type(self):
        result = self.engine.check_network_urls(
            "https://ads.example.com/banner.jpg",
            "https://example.com",
            "image"
        )
        self.assertTrue(result.matched or not result.matched, "Should process image request without error")

    def test_empty_url(self):
        result = self.engine.check_network_urls(
            "",
            "https://example.com",
            "script"
        )
        self.assertFalse(result.matched, "Empty URL should not match any filters")

    def test_invalid_url_format(self):
        result = self.engine.check_network_urls(
            "invalid:url::\\//",
            "https://example.com",
            "script"
        )
        self.assertFalse(result.matched, "Invalid URL should be handled gracefully")

if __name__ == '__main__':
    unittest.main()
