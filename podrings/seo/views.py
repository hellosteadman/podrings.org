from datetime import datetime, date
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files import File
from django.db.models.fields.files import ImageFieldFile
from django.urls import reverse
from django.utils.safestring import mark_safe
from easy_thumbnails.files import ThumbnailerImageFieldFile
import json
import logging
import os


class SEOMixin:
    seo_title = ''
    seo_description = ''
    robots = ''

    def get_seo_title(self):
        if getattr(self, 'object', None):
            return str(self.object)

        return self.seo_title

    def get_seo_description(self):
        if getattr(self, 'object', None):
            if hasattr(self.object, 'excerpt'):
                return self.object.excerpt

            if hasattr(self.object, 'description'):
                return self.object.description

        return self.seo_description

    def get_canonical_url(self):
        if hasattr(self, 'canonical_url'):
            return self.request.build_absolute_uri(
                reverse(self.canonical_url)
            )

        if getattr(self, 'object', None):
            if hasattr(self.object, 'get_absolute_url'):
                return self.request.build_absolute_uri(
                    self.object.get_absolute_url()
                )

        if getattr(self, 'paginate_by', 0):
            if page := self.request.GET.get('page'):
                try:
                    page = int(page)

                    if page > 1:
                        return self.request.build_absolute_uri(
                            '%s?page=%d' % (
                                self.request.path,
                                page
                            )
                        )
                except Exception:
                    print('Invalid page')

        return self.request.build_absolute_uri(self.request.path)

    def get_robots(self):
        return self.robots

    def get_context_data(self, **kwargs):
        return {
            'seo_title': self.get_seo_title(),
            'seo_description': self.get_seo_description(),
            'robots_content': self.get_robots(),
            'canonical_url': self.get_canonical_url(),
            **super().get_context_data(**kwargs)
        }


class OpenGraphMixin:
    og_locale = 'en-GB'
    og_type = 'article'
    og_title = ''
    og_description = ''
    og_site_name = og_title

    twitter_card = 'summary_large_image'
    twitter_title = ''
    twitter_description = ''
    twitter_site = ''
    twitter_creator = ''

    def get_og_locale(self):
        return self.og_locale

    def get_og_type(self):
        return self.og_type

    def get_og_title(self):
        if getattr(self, 'object', None):
            return str(self.object)

        return self.og_title

    def get_og_description(self):
        if getattr(self, 'object', None):
            if hasattr(self.object, 'excerpt'):
                return self.object.excerpt

            if hasattr(self.object, 'description'):
                return self.object.description

        return self.og_description

    def get_og_image(self):
        if getattr(self, 'og_image', None):
            return staticfiles_storage.url(self.og_image)

        if getattr(self, 'object', None):
            image = getattr(self.object, 'thumbnail', None)
            if image and isinstance(image, ThumbnailerImageFieldFile):
                try:
                    return image.get_thumbnail(
                        {
                            'size': (1200, 630),
                            'crop': True,
                            'upscale': True
                        }
                    ).url
                except Exception:
                    logging.warning(
                        'Error generating Open Graph thumbnail',
                        exc_info=True
                    )

            if image and isinstance(image, ImageFieldFile) and image:
                return image.url

    def get_og_url(self):
        return self.request.build_absolute_uri(self.request.path)

    def get_og_site_name(self):
        return self.og_site_name

    def get_og_tags(self):
        tags = [
            {
                'property': 'locale',
                'content': self.get_og_locale()
            },
            {
                'property': 'type',
                'content': self.get_og_type()
            },
            {
                'property': 'title',
                'content': self.get_og_title()
            },
            {
                'property': 'description',
                'content': self.get_og_description()
            },
            {
                'property': 'url',
                'content': self.get_og_url()
            },
            {
                'property': 'logo',
                'content': staticfiles_storage.url('img/logo.png')
            }
        ]

        image = self.get_og_image()
        if image and isinstance(image, File):
            tags.extend(
                [
                    {
                        'property': 'image',
                        'content': image.url
                    }
                ]
            )
        elif image and isinstance(image, str):
            tags.append(
                {
                    'property': 'image',
                    'content': image
                }
            )

        return tags

    def get_twitter_card(self):
        return self.twitter_card

    def get_twitter_title(self):
        return self.twitter_title or self.get_og_title()

    def get_twitter_description(self):
        return self.twitter_description or self.get_og_description()

    def get_twitter_site(self):
        return self.twitter_site

    def get_twitter_creator(self):
        return self.twitter_creator

    def get_twitter_tags(self):
        tags = [
            {
                'name': 'card',
                'content': self.get_twitter_card()
            },
            {
                'name': 'title',
                'content': self.get_twitter_title()
            },
            {
                'name': 'description',
                'content': self.get_twitter_description()
            },
            {
                'name': 'site',
                'content': self.get_twitter_site()
            },
            {
                'name': 'creator',
                'content': self.get_twitter_creator()
            }
        ]

        image = self.get_og_image()
        if image and isinstance(image, File):
            tags.append(
                {
                    'name': 'image',
                    'content': image.url
                }
            )
        elif image and isinstance(image, str):
            tags.append(
                {
                    'name': 'image',
                    'content': image
                }
            )

        return tags

    def get_context_data(self, **kwargs):
        return {
            'og_tags': self.get_og_tags(),
            'twitter_tags': self.get_twitter_tags(),
            **super().get_context_data(**kwargs)
        }


