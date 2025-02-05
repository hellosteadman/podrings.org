from django.db import transaction
from django.contrib import admin, messages
from .forms import RingAdminForm
from .models import Ring, Admin, Member, Invitation, Request, Commitment


class AdminInline(admin.TabularInline):
    model = Admin
    extra = 0


class MemberInline(admin.StackedInline):
    model = Member
    extra = 0


@admin.register(Ring)
class RingAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_on')
    list_filter = ('approved_on',)
    inlines = (AdminInline, MemberInline)
    filter_horizontal = ('moderation_tags',)
    readonly_fields = ('slug',)
    exclude = ('approved_on', 'approved_by')
    form = RingAdminForm

    @admin.action(description='Mark selected rings as approved')
    @transaction.atomic
    def approve(self, request, queryset):
        for obj in queryset.filter(approved_on=None):
            try:
                obj.approve(request.user)
            except Exception as ex:
                self.message_user(
                    request,
                    str(ex.args[0]),
                    level=messages.ERROR
                )

    actions = (approve,)

    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)

        if form.cleaned_data.get('approved') and not obj.approved_on:
            obj.approve(request.user)

        return obj


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('ring', 'kind', 'created_on')
    list_filter = ('kind',)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('podcast', 'ring', 'approved_on')
    list_filter = ('ring',)

    def has_add_permission(self, request):
        return False


@admin.register(Commitment)
class CommitmentAdmin(admin.ModelAdmin):
    list_display = ('promo__podcast', 'host', 'created_on', 'created_by')

    def has_add_permission(self, request):
        return False
