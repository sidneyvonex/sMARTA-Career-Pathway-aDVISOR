from django.urls import path
from . import views

urlpatterns = [
    path('offerings/', views.SchoolOfferingsView.as_view(), name='school-admin-offerings'),
    path(
        'students/<int:student_id>/grades/<int:grade_id>/verification/',
        views.SchoolGradeVerificationView.as_view(),
        name='school-admin-grade-verification',
    ),
    path('school/', views.SchoolProfileView.as_view(), name='school-admin-profile'),
    path('school/logo/', views.SchoolLogoUploadView.as_view(), name='school-admin-logo'),
    path('school/logo/remove/', views.SchoolLogoRemoveView.as_view(), name='school-admin-logo-remove'),
    path('counselors/', views.SchoolCounselorsView.as_view(), name='school-admin-counselors'),
    path('counselors/add/', views.SchoolCounselorAddView.as_view(), name='school-admin-counselor-add'),
    path('counselors/<int:counselor_id>/remove/', views.SchoolCounselorRemoveView.as_view(), name='school-admin-counselor-remove'),
    path('students/', views.SchoolStudentsView.as_view(), name='school-admin-students'),
    path('stats/', views.SchoolStatsView.as_view(), name='school-admin-stats'),
    path('assignments/', views.SchoolAssignmentView.as_view(), name='school-admin-assignment'),
    path('assignments/<int:assignment_id>/remove/', views.SchoolAssignmentRemoveView.as_view(), name='school-admin-assignment-remove'),
]
