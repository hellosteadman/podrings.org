from django.contrib import admin
from .models import Podcast, Episode, Promo


class EpisodeInline(admin.StackedInline):
    model = Episode
    extra = 0

    def has_add_permission(self, request, obj):
        return False


@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_on', 'created_by')
    inlines = (EpisodeInline,)
    readonly_fields = (
        'name',
        'rss',
        'website',
        'artwork',
        'created_by'
    )


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ('title', 'podcast', 'created_on')

