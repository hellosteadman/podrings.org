{% load i18n %}

{% blocktrans with name=object.first_name %}Hiya {{ name }} 👋{% endblocktrans %}

{% trans 'You’re receiving this email because you signed up to Podrings. ' %}
{% trans 'You can confirm your email address by clicking the button below.' %}

{% trans 'If you didn’t sign up for an account, you can disregard this email.' %}
