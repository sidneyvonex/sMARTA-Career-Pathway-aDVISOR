from django.urls import path
from . import views

urlpatterns = [
    path('student/<int:student_id>/pdf/', views.StudentReportView.as_view(), name='student-report-pdf'),
]
