from .tasks import send_email


def send(
    subject, recipient, body, preheader=None, tags=(),
    image_url=None, primary_url=None, primary_cta=None
):
    """
    Queues the `send_email` task, passing in the various
    arguments, and making sure they're safe to be sent
    over Redis.
    """

    send_email.delay(
        subject=str(subject),
        recipient=str(recipient),
        body=str(body),
        tags=tags,
        preheader=preheader,
        image_url=image_url and str(image_url),
        primary_url=primary_url and str(primary_url),
        primary_cta=primary_cta and str(primary_cta)
    )
