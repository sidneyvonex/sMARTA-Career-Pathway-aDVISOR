from django.urls import path
from .views import (
    StudentProfileView, PhotoUploadView, SubjectListView,
    MySubjectListView, MySubjectRemoveView,
    CBCGradeListView, CBCGradeDetailView,
    StudentCounselorView, EvidenceSummaryView, GradeSummaryView,
    LearnerCombinationChoiceDetailView,
    LearnerCombinationChoiceListCreateView,
    LearnerCombinationChoiceProvisionalView,
)

urlpatterns = [
    path('evidence-summary/', EvidenceSummaryView.as_view(), name='student-evidence-summary'),
    path('grades/summary/', GradeSummaryView.as_view(), name='student-grade-summary'),
    path(
        'combination-choices/',
        LearnerCombinationChoiceListCreateView.as_view(),
        name='learner-combination-choice-list',
    ),
    path(
        'combination-choices/<int:choice_id>/',
        LearnerCombinationChoiceDetailView.as_view(),
        name='learner-combination-choice-detail',
    ),
    path(
        'combination-choices/<int:choice_id>/provisional/',
        LearnerCombinationChoiceProvisionalView.as_view(),
        name='learner-combination-choice-provisional',
    ),
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
