from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from storages.backends.s3boto3 import S3StaticStorage, S3Boto3Storage
from . import __version__
import os


class LocalNetworkStorage(StaticFilesStorage):
    def url(self, name):
        url = super().url(name)
        static_url = os.getenv('STATIC_URL', '/static/')

        if not static_url.endswith('/'):
            static_url += '/'

        if url.startswith('/static/'):
            url = static_url + url[8:]

        return url


class Boto3Storage(S3Boto3Storage):
    def get_default_settings(self):
        return {
            **super().get_default_settings(),
            'querystring_auth': True,
            'default_acl': 'public-read'
        }


class ThumbnailStorage(S3Boto3Storage):
    def get_default_settings(self):
        return {
            **super().get_default_settings(),
            'querystring_auth': False,
            'default_acl': 'public-read'
        }


class StaticStorage(S3StaticStorage):
    def get_default_settings(self):
        return {
            **super().get_default_settings(),
            'bucket_name': settings.AWS_STORAGE_STATIC_BUCKET_NAME,
            'custom_domain': settings.AWS_S3_CUSTOM_STATIC_DOMAIN
        }

    def url(self, name):
        url = super().url(name)

        if '?' in url:
            url += '&'
        else:
            url += '?'

        url += 'v=%s' % __version__
        return url
