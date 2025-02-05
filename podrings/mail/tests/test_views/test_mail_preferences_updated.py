from django.test import TestCase


class PreferencesUpdatedViewTests(TestCase):
    def test_get(self):
        "Ensures the 'email preferences' view renders."

        response = self.client.get('/mail/prefs/updated/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'mail/preferences_updated.html',
            [t.name for t in response.templates]
        )
