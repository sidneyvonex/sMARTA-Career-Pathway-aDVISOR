from django.urls import path
from .views import (
    CounselorStudentsView, CounselorStudentDetailView,
    CounselorStatsView, CounselorNotesView, CounselorNoteDetailView,
    CounselorInterventionsView, CounselorInterventionDetailView,
    CounselorPlanReviewView,
)

urlpatterns = [
    path('students/', CounselorStudentsView.as_view(), name='counselor-students'),
    path('students/<int:student_id>/', CounselorStudentDetailView.as_view(), name='counselor-student-detail'),
    path(
        'students/<int:student_id>/plan-review/',
        CounselorPlanReviewView.as_view(),
        name='counselor-student-plan-review',
    ),
    path('stats/', CounselorStatsView.as_view(), name='counselor-stats'),
    path('notes/', CounselorNotesView.as_view(), name='counselor-notes'),
    path('notes/<int:note_id>/', CounselorNoteDetailView.as_view(), name='counselor-note-detail'),
    path(
        'interventions/',
        CounselorInterventionsView.as_view(),
        name='counselor-interventions',
    ),
    path(
        'interventions/<int:intervention_id>/',
        CounselorInterventionDetailView.as_view(),
        name='counselor-intervention-detail',
    ),
]
