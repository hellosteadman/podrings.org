from django.test import TestCase
from flurry.mail import send
from unittest.mock import patch


class SendTests(TestCase):
    def test(self):
        with patch('rq.queue.Queue.enqueue_job') as q:
            send(
                'Subject',
                [],
                'Body'
            )

        q.assert_called()
