{% load i18n %}{% blocktrans with name=user.first_name|default:user.username %}Hiya {{ name }} 👋{% endblocktrans %}

{% trans 'A new podring has been created, and needs your approval.' %}

### {% trans 'Name' %}

{{ object.name }}

### {% trans 'Creator' %}

{{ creator.get_full_name }} (<{{ creator.email }}>){% if object.description %}

### {% trans 'Description' %}

{% for line in object.description.splitlines %}> {{ line }}

{% endfor %}{% endif %}
