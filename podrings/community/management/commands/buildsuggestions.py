from django.core.management.base import BaseCommand
from podrings.community.models import Suggestion
from podrings.community.tasks import build_suggestions
from podrings.creative.models import Podcast


class Command(BaseCommand):
    help = 'Build podcast promo recommendations'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        Suggestion.objects.all().delete()

        for pk in Podcast.objects.values_list('pk', flat=True):
            build_suggestions.delay(pk)
