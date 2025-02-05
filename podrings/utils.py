from django.conf import settings
from django.core.files import File
from mimetypes import guess_extension
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse
from . import USER_AGENT
import os
import requests
import time


def unique_id():
    return hex(int(time.time() * 10000000))[2:]


def download_file(url, max_tries=3):
    headers = {
        'User-Agent': USER_AGENT
    }

    tries = 0
    while True:
        response = requests.get(
            url,
            headers=headers,
            stream=True
        )

        if response.status_code == 304:
            return

        if response.status_code < 500:
            response.raise_for_status()
            break

        tries += 1

        if tries == max_tries:
            response.raise_for_status()

        time.sleep(
            getattr(settings, 'DOWNLOAD_RETRY_SLEEP', 5)
        )

    urlparts = urlparse(url)
    ext = os.path.splitext(urlparts.path)[-1]

    if not ext and 'Content-Type' in response.headers:
        ext = guess_extension(response.headers['Content-Type'])

    with NamedTemporaryFile(suffix=ext, delete=False) as temp:
        try:
            for chunk in response.iter_content(chunk_size=1024):
                temp.write(chunk)
        except Exception:
            os.remove(temp.name)
            raise

    return File(
        open(temp.name, 'rb'),
        name='%s%s' % (unique_id(), ext)
    )


def parse_duration(string):
    if not string:
        return 0

    if ':' not in string:
        return float(string)

    parts = string.split(':')
    parts = [int(part) for part in parts]

    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        raise ValueError('Invalid duration format')

    total_seconds = hours * 3600 + minutes * 60 + seconds
    return float(total_seconds)
