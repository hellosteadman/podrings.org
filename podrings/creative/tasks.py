from base64 import urlsafe_b64encode
from django.conf import settings
from django.db import transaction
from django_rq.decorators import job
from mutagen import File
from podrings import USER_AGENT
from podrings.utils import download_file
import requests


@job('default', timeout='1m')
@transaction.atomic
def download_artwork(podcast_id, url):
    from .models import Podcast

    for obj in Podcast.objects.select_for_update().filter(
        pk=podcast_id
    ):
        obj.artwork = download_file(url)
        obj.save(update_fields=('artwork',))


@job('default', timeout='5m')
def convert_episode_to_promo(episode_id):
    from .models import Episode

    for obj in Episode.objects.filter(
        pk=episode_id,
        type='trailer'
    ).select_related():
        audio = download_file(obj.enclosure)
        meta = File(audio)
        obj.podcast.promos.all().delete()

        if not obj.podcast.promos.exists():
            obj.podcast.promos.create(
                title=obj.title,
                audio=audio,
                duration=int(meta.info.length),
                created_on=obj.published_on
            )


@job('default', timeout='1m')
@transaction.atomic
def set_op3_id(podcast_id):
    from .models import Podcast

    for obj in Podcast.objects.select_for_update().filter(
        pk=podcast_id
    ):
        b64_rss = urlsafe_b64encode(obj.rss.encode('utf-8')).decode('utf-8')
        response = requests.get(
            'https://op3.dev/api/1/shows/' + b64_rss,
            headers={
                'User-Agent': USER_AGENT,
                'Authorization': 'Bearer %s' % settings.OP3_API_KEY
            }
        )

        if response.status_code == 404:
            obj.op3_id = None
            obj.save(update_fields=('op3_id',))
            return

        response.raise_for_status()
        response = response.json()
        obj.op3_id = response['showUuid']
        obj.save(update_fields=('op3_id',))

        transaction.on_commit(
            lambda: set_downloads_per_month.delay(obj.pk)
        )


@job('default', timeout='1m')
@transaction.atomic
def set_downloads_per_month(podcast_id):
    from .models import Podcast

    for obj in Podcast.objects.select_for_update().filter(
        pk=podcast_id
    ):
        response = requests.get(
            'https://op3.dev/api/1/queries/show-download-counts',
            params={
                'showUuid': obj.op3_id.hex
            },
            headers={
                'User-Agent': USER_AGENT,
                'Authorization': 'Bearer %s' % settings.OP3_API_KEY
            }
        )

        response.raise_for_status()
        response = response.json()
        response = response['showDownloadCounts']

        if results := response.get(obj.op3_id.hex):
            obj.downloads_per_month = results['monthlyDownloads']
            obj.save(update_fields=('downloads_per_month',))
