from django.urls import path
from .views import (
    CounselorStudentsView, CounselorStudentDetailView,
    CounselorStatsView, CounselorNotesView, CounselorNoteDetailView,
)

urlpatterns = [
    path('students/', CounselorStudentsView.as_view(), name='counselor-students'),
    path('students/<int:student_id>/', CounselorStudentDetailView.as_view(), name='counselor-student-detail'),
    path('stats/', CounselorStatsView.as_view(), name='counselor-stats'),
    path('notes/', CounselorNotesView.as_view(), name='counselor-notes'),
    path('notes/<int:note_id>/', CounselorNoteDetailView.as_view(), name='counselor-note-detail'),
]
