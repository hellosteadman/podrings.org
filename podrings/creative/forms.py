from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mutagen import File
from podrings import mail
from .exceptions import FetchError
from .models import Podcast, Promo
import jwt


class PodcastForm(forms.Form):
    apple_id = forms.IntegerField(
        label=_('Search for your podcast by name'),
        widget=forms.TextInput(
            attrs={
                'data-pr-source': 'itunes',
                'autocomplete': 'off',
                'autocorrect': 'off',
                'autofocus': True
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_apple_id(self):
        apple_id = self.cleaned_data['apple_id']

        try:
            self._feed = Podcast.objects.parse_feed(apple_id)
        except FetchError as ex:
            raise forms.ValidationError(ex.args[0])

        return int(apple_id)

    def send_code(self, **kwargs):
        apple_id = int(self.cleaned_data['apple_id'])
        email = self._feed.feed.get('author_detail', {}).get('email')
        data = {
            'id': apple_id,
            'aud': email,
            'exp': timezone.now() + timezone.timedelta(hours=24)
        }

        data['next'] = (
            kwargs.pop('next', None) or reverse(
                'podcast_detail',
                args=(apple_id,)
            )
        ).replace(
            ':apple_id',
            str(apple_id)
        )

        token = jwt.encode(
            data,
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        url = 'http%s://%s%s' % (
            not settings.DEBUG and 's' or '',
            settings.DOMAIN,
            reverse('confirm_podcast', args=(token,))
        )

        mail.send(
            'Verify your podcast',
            email,
            render_to_string(
                'creative/confirm_feed_email.md',
                {
                    'feed': self._feed.feed
                }
            ),
            primary_url=url,
            primary_cta='Confirm your podcast'
        )


class AudioUploadInput(forms.FileInput):
    template_name = 'creative/forms/widgets/audio_upload.html'

    def get_context(self, name, value, attrs):
        attrs['accept'] = 'audio/*'
        return super().get_context(name, value, attrs)


class PromoForm(forms.ModelForm):
    audio = forms.FileField(
        label=_('Select your audio file'),
        widget=AudioUploadInput,
        help_text=_(
            'We recommend uploading a high-quality, uncompressed '
            'version of your promo. We support MP3, AAC, FLAC, '
            'Ogg, and AIFF files.'
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = _(
            'Don’t include the name of your podcast in your '
            'promo title.'
        )

    def clean_audio(self):
        audio = self.cleaned_data.get('audio')
        meta = File(audio)

        if meta is None:
            raise forms.ValidationError(
                _(
                    'This type of file is not supported.'
                    'Supported promo formats are MP3, AAC, FLAC, ',
                    'Ogg, and AIFF.'
                )
            )

        if not hasattr(meta, 'info') or not hasattr(meta.info, 'length'):
            raise forms.ValidationError(
                _('Could not determine audio duration.')
            )

        self._audio_metadata = meta
        return audio

    def save(self, commit=True):
        promo = super().save(commit=False)
        promo.duration = int(self._audio_metadata.info.length)

        if commit:
            promo.save()

        return promo

    class Meta:
        model = Promo
        fields = (
            'title',
            'audio'
        )
