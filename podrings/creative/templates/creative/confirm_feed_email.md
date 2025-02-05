{% load i18n %}## {% trans 'Verify your podcast' %}

{% blocktrans with feed=feed.title %}Click the button below to complete your podcast verification and add **{{ feed }}** to your account.{% endblocktrans %}

{% blocktrans with email='mailto:hello@podrings.org' %}If you didn’t make this request, you can ignore it or [contact us]({{ email }}) for help.{% endblocktrans %}
