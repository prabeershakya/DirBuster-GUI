import unittest
from unittest.mock import Mock

class DirBuster:
    def is_likely_directory(self, response, url):
        if url.endswith('/'):
            return True
        if response.status_code == 200 and response.text:
            text_lower = response.text.lower()
            if 'index of /' in text_lower or 'directory listing for' in text_lower:
                return True
        if response.status_code in [301, 302]:
            location = response.headers.get('Location', '')
            if location and location.endswith('/'):
                return True
        if response.status_code == 403 and '.' not in url.split('/')[-1]:
            return True
        return False

class TestDirBuster(unittest.TestCase):
    def setUp(self):
        self.buster = DirBuster()
    
    def test_url_ends_with_slash(self):
        resp = Mock(status_code=200, text="", headers={})
        self.assertTrue(self.buster.is_likely_directory(resp, "http://test.com/admin/"))
    
    def test_file_with_extension(self):
        resp = Mock(status_code=200, text="", headers={})
        self.assertFalse(self.buster.is_likely_directory(resp, "http://test.com/image.jpg"))
    
    def test_index_of_in_response(self):
        resp = Mock(status_code=200, text="<h1>Index of /admin</h1>", headers={})
        self.assertTrue(self.buster.is_likely_directory(resp, "http://test.com/admin"))
    
    def test_redirect_to_slash(self):
        resp = Mock(status_code=301, text="", headers={'Location': 'http://test.com/admin/'})
        self.assertTrue(self.buster.is_likely_directory(resp, "http://test.com/admin"))
    
    def test_403_no_extension(self):
        resp = Mock(status_code=403, text="", headers={})
        self.assertTrue(self.buster.is_likely_directory(resp, "http://test.com/private"))
    
    def test_403_with_extension(self):
        resp = Mock(status_code=403, text="", headers={})
        self.assertFalse(self.buster.is_likely_directory(resp, "http://test.com/script.php"))
    
    def test_other_status_codes(self):
        resp = Mock(status_code=404, text="", headers={})
        self.assertFalse(self.buster.is_likely_directory(resp, "http://test.com/missing"))

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDirBuster)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nTests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)