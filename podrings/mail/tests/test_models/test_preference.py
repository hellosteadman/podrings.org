from django.test import TestCase
from flurry.mail.models import Preference


class PreferenceTests(TestCase):
    def test_str(self):
        "Checks the string representation of Preference objects."
        obj = Preference(email_hash='foo')
        self.assertEqual(str(obj), 'foo')
