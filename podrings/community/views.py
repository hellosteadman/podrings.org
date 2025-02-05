from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Count, Q
from django.http.response import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    FormView,
    TemplateView,
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
    View
)

from podrings import mail
from podrings.creative.models import Podcast, Promo
from podrings.seo.views import SEOMixin
from .forms import UserCreationForm, RingForm, CommitmentForm
from .models import Ring, Suggestion, Request, Commitment
from .tasks import build_suggestions
import jwt
import os


class CreateUserView(SEOMixin, FormView):
    form_class = UserCreationForm
    template_name = 'registration/user_form.html'
    seo_title = 'Create an account'

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'next': self.request.GET.get('next', self.request.POST.get('next'))
        }

    @transaction.atomic
    def form_valid(self, form):
        form.save()
        token = jwt.encode(
            {
                'next': (
                    self.request.POST.get('next') or
                    settings.LOGIN_REDIRECT_URL
                ),
                'aud': form.instance.email,
                'exp': timezone.now() + timezone.timedelta(days=1)
            },
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        mail.send(
            'Confirm email address',
            form.instance.email,
            render_to_string(
                'registration/confirm_email.md',
                {
                    'object': form.instance
                }
            ),
            primary_url='http%s://%s%s' % (
                not settings.DEBUG and 's' or '',
                settings.DOMAIN,
                reverse('confirm_user_email', args=(token,))
            ),
            primary_cta='Confirm address'
        )

        return HttpResponseRedirect(
            reverse('user_created')
        )


class UserCreatedView(SEOMixin, TemplateView):
    template_name = 'registration/user_created.html'
    seo_title = 'Check your inbox'
    robots = 'noindex'


class ConfirmEmailView(View):
    def get(self, request, *args, **kwargs):
        try:
            token = jwt.decode(
                kwargs['token'],
                settings.SECRET_KEY,
                algorithms=('HS256',),
                options={
                    'verify_aud': False
                }
            )
        except jwt.DecodeError:
            raise Http404('Invalid token.')

        for user in User.objects.filter(email=token['aud']):
            user.is_active = True
            user.save(
                update_fields=('is_active',)
            )

            messages.success(request, _('Welcome aboard!'))
            return HttpResponseRedirect(
                token['next']
            )

        raise Http404('Invalid token.')


class LogoutView(TemplateView):
    template_name = 'registration/logged_out.html'

    def get(self, request):
        if self.request.method == 'GET':
            logout(request)
            messages.success(request, _('You have been logged out.'))

        return super().get(request)


class RingListView(SEOMixin, ListView):
    model = Ring

    def get_queryset(self):
        return super().get_queryset().filter(
            approved_on__isnull=False
        ).annotate(
            podcasts=Count(
                'memberships',
                filter=Q(
                    memberships__approved_on__isnull=False
                )
            )
        ).distinct()


class SuggestionListView(LoginRequiredMixin, RingListView):
    def get_queryset(self):
        return Suggestion.objects.filter(
            host__created_by=self.request.user
        ).select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        podcasts = defaultdict(list)
        podcasts_by_id = {}

        for obj in self.get_queryset():
            podcasts[obj.host_id].append(obj.promo)
            if obj.host_id not in podcasts_by_id:
                podcasts_by_id[obj.host_id] = obj.host

        context['object_list'] = [
            {
                'podcast': podcasts_by_id[pk],
                'promos': promos
            } for pk, promos in podcasts.items() if any(promos)
        ]

        return context


class CreateRingView(SEOMixin, LoginRequiredMixin, CreateView):
    model = Ring
    form_class = RingForm
    seo_title = 'Create a podring'

    def get_initial(self):
        return {
            'description': 'A little more info about the podring',
            'rules': open(
                os.path.join(
                    os.path.dirname(__file__),
                    'fixtures',
                    'rules.txt'
                )
            ).read().strip()
        }

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'user': self.request.user
        }

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.approved_on:
            message = 'Your podring is ready to accept submissions.'
        else:
            message = 'Your podring is awaiting approval.'

        messages.success(self.request, _(message))
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class RingMixin(SEOMixin):
    def get_ring(self):
        return self.object

    def get_context_data(self, **kwargs):
        obj = self.get_ring()
        admins = obj.admins
        admin = (
            self.request.user.is_authenticated and
            admins.filter(user=self.request.user).first()
        )

        is_member = (
            self.request.user.is_authenticated and
            obj.memberships.filter(
                podcast__created_by=self.request.user
            ).exists()
        )

        if self.request.user.is_authenticated:
            podcasts_to_add = self.request.user.podcasts.exclude(
                memberships__ring=obj
            ).exclude(
                joining_requests__ring=obj
            )
        else:
            podcasts_to_add = []

        return {
            **super().get_context_data(**kwargs),
            'is_member': not not (admin or is_member),
            'can_edit': admin and admin.can_edit,
            'can_approve': admin and admin.can_approve,
            'can_remove': admin and admin.can_remove,
            'can_delete': admin and admin.can_delete,
            'can_transfer': admin and admin.can_transfer and admins.exclude(
                user=self.request.user
            ).exists(),
            'podcasts_to_add': podcasts_to_add,
            'pending_requests': obj.joining_requests.filter(
                approved_on=None
            ),
            'podcasts': [
                membership.podcast
                for membership in obj.memberships.select_related().annotate(
                    promo_count=Count('podcast__promos')
                ).order_by(
                    '-promo_count',
                    'podcast__downloads_per_month',
                    '-created_on'
                )
            ]
        }


