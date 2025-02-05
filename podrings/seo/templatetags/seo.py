from django.template import Library
from ..helpers import title_case


register = Library()


@register.filter()
def titlecase(text):
    return title_case(text)
