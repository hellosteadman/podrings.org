{% block body %}{{ body }}{% endblock %}{% if primary_url %}

[**{{ primary_cta }}**]({{ primary_url }})
{% endif %}{% for link in footer_links %}
* [{{ link.title }}]({{ link.url }})
{% endfor %}{% if preferences_url %}
* [Manage email notifications]({{ preferences_url }}){% endif %}
