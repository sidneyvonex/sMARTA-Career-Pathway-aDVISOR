from django.urls import path
from . import views

urlpatterns = [
    path('school/', views.SchoolProfileView.as_view(), name='school-admin-profile'),
    path('school/logo/', views.SchoolLogoUploadView.as_view(), name='school-admin-logo'),
    path('counselors/', views.SchoolCounselorsView.as_view(), name='school-admin-counselors'),
    path('counselors/add/', views.SchoolCounselorAddView.as_view(), name='school-admin-counselor-add'),
    path('counselors/<int:counselor_id>/remove/', views.SchoolCounselorRemoveView.as_view(), name='school-admin-counselor-remove'),
]
