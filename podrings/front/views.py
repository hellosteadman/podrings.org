from django.db.models import Count, Q
from django.views.generic import TemplateView
from podrings.community.models import Ring
from podrings.creative.models import Promo
from podrings.seo.views import SEOMixin


class IndexView(SEOMixin, TemplateView):
    template_name = 'front/index.html'
    seo_title = 'Podrings: Indie podcast cross-promotion'

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            'ring_list': Ring.objects.annotate(
                approved_members=Count(
                    'memberships',
                    filter=Q(
                        memberships__approved_on__isnull=False
                    )
                )
            ).filter(
                approved_on__isnull=False,
                approved_members__gte=1
            ).order_by(
                '-created_on'
            ).distinct()[:12],
            'promo_list': Promo.objects.annotate(
                commitment_count=Count('commitments')
            ).order_by(
                '-commitment_count',
                '-podcast__downloads_per_month',
                '-podcast__created_by__is_staff',
                '-created_on'
            ).distinct()[:3]
        }
