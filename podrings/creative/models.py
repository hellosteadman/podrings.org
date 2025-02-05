from dateutil.parser import parse as parse_date
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone, html
from django.utils.translation import gettext_lazy as _
from feedparser import parse as parse_feed
from podrings import USER_AGENT
from podrings.utils import parse_duration
from uuid import uuid4
from .exceptions import FetchError
from .managers import PodcastManager
from .tasks import download_artwork, set_op3_id
import os
import requests
import time


class Podcast(models.Model):
    objects = PodcastManager()

    def upload_artwork(self, filename):
        return 'creative/podcasts/%d%s' % (
            int(self.apple_id),
            os.path.splitext(filename)[-1]
        )

    apple_id = models.PositiveIntegerField('Apple Podcasts ID', unique=True)
    op3_id = models.UUIDField('OP3 ID', editable=False, null=True, blank=True)
    name = models.CharField(max_length=1024)
    rss = models.URLField('RSS', max_length=1024)
    website = models.URLField(max_length=255)
    artwork = models.ImageField(
        upload_to=upload_artwork,
        max_length=255
    )

    description = models.TextField(null=True, blank=True)
    downloads_per_month = models.PositiveIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User',
        related_name='podcasts',
        on_delete=models.CASCADE
    )

    fetched_on = models.DateTimeField(null=True, blank=True, editable=False)
    owner_email = models.EmailField(max_length=255)
    invited_on = models.DateTimeField(null=True, blank=True)
    claimed_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('podcast_detail', args=(self.apple_id,))

    @transaction.atomic
    def fetch(self):
        if not (feed := getattr(self, '_feed_cache', None)):
            try:
                while True:
                    response = requests.head(
                        self.rss,
                        allow_redirects=False,
                        headers={
                            'User-Agent': USER_AGENT
                        }
                    )

                    if response.status_code in (301, 302):
                        self.rss = response.headers['Location']
                    else:
                        response.raise_for_status()
                        break

                response = requests.get(
                    self.rss,
                    stream=True,
                    headers={
                        'User-Agent': USER_AGENT
                    }
                )

                feed = parse_feed(response.content)
            except Exception:
                raise FetchError(
                    _('The podcast feed could not be reached.')
                )

        author = feed.feed.get('author_detail', {})

        self.name = feed.feed.title
        if email := author.get('email'):
            self.owner_email = email

        self.website = feed.feed.get('link', '')
        self.description = html.strip_tags(
            feed.feed.get('summary', '')
        )

        self.fetched_on = timezone.now()
        self.save()

        if img := feed.feed.get('image', {}).get('href'):
            transaction.on_commit(
                lambda: download_artwork.delay(
                    self.pk,
                    img
                )
            )

        ids = []
        for entry in feed.entries:
            enclosure = None
            for link in entry.get('links', []):
                if link['rel'] == 'enclosure':
                    enclosure = link['href']

            if not enclosure:
                continue

            if entry.get('guidislink'):
                identifier = entry.link
            else:
                identifier = entry.id

            obj = self.episodes.select_for_update().filter(
                identifier=identifier
            ).first() or Episode(
                podcast=self,
                identifier=identifier
            )

            obj.title = entry.title
            obj.published_on = parse_date(entry.published)
            obj.enclosure = enclosure
            obj.description = html.strip_tags(
                entry.get('summary', '')
            )

            obj.webpage = entry.get('link')
            obj.type = entry.get('itunes_episodetype', 'full')
            obj.season = entry.get('itunes_season')
            obj.episode = entry.get('itunes_episode')

            if duration := entry.get('itunes_duration'):
                obj.duration = parse_duration(duration)

            obj.save()
            ids.append(obj.pk)

        if not self.op3_id:
            transaction.on_commit(
                lambda: set_op3_id.delay(self.pk)
            )

        self.episodes.exclude(pk__in=ids).delete()

    class Meta:
        ordering = ('name',)
        get_latest_by = 'created_on'


class Episode(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    podcast = models.ForeignKey(
        Podcast,
        on_delete=models.CASCADE,
        related_name='episodes'
    )

    identifier = models.CharField(max_length=1024, db_index=True)
    title = models.CharField(max_length=1024)
    published_on = models.DateTimeField()
    enclosure = models.URLField(max_length=1024)
    duration = models.PositiveIntegerField()
    description = models.TextField()
    webpage = models.URLField(null=True, blank=True)
    type = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        choices=(
            ('full', 'Full'),
            ('bonus', 'Bonus'),
            ('trailer', 'Trailer')
        )
    )

    season = models.PositiveIntegerField(null=True, blank=True)
    episode = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_duration_display(self):
        if self.duration > (60 * 60):
            return time.strftime(
                '%H:%M:%S',
                time.gmtime(int(self.duration))
            )

        return time.strftime(
            '%M:%S',
            time.gmtime(int(self.duration))
        )

    class Meta:
        unique_together = ('identifier', 'podcast')
        ordering = ('-season', '-episode', '-published_on')
        get_latest_by = 'published_on'


class Promo(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    def upload_audio(self, filename):
        return 'creative/promos/%s%s' % (
            self.id,
            os.path.splitext(filename)[-1]
        )

    podcast = models.ForeignKey(
        Podcast,
        on_delete=models.CASCADE,
        related_name='promos'
    )

    title = models.CharField(max_length=100)
    audio = models.FileField(
        upload_to=upload_audio,
        max_length=255
    )

    duration = models.PositiveIntegerField(null=True)
    description = models.TextField()

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.updated_on = timezone.now()
        super().save(*args, **kwargs)

    def get_duration_display(self):
        if self.duration > (60 * 60):
            return time.strftime(
                '%H:%M:%S',
                time.gmtime(int(self.duration))
            )

        return time.strftime(
            '%M:%S',
            time.gmtime(int(self.duration))
        )

    @property
    def filename(self):
        ext = os.path.splitext(self.audio.name)[-1]

        return '%s - %s%s' % (
            self.podcast.name.title(),
            self.title.title(),
            ext
        )

    class Meta:
        ordering = ('-created_on',)
        get_latest_by = 'created_on'
