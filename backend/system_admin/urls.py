from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='system-admin-dashboard'),
    path('schools/', views.SchoolListView.as_view(), name='system-admin-schools'),
    path('schools/<int:school_id>/', views.SchoolDetailView.as_view(), name='system-admin-school-detail'),
    path('schools/<int:school_id>/deactivate/', views.SchoolDeactivateView.as_view(), name='system-admin-school-deactivate'),
    path('schools/<int:school_id>/activate/', views.SchoolActivateView.as_view(), name='system-admin-school-activate'),
]
