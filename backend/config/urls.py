from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({'status': 'ok', 'version': '1.0.0'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health-check'),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/students/', include('students.urls')),
    path('api/v1/students/assessment/', include('riasec.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/counselors/', include('counselors.urls')),
    path('api/v1/parents/', include('parents.urls')),
    path('api/v1/school-admin/', include('school_admin.urls')),
    path('api/v1/system-admin/', include('system_admin.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/guidance/', include('guidance.urls')),
    path('api/v1/tertiary/', include('tertiary.urls')),
]

if 'devmail' in settings.INSTALLED_APPS:
    urlpatterns += [path('api/v1/dev/', include('devmail.urls'))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
