from django import forms
from django.db import transaction
from .models import Tag, Preference


class PreferencesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.email_hash = kwargs.pop('email_hash')
        preferences = dict(
            Preference.objects.filter(
                email_hash=self.email_hash,
            ).values_list(
                'tag__slug',
                'subscribed'
            )
        )

        initial = kwargs.get('initial', {})

        for tag in Tag.objects.all():
            if tag.slug in preferences:
                initial['tag_%d' % tag.pk] = preferences[tag.slug]
            else:
                initial['tag_%d' % tag.pk] = True

        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        for tag in Tag.objects.all():
            self.fields['tag_%d' % tag.pk] = forms.BooleanField(
                label=tag.label,
                required=False
            )

    @transaction.atomic
    def save(self):
        for tag in Tag.objects.all():
            subscribed = self.cleaned_data.get('tag_%d' % tag.pk)
            if not Preference.objects.filter(
                email_hash=self.email_hash,
                tag=tag
            ).update(
                subscribed=subscribed
            ):
                if not subscribed:
                    Preference.objects.create(
                        email_hash=self.email_hash,
                        tag=tag,
                        subscribed=False
                    )
