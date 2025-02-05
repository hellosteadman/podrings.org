from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from feedparser import parse
from hashlib import md5
from markdown import markdown
from podrings.community.models import Ring
from podrings.creative.exceptions import MissingEmail
from podrings.creative.models import Podcast
from urllib.parse import urlparse
import os
import re
import requests
import time


USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15'  # NOQA
RSS_URL = 'https://podnews.net/sitemap/trailers.xml'
PODNEWS_PAGE_EX = r'Subscribe in all apps: <a[^>]*href="(https://podnews.net/podcast/[^"]+)"'  # NOQA
ITUNES_TAG_EX = r'^app-id=(\d+)'
UNACCEPTABLE_CATEGORIES = (
    'Alternative Health',
    'Christianity',
    'Courses',
    'Hinduism',
    'Investing',
    'Islam',
    'Judaism',
    'Religion',
    'Religion & Spirituality'
)

UNACCEPTABLE_DOMAINS = (
    'access.acast.com',
    'cbc.ca',
    'feeds.boston.com',
    'feeds.megaphone.fm',
    'feeds.npr.org',
    'feeds.sharp-stream.com',
    'feeds.wgbh.org',
    'omnycontent.com',
    'podcast.global.com',
    'rss.art19.com',
    'rss.pdrl.fm'
)


class Command(BaseCommand):
    help = 'Fetches new podcast trailers from Podnews'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def __get(self, url):
        cache_dir = os.path.join(
            settings.BASE_DIR,
            '.cache'
        )

        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

        cache_filename = os.path.join(
            cache_dir,
            '%s.xml' % md5(url.encode('utf-8')).hexdigest()
        )

        if not os.path.exists(cache_filename):
            response = requests.get(
                url,
                headers={
                    'User-Agent': USER_AGENT
                }
            )

            response.raise_for_status()

            with open(cache_filename, 'wb') as f:
                f.write(response.content)

        with open(cache_filename, 'rb') as f:
            return f.read()

    def _get_apple_id(self, page_url):
        stream = self.__get(page_url)
        soup = BeautifulSoup(stream, 'html.parser')

        if head := soup.find('head'):
            for meta in head.find_all('meta'):
                if meta.get('name') == 'apple-itunes-app':
                    if content := meta.get('content'):
                        if match := re.search(ITUNES_TAG_EX, content):
                            return int(match.groups()[0])

                    raise Exception('iTunes meta tag has no valid ID.')

            return

        raise Exception('No head tag found.')

    def _podcast_is_eligible(self, apple_id):
        if result := Podcast.objects.get_itunes_result(apple_id):
            for category in result.get('genres', []):
                if category in UNACCEPTABLE_CATEGORIES:
                    return False

            url = result['feedUrl']
            domain = urlparse(url).hostname

            while domain.startswith('www.'):
                domain = domain[4:]

            if domain in UNACCEPTABLE_DOMAINS:
                return False

            return True

    def _ingest_podcast(self, url):
        feed = parse(self.__get(url))
        raise Exception(feed.feed.keys())

    def handle(self, *args, **options):
        feed = parse(self.__get(RSS_URL))

        with transaction.atomic():
            mark = User.objects.get(is_superuser=True)
            ring = Ring.objects.filter(
                name='New & Noteworthy'
            ).first()

            if ring is None:
                ring = Ring.objects.create(
                    name='New & Noteworthy',
                    slug=hex(int(time.time() * 10000000))[2:],
                    description='Newly added or updated podcasts.',
                    approved_on=timezone.now(),
                    approved_by=mark
                )

                for admin in User.objects.filter(is_staff=True):
                    ring.admins.create(
                        user=admin,
                        can_edit=True,
                        can_approve=True,
                        can_remove=True,
                        can_delete=admin.is_superuser,
                        can_transfer=admin.is_superuser
                    )

            # for m in ring.memberships.select_related():
            #     m.podcast.delete()
            #     m.delete()

        for entry in feed.entries:
            content_encoded = markdown(entry.description)

            for content in entry.get('content', []):
                if content.get('type') == 'text/html':
                    content_encoded = content['value']

            if page_url := re.search(PODNEWS_PAGE_EX, content_encoded):
                page_url = page_url.groups()[0]

                if not (apple_id := self._get_apple_id(page_url)):
                    continue

                if not self._podcast_is_eligible(apple_id):
                    continue

                try:
                    podcast = Podcast.objects.fetch_from_apple_id(
                        apple_id,
                        create_user_from_owner=True
                    )
                except MissingEmail:
                    pass
                else:
                    # print(podcast.name)
                    podcast.memberships.get_or_create(
                        ring=ring,
                        defaults={
                            'approved_on': timezone.now(),
                            'approved_by': mark
                        }
                    )
