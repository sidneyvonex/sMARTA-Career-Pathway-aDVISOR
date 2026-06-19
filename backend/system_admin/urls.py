from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='system-admin-dashboard'),
    path('schools/', views.SchoolListView.as_view(), name='system-admin-schools'),
    path('schools/<int:school_id>/', views.SchoolDetailView.as_view(), name='system-admin-school-detail'),
    path('schools/<int:school_id>/deactivate/', views.SchoolDeactivateView.as_view(), name='system-admin-school-deactivate'),
    path('schools/<int:school_id>/activate/', views.SchoolActivateView.as_view(), name='system-admin-school-activate'),
    path('users/', views.UserListView.as_view(), name='system-admin-users'),
    path('users/<int:user_id>/', views.UserDetailView.as_view(), name='system-admin-user-detail'),
    path('users/<int:user_id>/deactivate/', views.UserDeactivateView.as_view(), name='system-admin-user-deactivate'),
    path('users/<int:user_id>/activate/', views.UserActivateView.as_view(), name='system-admin-user-activate'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='system-admin-audit-logs'),
]
