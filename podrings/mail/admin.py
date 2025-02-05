from django.contrib import admin
from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug')
    prepopulated_fields = {
        'slug': ('label',)
    }

    fields = (
        'label',
        'slug'
    )
