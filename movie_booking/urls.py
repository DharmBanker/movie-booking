"""
Root URL Configuration — Movie Booking Backend
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


@ensure_csrf_cookie
def csrf_token_view(request):
    """Returns CSRF token so the browser JS can include it in POST requests."""
    from django.middleware.csrf import get_token
    return JsonResponse({'csrfToken': get_token(request)})


urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # CSRF token endpoint for browser JS
    path('api/csrf/', csrf_token_view, name='csrf-token'),

    # Frontend pages
    path('', include('frontend.urls')),

    # API v1 Routes
    path('api/v1/', include('movies.urls', namespace='movies')),
    path('api/v1/', include('bookings.urls', namespace='bookings')),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
