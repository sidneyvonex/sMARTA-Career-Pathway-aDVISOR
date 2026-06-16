from django.urls import path
from .views import (
    StudentProfileView, PhotoUploadView, SubjectListView,
    MySubjectListView, MySubjectRemoveView,
    CBCGradeListView, CBCGradeDetailView,
    StudentCounselorView,
)

urlpatterns = [
    path('profile/', StudentProfileView.as_view(), name='student-profile'),
    path('profile/photo/', PhotoUploadView.as_view(), name='student-photo'),
    path('subjects/', SubjectListView.as_view(), name='subject-list'),
    path('my-subjects/', MySubjectListView.as_view(), name='my-subject-list'),
    path('my-subjects/<int:pk>/remove/', MySubjectRemoveView.as_view(), name='my-subject-remove'),
    path('my-subjects/<int:subject_pk>/grades/', CBCGradeListView.as_view(), name='cbc-grade-list'),
    path(
        'my-subjects/<int:subject_pk>/grades/<int:grade_pk>/',
        CBCGradeDetailView.as_view(),
        name='cbc-grade-detail',
    ),
    path('counselor/', StudentCounselorView.as_view(), name='student-counselor'),
]
