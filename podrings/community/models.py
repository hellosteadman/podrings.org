from django.conf import settings
from django.db import models, transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from qrcode import make
from qrcode.image.svg import SvgImage
from podrings import mail
from uuid import uuid4
import os


class Ring(models.Model):
    def upload_header(self, filename):
        return 'rings/%s/header%s' % (
            self.slug,
            os.path.splitext(filename)[-1]
        )

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField('URL', max_length=255, null=True, blank=True)
    popularity = models.IntegerField(default=0, editable=False)
    moderation_tags = models.ManyToManyField(
        'moderation.Tag',
        related_name='rings',
        blank=True
    )

    created_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='ring_approvals',
        null=True,
        blank=True
    )

    header = models.ImageField(
        upload_to=upload_header,
        max_length=255,
        null=True,
        blank=True
    )

    rules = models.TextField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('ring_detail', args=(self.slug,))

    def approve(self, approved_by):
        self.approved_on = timezone.now()
        self.approved_by = approved_by
        self.save(
            update_fields=('approved_on', 'approved_by')
        )

        for admin in self.admins.filter(
            can_delete=True
        ).select_related():
            mail.send(
                _('Your Podring is live'),
                admin.user.email,
                render_to_string(
                    'community/ring_approved_email.md',
                    {
                        'object': self,
                        'user': admin.user
                    }
                ),
                primary_url='http%s://%s%s' % (
                    not settings.DEBUG and 's' or '',
                    settings.DOMAIN,
                    self.get_absolute_url()
                ),
                primary_cta='Manage your podring'
            )

    def get_sharing_url(self):
        return 'http%s://%s%s' % (
            not settings.DEBUG and 's' or '',
            settings.DOMAIN,
            self.get_absolute_url()
        )

    def get_qr_code(self):
        return make(
            self.get_sharing_url(),
            image_factory=SvgImage
        )

    class Meta:
        ordering = ('-popularity', '-approved_on')
        get_latest_by = 'created_on'


class Admin(models.Model):
    ring = models.ForeignKey(
        Ring,
        on_delete=models.CASCADE,
        related_name='admins'
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='adminships'
    )

    can_edit = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_remove = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_transfer = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user)

    class Meta:
        ordering = (
            '-can_remove',
            '-can_approve',
            'user__last_name',
            'user__first_name',
            'user__email',
            '-created_on'
        )

        get_latest_by = 'created_on'
        unique_together = ('user', 'ring')


