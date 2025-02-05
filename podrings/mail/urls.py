from django.conf import settings
from django.urls import path
from .views import PreferencesUpdatedView, PreferencesView, PreviewView


urlpatterns = [
    path('prefs/updated/', PreferencesUpdatedView.as_view(), name='mail_preferences_updated'),  # NOQA
    path('prefs/<str:email_hash>/', PreferencesView.as_view(), name='mail_preferences')  # NOQA
]


if settings.DEBUG:
    urlpatterns += [
        path('preview/', PreviewView.as_view(), name='email_review')
    ]
