from django.urls import path
from . import views

urlpatterns = [
    path('student/<int:student_id>/pdf/', views.StudentReportView.as_view(), name='student-report-pdf'),
    path('school/overview/pdf/', views.SchoolOverviewReportView.as_view(), name='school-overview-report-pdf'),
    path('school/roster/pdf/', views.SchoolRosterReportView.as_view(), name='school-roster-report-pdf'),
    path('counselor/overview/pdf/', views.CounselorOverviewReportView.as_view(), name='counselor-overview-report-pdf'),
    path('counselor/roster/pdf/', views.CounselorRosterReportView.as_view(), name='counselor-roster-report-pdf'),
    path('system/overview/pdf/', views.PlatformOverviewReportView.as_view(), name='system-overview-report-pdf'),
    path('system/schools/pdf/', views.SchoolsDirectoryReportView.as_view(), name='system-schools-report-pdf'),
]
