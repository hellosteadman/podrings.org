from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_rq.decorators import job
from email.utils import formataddr
from markdown import markdown
from hashlib import sha256


@job('default')
def send_email(
    subject, recipient, body, preheader=None, tags=(),
    image_url=None, primary_url=None, primary_cta=None
):
    from .models import Preference

    ctx = {
        'preheader': None,
        'primary_cta': primary_cta,
        'footer_links': [],
        'primary_url': primary_url
    }

    if any(tags):
        email_hash = sha256(
            recipient.lower().encode('utf-8')
        ).hexdigest()

        if Preference.objects.filter(
            email_hash=email_hash,
            tag__slug__in=tags,
            subscribed=False
        ).exists():
            return

        ctx['preferences_url'] = 'http%s://%s%s' % (
            not settings.DEBUG and 's' or '',
            settings.DOMAIN,
            reverse(
                'mail_preferences',
                args=(email_hash,)
            )
        )

    md_body = render_to_string(
        'mail/layout.md',
        {
            'body': body,
            **ctx
        }
    )

    html_body = render_to_string(
        'mail/message.html',
        {
            'body': mark_safe(markdown(body)),
            'image_url': image_url,
            **ctx
        }
    )

    message = EmailMultiAlternatives(
        subject,
        md_body,
        formataddr(
            (
                settings.DEFAULT_FROM_NAME,
                settings.DEFAULT_FROM_EMAIL
            )
        ),
        [recipient]
    )

    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)
