{% load i18n %}{% blocktrans with name=podcast.created_by.first_name %}Hiya {{ name }} 👋{% endblocktrans %}

{% blocktrans with podcast=podcast.name ring=ring.name %}Your podcast, **{{ podcast }}**, has been accepted into the **{{ ring }}** podring.{% endblocktrans %}

## {% trans 'What to do next' %}

1. {% trans 'Visit your podcast page via the button below.' %}
2. {% trans 'If you haven’t yet, upload a promo for your podcast.' %}