class Member(models.Model):
    ring = models.ForeignKey(
        Ring,
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    podcast = models.ForeignKey(
        'creative.Podcast',
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    created_on = models.DateTimeField(auto_now_add=True)
    approved_on = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='membership_approvals',
        null=True,
        blank=True
    )

    def __str__(self):
        return str(self.podcast)

    class Meta:
        ordering = ('created_on',)
        get_latest_by = 'created_on'
        unique_together = ('podcast', 'ring')


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    ring = models.ForeignKey(
        Ring,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    kind = models.CharField(
        max_length=6,
        choices=(
            ('admin', 'Admin'),
            ('member', 'Member')
        )
    )

    created_on = models.DateTimeField(auto_now_add=True)
    invitee_name = models.CharField(max_length=100)
    invitee_email = models.EmailField(max_length=255)
    podcast = models.ForeignKey(
        'creative.Podcast',
        on_delete=models.CASCADE,
        related_name='invitations',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.get_kind_display()

    class Meta:
        ordering = ('-created_on',)
        get_latest_by = 'created_on'


class Request(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    ring = models.ForeignKey(
        Ring,
        on_delete=models.CASCADE,
        related_name='joining_requests'
    )

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='joining_requests',
        null=True,
        blank=True
    )

    podcast = models.ForeignKey(
        'creative.Podcast',
        on_delete=models.CASCADE,
        related_name='joining_requests'
    )

    sent_on = models.DateTimeField(null=True, blank=True)

    approved_on = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='joining_request_approvals',
        null=True,
        blank=True
    )

    def __str__(self):
        return str(self.ring)

    def get_absolute_url(self):
        return reverse('join_request_detail', args=(self.ring.slug, self.pk))

    def send_email(self):
        image_url = None

        if self.podcast.artwork:
            thumbnailer = get_thumbnailer(self.podcast.artwork)
            thumbnail = thumbnailer.get_thumbnail(
                {
                    'size': (512, 512),
                    'crop': True
                }
            )

            image_url = thumbnail.url

        for admin in self.ring.admins.filter(
            can_approve=True
        ).select_related():
            mail.send(
                _('Podring joining request'),
                admin.user.email,
                render_to_string(
                    'community/approval_request_email.md',
                    {
                        'user': admin.user,
                        'object': self
                    }
                ),
                image_url=image_url,
                primary_url='http%s://%s%s' % (
                    not settings.DEBUG and 's' or '',
                    settings.DOMAIN,
                    self.get_absolute_url()
                ),
                primary_cta='Review podcast'
            )

        self.sent_on = timezone.now()
        self.save(update_fields=('sent_on',))

    @transaction.atomic
    def approve(self, approved_by):
        self.approved_on = timezone.now()
        self.approved_by = approved_by
        self.save(
            update_fields=(
                'approved_on',
                'approved_by'
            )
        )

        obj = self.ring.memberships.create(
            podcast=self.podcast,
            approved_on=self.approved_on,
            approved_by=self.approved_by
        )

        mail.send(
            _('Welcome to %s' % self.ring.name),
            self.podcast.created_by.email,
            render_to_string(
                'community/request_approved_email.md',
                {
                    'podcast': self.podcast,
                    'ring': self.ring
                }
            ),
            primary_url='http%s://%s%s' % (
                not settings.DEBUG and 's' or '',
                settings.DOMAIN,
                self.podcast.get_absolute_url()
            ),
            primary_cta='Manage your promos'
        )

        return obj

    class Meta:
        ordering = ('-created_on',)
        get_latest_by = 'created_on'
        unique_together = ('podcast', 'ring')


class Suggestion(models.Model):
    host = models.ForeignKey(
        'creative.Podcast',
        on_delete=models.CASCADE,
        related_name='suggestions'
    )

    promo = models.ForeignKey(
        'creative.Promo',
        on_delete=models.CASCADE,
        related_name='suggestions'
    )

    ordering = models.PositiveIntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('ordering',)
        get_latest_by = 'created_on'


class Commitment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)

    promo = models.ForeignKey(
        'creative.Promo',
        on_delete=models.CASCADE,
        related_name='commitments'
    )

    host = models.ForeignKey(
        'creative.Podcast',
        on_delete=models.CASCADE,
        related_name='commitments'
    )

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='commitments',
        null=True,
        blank=True
    )

    run_on = models.DateField()
    slot = models.CharField(
        max_length=4,
        choices=(
            ('pre', 'Beginning of episode'),
            ('mid', 'Middle of episode'),
            ('post', 'End of episode')
        )
    )

    def __str__(self):
        return self.get_slot_display()

    def get_absolute_url(self):
        return reverse(
            'commitment_detail',
            args=(
                self.promo.podcast.apple_id,
                self.promo.pk,
                self.pk
            )
        )

    def get_tracking_url(self):
        return 'https://episodes.fm/%d' % self.promo.podcast.apple_id

    def get_shownotes_inclusion(self, text_format='markdown'):
        podcast_ids = set([self.host_id, self.promo.podcast_id])

        return render_to_string(
            'community/commitments_shownotes_inclusion.%s' % {
                'markdown': 'md',
                'html': 'html',
                'plain': 'txt'
            }[text_format],
            {
                'object': self,
                'rings': Ring.objects.filter(
                    memberships__podcast_id__in=podcast_ids
                ).distinct()
            }
        ).strip()

    class Meta:
        ordering = ('-run_on',)
        get_latest_by = 'created_on'
