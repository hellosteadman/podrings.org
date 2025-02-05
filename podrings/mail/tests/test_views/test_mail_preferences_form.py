from django.test import TestCase
from flurry.mail.models import Tag, Preference


class PreferencesViewTests(TestCase):
    def setUp(self):
        "Creates 3 tags for testing."

        self.foo = Tag.objects.create(
            label='Foo',
            slug='foo'
        )

        self.bar = Tag.objects.create(
            label='Bar',
            slug='bar'
        )

        self.baz = Tag.objects.create(
            label='Baz',
            slug='baz'
        )

    def test_get(self):
        "Ensures the email preferences form is displayed."

        Preference.objects.create(
            email_hash='f4e19df2e6c609fbd59a42b9063d0fadf44260218531ea21ad8c575f205c0453',  # NOQA
            tag=self.bar
        )

        response = self.client.get(
            '/mail/prefs/f4e19df2e6c609fbd59a42b9063d0fadf44260218531ea21ad8c575f205c0453/'  # NOQA
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'mail/preferences_form.html',
            [t.name for t in response.templates]
        )

    def test_post(self):
        """
        Ensure the user can update email preferences and be
        redirected to the "updated" view.
        """

        response = self.client.post(
            '/mail/prefs/f4e19df2e6c609fbd59a42b9063d0fadf44260218531ea21ad8c575f205c0453/',  # NOQA
            {
                'tag_%d' % self.foo.pk: 'on',
                'tag_%d' % self.baz.pk: 'on'
            }
        )

        prefs = Preference.objects.filter(
            email_hash='f4e19df2e6c609fbd59a42b9063d0fadf44260218531ea21ad8c575f205c0453',  # NOQA
            subscribed=False
        ).values_list(
            'tag__slug',
            flat=True
        ).order_by(
            'tag__slug'
        )

        self.assertEqual(
            list(prefs),
            ['bar']
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            '/mail/prefs/updated/'
        )
