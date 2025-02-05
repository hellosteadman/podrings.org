from django import forms
from django.conf import settings
from django.contrib.auth.forms import SetPasswordMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from podrings import mail
from podrings.creative.exceptions import FetchError
from podrings.creative.models import Podcast
from podrings.seo.helpers import title_case
from tempus_dominus.widgets import DatePicker
from .models import Ring, Request, Commitment
import time


class UserCreationForm(SetPasswordMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(
        label=_('Email address'),
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                'autocomplete': 'email'
            }
        )
    )

    password1, password2 = SetPasswordMixin.create_password_fields()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password2'].label = _('Confirm your password')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _('Someone has already signed up with this email address.')
            )

        return email.lower()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.username = self.cleaned_data['email']
        password = self.cleaned_data['password2']
        obj.set_password(password)
        obj.is_active = False

        if commit:
            obj.save()

        return obj

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email'
        )


class RingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['name'].label = _('Name your podring')
        self.fields['name'].widget.attrs['class'] = 'form-control-lg'
        self.fields['name'].help_text = _(
            'If you want to bring together podcasters who '
            'care about recycling for example, just call your '
            'podring <q>Recycling</q>.'
        )
        
        self.fields['header'].label = _('Header image (optional)')
        self.fields['header'].help_text = _(
            'Upload a landscape image (around 1,200 x 630 pixels).'
        )
        
        self.fields['description'].widget.attrs['style'] = 'min-height: 5rem'

        self.fields['url'].label = _('Associated website')
        self.fields['url'].help_text = _(
            'If you have a website associated with your podring, '
            'paste the URL here.'
        )

        self.fields['rules'].widget.attrs['style'] = 'min-height: 10rem'
        self.fields['rules'].help_text = _(
            'These are the rules members of your podring must accept '
            'and abide by in order to join and remain in your community. '
            'It’s up to you to enforce these rules.'
        )

        self.fields['moderation_tags'].widget = forms.CheckboxSelectMultiple(
            choices=self.fields['moderation_tags'].choices
        )

    def clean_name(self):
        name = self.cleaned_data['name']
        if name == name.lower():
            return title_case(name.title())

        if name == name.upper():
            return title_case(name.title())

        return name

    def save(self, commit=True):
        obj = super().save(commit=False)

        if not obj.slug:
            obj.slug = hex(int(time.time() * 10000000))[2:]

        if self.user.is_staff:
            obj.approved_on = timezone.now()
            obj.approved_by = self.user

        self.__new = not obj.pk
        obj.save()
        self.save_m2m()

        return obj

    def _save_m2m(self):
        super()._save_m2m()

        if self.__new:
            self.instance.admins.create(
                user=self.user,
                can_edit=True,
                can_approve=True,
                can_remove=True,
                can_delete=True,
                can_transfer=True
            )

            if not self.user.is_staff:
                image_url = None

                if self.instance.header:
                    thumbnailer = get_thumbnailer(self.instance.header)
                    thumbnail = thumbnailer.get_thumbnail(
                        {
                            'size': (512, 288),
                            'crop': True
                        }
                    )

                    image_url = thumbnail.url

                for user in User.objects.filter(
                    is_staff=True
                ):
                    mail.send(
                        'New podring',
                        user.email,
                        render_to_string(
                            'community/approve_ring_email.md',
                            {
                                'object': self.instance,
                                'user': user,
                                'creator': self.user
                            }
                        ),
                        image_url=image_url,
                        primary_url='http%s://%s%s' % (
                            not settings.DEBUG and 's' or '',
                            settings.DOMAIN,
                            reverse(
                                'admin:community_ring_change',
                                args=(self.instance.pk,)
                            )
                        ),
                        primary_cta='View details'
                    )

    class Meta:
        model = Ring
        fields = (
            'name',
            'header',
            'description',
            'url',
            'rules',
            'moderation_tags'
        )


