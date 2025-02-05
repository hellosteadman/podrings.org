from django.template import Library
from hashlib import md5
from urllib.parse import urlencode


register = Library()


@register.filter()
def gravatar(email, width=50):
    return 'https://gravatar.com/avatar/%s?%s' % (
        md5(email.encode('utf-8')).hexdigest(),
        urlencode(
            {
                's': width,
                'd': 'mp'
            }
        )
    )


@register.filter()
def obfuscate_email(value):
    if not value:
        return ''

    username, domain = value.split('@')

    if len(username) > 2:
        obscured_username = ''.join(
            (
                username[0],
                '*' * (min((len(username) - 2), 5)),
                username[-1]
            )
        )
    else:
        obscured_username = '*'

    name, tld = domain.split('.', 1)
    if len(name) > 2:
        obsucred_name = ''.join(
            (
                name[0],
                '*' * (min((len(name) - 2), 5)),
                name[-1]
            )
        )

        obsucred_domain = '%s.%s' % (obsucred_name, tld)
    elif obscured_username == '*':
        obsucred_domain = domain
    else:
        obsucred_domain = '%s.%s' % ('*' * len(name), tld)

    return '%s@%s' % (obscured_username, obsucred_domain)
