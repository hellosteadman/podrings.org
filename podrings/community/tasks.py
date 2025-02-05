from django.db import transaction
from django_rq.decorators import job


@job('default', timeout='1m')
@transaction.atomic()
def build_suggestions(podcast_id):
    """
    This function builds a list of promos that can be
    included by a host podcast.
    """

    def get_frequency(promo):
        return host.commitments.filter(
            promo__podcast=promo.podcast
        ).count()

    from podrings.creative.models import Podcast, Promo

    for host in Podcast.objects.filter(pk=podcast_id):
        promos = []
        max_downloads = Promo.objects.filter(
            podcast__memberships__ring__in=host.memberships.values_list(
                'ring_id',
                flat=True
            ),
            podcast__op3_id__isnull=False
        ).values_list(
            'podcast__downloads_per_month',
            flat=True
        ).order_by(
            '-podcast__downloads_per_month'
        ).first() or 0
        promoted_podcsats = []

        for promo in Promo.objects.filter(
            podcast__memberships__ring__in=host.memberships.values_list(
                'ring_id',
                flat=True
            )
        ).exclude(
            podcast_id=host.pk
        ).distinct().select_related().iterator():
            if promo.podcast_id in promoted_podcsats:
                continue

            promoted_podcsats.append(promo.podcast_id)
            if promo.podcast.op3_id:
                offset = max_downloads - promo.podcast.downloads_per_month
            else:
                offset = 0

            promos.append(
                {
                    'obj': promo,
                    'offset': offset
                }
            )

        promos = [
            o['obj']
            for o in sorted(promos, key=lambda o: o['offset'])
        ]

        host.suggestions.all().delete()

        for i, promo in enumerate(
            sorted(promos, key=get_frequency)
        ):
            host.suggestions.create(
                promo=promo,
                ordering=i
            )