class RingDetailView(RingMixin, DetailView):
    model = Ring

    def get_queryset(self):
        q = Q(
            approved_on__isnull=False
        )

        if self.request.user.is_authenticated:
            q |= Q(
                admins__user=self.request.user
            )

        return super().get_queryset().filter(q)


class UpdateRingView(RingMixin, LoginRequiredMixin, UpdateView):
    model = Ring
    form_class = RingForm
    seo_title = 'Update podring'

    def get_queryset(self):
        return super().get_queryset().filter(
            admins__user=self.request.user,
            admins__can_edit=True
        )

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'user': self.request.user
        }

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Your podring has been updated.'))
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class JoinRingView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        ring = get_object_or_404(
            Ring,
            slug=kwargs['slug']
        )

        podcast = get_object_or_404(
            Podcast,
            apple_id=kwargs['apple_id']
        )

        if podcast.created_by != self.request.user:
            messages.error(request, _('This is not one of your podcasts.'))
            return HttpResponseRedirect(
                ring.get_absolute_url()
            )

        if request.method != 'GET':
            return HttpResponseRedirect(
                ring.get_absolute_url()
            )

        success_url = (
            request.GET.get('layout') == 'onboarding' and
            '%s?modal=promos' % podcast.get_absolute_url() or
            ring.get_absolute_url()
        )

        with transaction.atomic():
            # If the logged-in user is already an admin
            # of this ring, and has permission to approve
            # new additions...
            if ring.admins.filter(
                user=podcast.created_by,
                can_approve=True
            ).exists():
                # If the podcast is already part of this ring...
                if ring.memberships.filter(podcast=podcast).exists():
                    messages.info(
                        request,
                        _('This podcast is already part of the ring.')
                    )
                else:
                    # Add the podcast to the ring, and mark it
                    # as approved, since it's owned by a ring admin
                    # with approval permission.

                    ring.memberships.create(
                        podcast=podcast,
                        approved_on=timezone.now(),
                        approved_by=request.user
                    )

                    messages.success(
                        request,
                        _('Added this podcast to the ring.')
                    )

                # Redirect to the ring homepage
                return HttpResponseRedirect(success_url)

            # If the user has already asked for this podcast
            # to be part of the ring...
            if ring.joining_requests.filter(
                created_by=request.user,
                podcast=podcast
            ).exists():
                messages.info(
                    request,
                    _('Your request to join has already been sent.')
                )

                # Redirect to the ring homepage
                return HttpResponseRedirect(success_url)

            # Create a new joining request
            obj = ring.joining_requests.create(
                created_by=request.user,
                podcast=podcast
            )

            # Email ring admins with approval permissions
            # and ask them to approve the podcast.
            transaction.on_commit(obj.send_email)
            messages.success(
                request,
                _('Joining request sent.')
            )

            # Redirect to the ring homepage, setting a
            # query parameter to show a confirmation modal.
            return HttpResponseRedirect(
                request.GET.get('layout') == 'onboarding' and
                success_url or (
                    '%s?view=request-sent' % ring.get_absolute_url()
                )
            )


class ShareRingView(RingMixin, LoginRequiredMixin, DetailView):
    model = Ring
    template_name = 'community/ring_share.html'
    seo_title = 'Share podring'


class RingQRCodeView(View):
    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(Ring, slug=kwargs['slug'])
        code = obj.get_qr_code()

        response = HttpResponse(content_type='image/svg+xml')
        code.save(response)
        return response