class OpenGraphArticleMixin(OpenGraphMixin):
    og_type = 'article'
    article_author = ''
    article_section = ''
    article_published_time = ''

    def get_article_author(self):
        return self.article_author

    def get_article_section(self):
        return self.article_section

    def get_article_published_time(self):
        return self.article_published_time

    def get_article_tags(self):
        return [
            {
                'property': 'author',
                'content': self.get_article_author()
            },
            {
                'property': 'section',
                'content': self.get_article_section()
            },
            {
                'property': 'published_time',
                'content': self.get_article_published_time()
            }
        ]

    def get_context_data(self, **kwargs):
        return {
            'article_tags': self.get_article_tags(),
            **super().get_context_data(**kwargs)
        }


class LinkedDataEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        return super().default(value)


class LinkedDataMixin:
    ld_type = 'Thing'
    ld_breadcrumbs = [
        ('/', 'Home'),
        ('.', '__str__')
    ]

    def get_ld_type(self):
        return self.ld_type

    def _load_ld_fixture(self, name):
        app, fixture = name.split('.')
        filename = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            app,
            'fixtures',
            'ld',
            '%s.json' % fixture
        )

        return self._prepare_fixture(filename)

    def _prepare_fixture(self, filename):
        with open(filename, 'rb') as f:
            data = json.load(f)

        for key, value in data.items():
            if isinstance(value, dict):
                import_name = value.pop('@import', None)
                if import_name:
                    import_fixture = self._load_ld_fixture(import_name)
                    data[key] = {
                        **import_fixture,
                        **value
                    }

        return data

    def get_ld_attributes(self):
        if hasattr(self, 'ld_attributes'):
            return self.ld_attributes

        if hasattr(self, 'ld_fixture'):
            return self._load_ld_fixture(self.ld_fixture)

        return {}

    def get_ld_breadcrumb_trail(self):
        return self.ld_breadcrumbs

    def get_ld_breadcrumb(self):
        leaves = self.get_ld_breadcrumb_trail()

        def get_str():
            if hasattr(self, 'object'):
                return str(self.object)

            return self.request.path.replace(
                '/', ''
            ).replace(
                '-', ' '
            ).capitalize()

        if any(leaves):
            return {
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    {
                        '@type': 'ListItem',
                        'position': index + 1,
                        'item': self.request.build_absolute_uri(
                            callable(leaf[0]) and leaf[0]() or leaf[0]
                        ),
                        'name': leaf[1] == '__str__' and get_str() or leaf[1]
                    } for (index, leaf) in enumerate(leaves)
                ]
            }

    def get_ld_url(self):
        if hasattr(self, 'ld_url'):
            return self.request.build_absolute_uri(
                reverse(self.ld_url)
            )

    def get_linked_data(self):
        data = {
            '@context': 'https://schema.org',
            '@type': self.get_ld_type(),
            **self.get_ld_attributes()
        }

        url = self.get_ld_url()
        if 'url' not in data and url:
            data['url'] = url

        breadcrumb = self.get_ld_breadcrumb()
        if 'breadcrumb' not in data and breadcrumb:
            data['breadcrumb'] = breadcrumb

        return data

    def get_context_data(self, **kwargs):
        local = {}

        def get_json_ld():
            if 'ld' not in local:
                local['ld'] = mark_safe(
                    json.dumps(
                        kwargs.get('json_ld', self.get_linked_data()),
                        indent=4,
                        cls=LinkedDataEncoder
                    )
                )

            return local['ld']

        return {
            'json_ld': get_json_ld,
            **super().get_context_data(**kwargs)
        }
