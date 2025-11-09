import unittest

import contact_app as myapp


class ContactPageTest(unittest.TestCase):
    def setUp(self):
        self.app = myapp.app.test_client()
        self.app.testing = True

    def test_get_contact(self):
        resp = self.app.get('/contact')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_data(as_text=True)
        # Check basic form presence
        self.assertIn('<form', data)
        self.assertIn('name="message"', data)


if __name__ == '__main__':
    unittest.main()