class DeleteRingView(RingMixin, LoginRequiredMixin, DeleteView):
    model = Ring
    seo_title = 'Delete podring'

    def get_queryset(self):
        return super().get_queryset().filter(
            admins__user=self.request.user,
            admins__can_delete=True
        )

    @transaction.atomic()
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Your podring has been deleted.'))
        return response

    def get_success_url(self):
        return reverse('suggestion_list')


class JoinRequestListView(RingMixin, LoginRequiredMixin, ListView):
    seo_title = 'Members'

    def get_queryset(self):
        self.object = get_object_or_404(
            Ring,
            slug=self.kwargs['slug'],
            admins__user=self.request.user,
            admins__can_approve=True
        )

        return self.object.joining_requests.select_related().prefetch_related()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'object': self.object
        }


class JoinRequestDetailView(RingMixin, LoginRequiredMixin, DetailView):
    seo_title = 'Members'
    episodes_per_page = 10

    def get_queryset(self):
        ring = get_object_or_404(
            Ring,
            slug=self.kwargs['slug'],
            admins__user=self.request.user,
            admins__can_approve=True
        )

        return ring.joining_requests.select_related().prefetch_related()

    def get_ring(self):
        return self.object.ring

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', '1')
        obj = self.get_object().podcast
        episodes = obj.episodes

        paginator = Paginator(
            episodes.exclude(type='trailer'),
            self.episodes_per_page
        )

        try:
            page = paginator.page(page)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = None

        return {
            **super().get_context_data(**kwargs),
            'trailer': episodes.filter(type='trailer').first(),
            'page_obj': page,
            'request': self.request
        }


class RequestActionView(LoginRequiredMixin, View):
    def get_object(self):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(
                Request,
                ring__slug=self.kwargs['slug'],
                ring__admins__user=self.request.user,
                ring__admins__can_approve=True,
                pk=self.kwargs['pk']
            )

        return self.object


class AcceptRequestView(RequestActionView):
    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.method == 'GET':
            with transaction.atomic():
                obj.approve(request.user)

        return HttpResponseRedirect(
            obj.ring.get_absolute_url()
        )


class DeleteRequestView(RequestActionView):
    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.method == 'GET':
            with transaction.atomic():
                obj.delete()
                obj.ring.memberships.filter(
                    podcast=obj.podcast
                ).delete()

        return HttpResponseRedirect(
            obj.ring.get_absolute_url()
        )


class CreateCommitmentView(LoginRequiredMixin, CreateView):
    model = Commitment
    form_class = CommitmentForm

    def get_initial(self):
        initial = {
            **super().get_initial(),
            'slot': 'mid'
        }

        podcasts = self.request.user.podcasts
        if self.request.GET.get('host'):
            podcasts = podcasts.filter(
                apple_id=self.request.GET['host']
            )

        if podcast := podcasts.order_by(
            '-fetched_on'
        ).first():
            initial['host'] = podcast
            dates = podcast.episodes.values_list(
                'published_on',
                flat=True
            ).order_by(
                '-published_on'
            )[:2]

            today = timezone.now().date()

            if dates.count() > 1:
                latest = dates[0].date()
                delta = latest - dates[1].date()
                run_on = latest + delta

                while run_on <= today:
                    run_on += delta

                initial['run_on'] = run_on

        return initial

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'user': self.request.user,
            'instance': Commitment(
                promo=get_object_or_404(
                    Promo,
                    podcast__apple_id=self.kwargs['apple_id'],
                    pk=self.kwargs['promo_id']
                ),
                created_by=self.request.user
            )
        }

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        transaction.on_commit(
            lambda: build_suggestions.delay(
                form.instance.host_id
            )
        )

        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class CommitmentDetailView(LoginRequiredMixin, DetailView):
    model = Commitment

    def get_queryset(self):
        return super().get_queryset().filter(
            promo=get_object_or_404(
                Promo,
                podcast__apple_id=self.kwargs['apple_id'],
                pk=self.kwargs['promo_id']
            )
        ).select_related()

    def get_context_data(self, **kwargs):
        obj = self.get_object()

        return {
            **super().get_context_data(**kwargs),
            'shownotes_inclusion': {
                'markdown': obj.get_shownotes_inclusion(),
                'html': obj.get_shownotes_inclusion('html'),
                'plain': obj.get_shownotes_inclusion('plain')
            }
        }