class CreateRequestForm(forms.ModelForm):
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

    agree = forms.BooleanField(
        label=_('Confirm you agree to this podring’s rules')
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.ring = kwargs.pop('ring')
        self.from_owner = kwargs.pop('from_owner')
        super().__init__(*args, **kwargs)

        if self.from_owner:
            self.fields['agree'].label = _(
                'Confirm this is your podcast, and you have '
                'authority to add this podcast to a podring'
            )

    def clean_apple_id(self):
        apple_id = self.cleaned_data['apple_id']

        if self.ring.memberships.filter(podcast__apple_id=apple_id).exists():
            raise forms.ValidationError(
                _('This podcast is already part of the podring.')
            )

        if self.ring.joining_requests.filter(
            podcast__apple_id=apple_id
        ).exists():
            raise forms.ValidationError(
                _(
                    'This podcast is already in the process of joining '
                    'the podring.'
                )
            )

        try:
            self._podcast = Podcast.objects.fetch_from_apple_id(
                apple_id,
                created_by=self.user
            )
        except FetchError as ex:
            raise forms.ValidationError(ex.args[0])

        return self._podcast.apple_id

    @transaction.atomic
    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.ring = self.ring
        obj.created_by = self.user
        obj.podcast = self._podcast
        obj.save()

        self.save_m2m()
        return obj

    class Meta:
        model = Request
        fields = ()


class ConfirmRequestForm(forms.ModelForm):
    code = forms.IntegerField(
        label=_('Enter the confirmation code from your email'),
        widget=forms.TextInput(
            attrs={
                'autofocus': True,
                'autocorrect': 'off',
                'autocomplete': 'off'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        initial = kwargs.get('initial', {})
        initial['code'] = ''
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']
        if str(code) != str(self.instance.code):
            raise forms.ValidationError(
                _('That isn’t the right code.')
            )

        return int(code)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.approved_on = timezone.now()
        obj.approved_by = self.user

        if commit:
            obj.save()
            self.save_m2m()

        return obj

    def _save_m2m(self):
        super()._save_m2m()

        if self.instance.ring.admins.filter(
            user=self.user,
            can_approve=True
        ).exists():
            self.instance.podcast.memberships.create(
                ring=self.instance.ring,
                approved_on=self.instance.approved_on,
                approved_by=self.instance.approved_by
            )
        else:
            self.instance.send_approval_request()

    class Meta:
        model = Request
        fields = ('code',)


class RingAdminForm(forms.ModelForm):
    approved = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        if instance := kwargs.get('instance'):
            initial = kwargs.get('initial', {})

            if instance.approved_on:
                initial['approved'] = True
                kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

    class Meta:
        model = Ring
        fields = (
            'name',
            'description',
            'url',
            'moderation_tags',
            'header',
            'rules'
        )


class CommitmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        from podrings.community.models import Ring

        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        self.fields['host'] = forms.ModelChoiceField(
            label=_('Podcast hosting this promo'),
            queryset=self.user.podcasts.filter(
                memberships__ring__in=Ring.objects.filter(
                    memberships__podcast=self.instance.promo.podcast
                )
            ).exclude(
                pk=self.instance.promo.podcast_id
            )
        )

        self.fields['run_on'] = forms.DateField(
            label=_('Planned episode date'),
            help_text=_(
                'If you plan to run this on multiple episodes '
                'or you\'re using dynamic ad insertion, select '
                'the date of the next episode that will include '
                'this promo.'
            ),
            widget=DatePicker(
                options={
                    'minDate': timezone.now().strftime('%Y-%m-%d')
                }
            )
        )

        self.fields['slot'].label = _('Ad slot')
        self.fields['slot'].help_text = _(
            'Promos should be scheduled towards the last '
            'half of an episode. If you aren\'t sure when '
            'the promo will run, select the middle option '
            '(you won’t be held to it).'
        )

    class Meta:
        model = Commitment
        fields = (
            'host',
            'run_on',
            'slot'
        )
