from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.auth.views import LoginView
from .auth import EmailAuthenticationForm


urlpatterns = [
    path('admin/rq/', include('django_rq.urls')),
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(authentication_form=EmailAuthenticationForm), name='login'),  # NOQA
    path('~/email/', include('podrings.mail.urls')),
    path('', include('podrings.creative.urls')),
    path('', include('podrings.community.urls')),
    path('', include('podrings.front.urls'))
]


if settings.DEBUG:
    from django.views.static import serve as static_serve

    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            static_serve,
            {
                'document_root': settings.MEDIA_ROOT
            }
        )
    ]
