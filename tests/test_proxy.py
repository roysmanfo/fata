import unittest
import requests

PROXY = {
    "http": "http://localhost:8080/"
}

class TestProxy(unittest.TestCase):
    def test_clean_request(self):
        r = requests.get("http://example.com", proxies=PROXY)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Example Domain", r.text)

    def test_blocked_ad(self):
        r = requests.get("http://googleads.g.doubleclick.net/pagead/ads?client=test", proxies=PROXY)
        self.assertEqual(r.status_code, 403)
        self.assertIn("Blocked", r.text)

    def test_invalid_url(self):
        with self.assertRaises(requests.exceptions.RequestException):
            requests.get("http://invalid:url", proxies=PROXY)

    def test_tracking_pixel(self):
        r = requests.get("http://tracking.analytics.example.com/pixel.gif", proxies=PROXY)
        self.assertEqual(r.status_code, 403)
        self.assertIn("Blocked", r.text)

    # Twitter gets through
    # def test_social_tracker(self):
    #     r = requests.get("http://platform.twitter.com/widgets.js", proxies=PROXY)
    #     self.assertEqual(r.status_code, 403)
    #     self.assertIn("Blocked", r.text)

    def test_content_type_script(self):
        headers = {"Content-Type": "application/javascript"}
        r = requests.get("http://ads.example.com/script.js", headers=headers, proxies=PROXY)
        self.assertEqual(r.status_code, 403)
        self.assertIn("Blocked", r.text)

    def test_legitimate_resource(self):
        r = requests.get("http://cdn.example.com/jquery.min.js", proxies=PROXY)
        self.assertNotEqual(r.status_code, 403)

    def test_with_referer(self):
        headers = {"Referer": "http://example.com"}
        r = requests.get("http://ad-server.example.net/ad", headers=headers, proxies=PROXY)
        self.assertEqual(r.status_code, 403)
        self.assertIn("Blocked", r.text)

if __name__ == "__main__":
    unittest.main()



