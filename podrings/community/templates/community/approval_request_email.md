{% load i18n %}{% blocktrans with name=user.first_name|default:user.username %}Hiya {{ name }} 👋{% endblocktrans %}

{% blocktrans with name=object.created_by.get_full_name|default:'Someone' podcast=object.podcast.name ring=object.ring.name %}{{ name }} would like you to add **{{ podcast }}** to your **{{ ring }}** podring.{% endblocktrans %}

{% trans 'Here’s the description of the show:' %}

{% for line in object.podcast.description.splitlines %}> {{ line }}

{% endfor %}

{% blocktrans with name=object.created_by.first_name|default:'the owner' %}If you don’t want to add this podcast to the podring, you can disregard the email. Otherwise, click the button below to review the podcast further.{% endblocktrans %}
