from django.test import TestCase
from flurry.mail.models import Tag


class TagTests(TestCase):
    def test_str(self):
        "Checks the string representation of Tag objects."
        obj = Tag(label='Foo')
        self.assertEqual(str(obj), 'Foo')
