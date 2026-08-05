from django.urls import path
from . import views
from .marks import SchoolAcademicPeriodListView, SchoolMarksImportView

urlpatterns = [
    path(
        'academic-periods/',
        SchoolAcademicPeriodListView.as_view(),
        name='school-admin-academic-periods',
    ),
    path(
        'marks/import/',
        SchoolMarksImportView.as_view(),
        name='school-admin-marks-import',
    ),
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
    path('counselors/<int:counselor_id>/reset-password/', views.CounselorPasswordResetView.as_view(), name='school-admin-counselor-reset-password'),
    path('students/<int:student_id>/reset-password/', views.StudentPasswordResetView.as_view(), name='school-admin-student-reset-password'),
    path('students/', views.SchoolStudentsView.as_view(), name='school-admin-students'),
    path(
        'students/import/',
        views.SchoolStudentImportView.as_view(),
        name='school-admin-student-import',
    ),
    path(
        'membership-requests/',
        views.SchoolMembershipRequestsView.as_view(),
        name='school-admin-membership-requests',
    ),
    path(
        'membership-requests/<int:student_id>/decision/',
        views.SchoolMembershipDecisionView.as_view(),
        name='school-admin-membership-decision',
    ),
    path('stats/', views.SchoolStatsView.as_view(), name='school-admin-stats'),
    path('assignments/', views.SchoolAssignmentView.as_view(), name='school-admin-assignment'),
    path(
        'assignments/bulk/',
        views.SchoolBulkAssignmentView.as_view(),
        name='school-admin-bulk-assignment',
    ),
    path('assignments/<int:assignment_id>/remove/', views.SchoolAssignmentRemoveView.as_view(), name='school-admin-assignment-remove'),
]
