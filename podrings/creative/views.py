from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView,
    FormView,
    DetailView,
    CreateView,
    TemplateView,
    View
)

from podrings.community.tasks import build_suggestions
from podrings.seo.views import SEOMixin
from .forms import PodcastForm, PromoForm
from .models import Podcast, Promo
import jwt


class PodcastListView(SEOMixin, LoginRequiredMixin, ListView):
    model = Podcast
    template_name = 'creative/user_podcast_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(
            created_by=self.request.user
        )


class CreatePodcastView(SEOMixin, LoginRequiredMixin, FormView):
    form_class = PodcastForm
    template_name = 'creative/podcast_form.html'
    seo_title = 'Add podcast'

    def get_form_kwargs(self):
        return {
            'user': self.request.user,
            **super().get_form_kwargs()
        }

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'next': self.request.GET.get('next', self.request.POST.get('next'))
        }

    @transaction.atomic
    def form_valid(self, form):
        kwargs = {}
        if next_url := (
            self.request.POST.get('next', self.request.GET.get('next'))
        ):
            kwargs['next'] = next_url

        form.send_code(**kwargs)
        return HttpResponseRedirect(
            reverse('podcast_created')
        )


class ConfirmPodcastView(LoginRequiredMixin, View):
    @transaction.atomic
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

        apple_id = token['id']
        obj = Podcast.objects.fetch_from_apple_id(
            apple_id,
            created_by=self.request.user
        )

        if obj.created_by == self.request.user:
            messages.success(request, _('Podcast confirmed.'))

        return HttpResponseRedirect(
            token['next']
        )


class PodcastCreatedView(SEOMixin, LoginRequiredMixin, TemplateView):
    template_name = 'creative/podcast_created.html'
    seo_title = 'Podcast added'


class PodcastMixin(SEOMixin):
    def get_podcast(self):
        return self.get_object()

    def get_context_data(self, **kwargs):
        obj = self.get_podcast()
        user = self.request.user

        return {
            **super().get_context_data(**kwargs),
            'can_edit': user.is_authenticated and obj.created_by == user
        }


class PodcastDetailView(PodcastMixin, DetailView):
    model = Podcast
    slug_field = 'apple_id'
    slug_url_kwarg = 'apple_id'
    robots = 'noindex'
    episodes_per_page = 10

    def get_context_data(self, **kwargs):
        page = self.request.GET.get('page', '1')
        obj = self.get_object()
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
            'page_obj': page
        }


class PromoMixin(PodcastMixin, LoginRequiredMixin):
    model = Promo

    def get_podcast(self):
        return get_object_or_404(
            Podcast,
            created_by=self.request.user,
            apple_id=self.kwargs['apple_id']
        )

    def get_queryset(self):
        return super().get_queryset().filter(
            podcast=self.get_podcast()
        )


class PromoListView(PromoMixin, ListView):
    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'podcast': self.get_podcast()
        }


class CreatePromoView(PromoMixin, CreateView):
    model = Promo
    form_class = PromoForm

    def get_initial(self):
        now = timezone.now()

        return {
            **super().get_initial(),
            'title': _('%(month)s, %(year)s Promo') % {
                'month': now.strftime('%B'),
                'year': now.strftime('%Y')
            }
        }

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'layout': (
                self.request.GET.get('layout', self.request.POST.get('layout'))
            )
        }

    @transaction.atomic
    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.podcast = self.get_podcast()
        obj.created_by = self.request.user
        obj.save()

        messages.success(self.request, _('Your promo has been uploaded.'))
        success_url = reverse(
            'podcast_promos',
            args=(obj.podcast.apple_id,)
        )

        if self.request.POST.get('layout') == 'onboarding':
            success_url = reverse(
                'promo_created',
                args=(obj.podcast.apple_id,)
            )

            build_suggestions(obj.podcast.pk)

        return HttpResponseRedirect(success_url)


class PromoCreatedView(SEOMixin, LoginRequiredMixin, DetailView):
    template_name = 'creative/promo_created.html'
    seo_title = 'Promo created'

    def get_object(self):
        return get_object_or_404(
            Podcast,
            created_by=self.request.user,
            apple_id=self.kwargs['apple_id']
        )

    def get_context_data(self, **kwargs):
        obj = self.get_object()

        return {
            **super().get_context_data(**kwargs),
            'object_list': obj.suggestions.all()[:3]
        }
