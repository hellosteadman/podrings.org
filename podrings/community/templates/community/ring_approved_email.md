{% load i18n %}{% blocktrans with name=user.first_name|default:user.username %}Hi {{ name }}.{% endblocktrans %}

{% blocktrans with ring=object.name %}Your podring, **{{ ring }}** is now live on the Podrings website!{% endblocktrans %}

## {% trans 'What to do next' %}

1. {% trans 'Check the details on your podring page (click the button below).' %}
2. {% trans 'Add your own shows to the podring.' %}
3. {% trans 'Invite podcasters to join.' %}

{% blocktrans with email='hello@podrings.org' %}If you have any questions about what to do next, email <{{ email }}>.{% endblocktrans %}
