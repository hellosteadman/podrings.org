from django.urls import path
from .views import (
    PodcastListView,
    CreatePodcastView,
    ConfirmPodcastView,
    PodcastCreatedView,
    PodcastDetailView,
    PromoListView,
    CreatePromoView,
    PromoCreatedView
)


urlpatterns = [
    path('podcasts/', PodcastListView.as_view(), name='user_podcast_list'),
    path('add/', CreatePodcastView.as_view(), name='create_podcast'),
    path('add/<path:token>/', ConfirmPodcastView.as_view(), name='confirm_podcast'),  # NOQA
    path('added/', PodcastCreatedView.as_view(), name='podcast_created'),
    path('@<int:apple_id>/', PodcastDetailView.as_view(), name='podcast_detail'),  # NOQA
    path('@<int:apple_id>/promos/', PromoListView.as_view(), name='podcast_promos'),  # NOQA
    path('@<int:apple_id>/promos/create/', CreatePromoView.as_view(), name='create_promo'),  # NOQA
    path('@<int:apple_id>/promos/created/', PromoCreatedView.as_view(), name='promo_created')  # NOQA
]
