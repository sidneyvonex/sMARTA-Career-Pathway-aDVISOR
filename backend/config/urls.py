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
]
