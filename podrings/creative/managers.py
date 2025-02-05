from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from feedparser import parse
from podrings import USER_AGENT
from .exceptions import FetchError, MissingEmail
from .tasks import convert_episode_to_promo
import logging
import requests


class PodcastManager(models.Manager):
    def get_itunes_result(self, apple_id):
        cachekey = 'feeds:%d' % int(apple_id)

        if (response := cache.get(cachekey)) is None:
            try:
                response = requests.get(
                    'https://itunes.apple.com/lookup',
                    params={
                        'id': apple_id
                    },
                    headers={
                        'User-Agent': USER_AGENT
                    }
                )

                response.raise_for_status()
            except Exception:
                raise FetchError(
                    _(
                        'The Apple Podcasts directory is currently '
                        'unavailable. Try again in a few moments.'
                    )
                )

            response = response.json()
            cache.set(cachekey, response)

        for result in response.get('results', []):
            if result['kind'] != 'podcast':
                continue

            return result

    def parse_feed(self, url):
        try:
            apple_id = int(url)
        except ValueError():
            pass
        else:
            if result := self.get_itunes_result(apple_id):
                url = result['feedUrl']
            else:
                raise FetchError(
                    _('No podcast could be found matching the given ID.')
                )

        logger = logging.getLogger('podrings.creative')

        try:
            response = requests.get(
                url,
                stream=True,
                headers={
                    'User-Agent': USER_AGENT
                }
            )
        except Exception:
            logger.error(
                'Error getting feed',
                exc_info=True,
                extra={
                    'url': url
                }
            )

            raise FetchError(
                _('The podcast feed could not be reached.')
            )

        feed = parse(response.content)

        if feed.feed.get('author_detail', {}).get('email'):
            return feed

        raise FetchError(
            _('This podcast feed does not list an email address.')
        )

    @transaction.atomic
    def fetch_from_rss(self, url, **kwargs):
        logger = logging.getLogger('podrings.creative')

        try:
            while True:
                response = requests.head(
                    url,
                    allow_redirects=False,
                    headers={
                        'User-Agent': USER_AGENT
                    }
                )

                if response.status_code in (301, 302):
                    url = response.headers['Location']
                else:
                    response.raise_for_status()
                    break

            response = requests.get(
                url,
                stream=True,
                headers={
                    'User-Agent': USER_AGENT
                }
            )
        except Exception:
            logger.error(
                'Error getting feed',
                exc_info=True,
                extra={
                    'url': url
                }
            )

            raise FetchError(
                _('The podcast feed could not be reached.')
            )

        for obj in self.filter(rss=url):
            obj.fetch()
            return obj

        feed = parse(response.content)
        author = feed.feed.get('author_detail', {})
        autodiscover_promo = kwargs.pop('autodiscover_promo', True)

        if author.get('email'):
            if kwargs.pop('create_user_from_owner', False):
                email = author['email'].lower()

                q = models.Q(
                    email__iexact=email
                ) | models.Q(
                    username__iexact=email
                )

                user = User.objects.filter(q).first()

                if user is None:
                    if name := author.get('name'):
                        if ' ' in name:
                            first_name, last_name = name.rsplit(' ', 1)
                        else:
                            first_name = name
                            last_name = ''
                    else:
                        name, domain = email.split('@', 1)
                        if '.' in name:
                            first_name, last_name = name.rsplit('.', 1)
                        else:
                            first_name = name
                            last_name = ''

                    user = User.objects.create(
                        email=email,
                        username=email,
                        first_name=first_name.strip().title(),
                        last_name=last_name.strip().title(),
                        password='!'
                    )

                kwargs['created_by'] = user

            obj = self.model(rss=url, **kwargs)
            obj._feed_cache = feed
            obj.fetch()

            if autodiscover_promo:
                for episode in obj.episodes.filter(
                    type='trailer',
                    duration__lte=100
                ):
                    transaction.on_commit(
                        lambda: convert_episode_to_promo.delay(episode.pk)
                    )

            return obj

        raise MissingEmail(
            _('This podcast feed does not list an email address.')
        )

    @transaction.atomic
    def fetch_from_apple_id(self, apple_id, **kwargs):
        if result := self.get_itunes_result(apple_id):
            for obj in self.filter(apple_id=result['trackId']):
                obj.fetch()
                return obj

            return self.fetch_from_rss(
                result['feedUrl'],
                apple_id=result['trackId'],
                **kwargs
            )

        raise FetchError(
            _('No podcast could be found matching the given ID.')
        )
