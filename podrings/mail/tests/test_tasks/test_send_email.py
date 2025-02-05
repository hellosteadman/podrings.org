from django.test import TestCase
from django.core import mail
from flurry.mail.tasks import send_email
from flurry.mail.models import Tag, Preference


class SendEmailTests(TestCase):
    def test_subscribed(self):
        """
        Ensures an email is sent to the specified address.
        """

        send_email(
            'Subject',
            'jo@example.com',
            'Hello Jo.',
            preheader='We hope this email finds you well.',
            tags=('new',),
            image_url='header.jpg',
            primary_url='https://jointheflurry.com/',
            primary_cta='Join the Flurry'
        )

        message = mail.outbox.pop()
        self.assertEqual(message.subject, 'Subject')
        self.assertEqual(message.recipients()[0], 'jo@example.com')
        self.assertFalse(any(mail.outbox))

    def test_unsubscribed(self):
        """
        Ensures an email is not sent to the specified address
        that has elected not to receive certain messages.
        """

        tag = Tag.objects.create(slug='new')
        Preference.objects.create(
            email_hash='f4e19df2e6c609fbd59a42b9063d0fadf44260218531ea21ad8c575f205c0453',  # NOQA
            tag=tag,
            subscribed=False
        )

        send_email(
            'Subject',
            'jo@example.com',
            'Hello Jo.',
            preheader='We hope this email finds you well.',
            tags=('new',),
            image_url='header.jpg',
            primary_url='https://jointheflurry.com/',
            primary_cta='Join the Flurry'
        )

        self.assertFalse(any(mail.outbox))
