from django.urls import path
from .views import (
    CreateUserView,
    UserCreatedView,
    ConfirmEmailView,
    LogoutView,
    RingListView,
    SuggestionListView,
    CreateRingView,
    RingDetailView,
    JoinRingView,
    UpdateRingView,
    JoinRequestListView,
    JoinRequestDetailView,
    AcceptRequestView,
    DeleteRequestView,
    ShareRingView,
    RingQRCodeView,
    DeleteRingView,
    CreateCommitmentView,
    CommitmentDetailView
)


urlpatterns = [
    path('signup/', CreateUserView.as_view(), name='create_user'),
    path('signup/confirm/', UserCreatedView.as_view(), name='user_created'),
    path('signup/confirm/<path:token>/', ConfirmEmailView.as_view(), name='confirm_user_email'),  # NOQA
    path('logout/', LogoutView.as_view(), name='logout'),
    path('explore/', RingListView.as_view(), name='ring_list'),
    path('dashboard/', SuggestionListView.as_view(), name='suggestion_list'),
    path('start/', CreateRingView.as_view(), name='create_ring'),
    path('@<slug:slug>/', RingDetailView.as_view(), name='ring_detail'),
    path('@<slug:slug>/add/<int:apple_id>/', JoinRingView.as_view(), name='join_ring'),  # NOQA
    path('@<slug:slug>/edit/', UpdateRingView.as_view(), name='update_ring'),
    path('@<slug:slug>/requests/', JoinRequestListView.as_view(), name='join_requests'),  # NOQA
    path('@<slug:slug>/requests/<uuid:pk>/', JoinRequestDetailView.as_view(), name='join_request_detail'),  # NOQA
    path('@<slug:slug>/requests/<uuid:pk>/accept/', AcceptRequestView.as_view(), name='accept_join_request'),  # NOQA
    path('@<slug:slug>/requests/<uuid:pk>/delete/', DeleteRequestView.as_view(), name='delete_join_request'),  # NOQA
    path('@<slug:slug>/share/', ShareRingView.as_view(), name='share_ring'),
    path('@<slug:slug>/qr/', RingQRCodeView.as_view(), name='ring_qrcode'),
    path('@<slug:slug>/delete/', DeleteRingView.as_view(), name='delete_ring'),
    path('@<int:apple_id>/promos/<uuid:promo_id>/commitments/create/', CreateCommitmentView.as_view(), name='create_commitment'),  # NOQA
    path('@<int:apple_id>/promos/<uuid:promo_id>/commitments/<uuid:pk>/', CommitmentDetailView.as_view(), name='commitment_detail')  # NOQA
]
