from django.urls import path
from tertiary.views import EducationGoalDetailView, EducationGoalListCreateView
from .views import (
    AcademicGoalConfirmAchievementView,
    AcademicGoalDetailView,
    AcademicGoalListCreateView,
    StudentProfileView, PhotoUploadView, SubjectListView,
    MySubjectListView, MySubjectRemoveView,
    CBCGradeListView, CBCGradeDetailView, ProgressAssessmentView,
    StudentCounselorView, StudentDashboardView, EvidenceSummaryView, GradeSummaryView,
    StudentInterventionsView,
    StudentSchoolMembershipListCreateView,
    LearnerCombinationChoiceDetailView,
    LearnerCombinationChoiceListCreateView,
    LearnerCombinationChoiceProvisionalView,
    LearnerPlanView,
    PlanMilestoneDetailView,
    PlanMilestoneListCreateView,
)
from parents.views import (
    StudentParentAccessApproveView,
    StudentParentAccessListView,
    StudentParentAccessRevokeView,
)
from .period_views import AcademicPeriodListView

urlpatterns = [
    path(
        'academic-periods/',
        AcademicPeriodListView.as_view(),
        name='student-academic-period-list',
    ),
    path(
        'education-goals/',
        EducationGoalListCreateView.as_view(),
        name='education-goal-list',
    ),
    path(
        'education-goals/<int:goal_id>/',
        EducationGoalDetailView.as_view(),
        name='education-goal-detail',
    ),
    path(
        'school-memberships/',
        StudentSchoolMembershipListCreateView.as_view(),
        name='student-school-memberships',
    ),
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path(
        'parent-access/',
        StudentParentAccessListView.as_view(),
        name='student-parent-access-list',
    ),
    path(
        'parent-access/<int:link_id>/approve/',
        StudentParentAccessApproveView.as_view(),
        name='student-parent-access-approve',
    ),
    path(
        'parent-access/<int:link_id>/revoke/',
        StudentParentAccessRevokeView.as_view(),
        name='student-parent-access-revoke',
    ),
    path('evidence-summary/', EvidenceSummaryView.as_view(), name='student-evidence-summary'),
    path(
        'interventions/',
        StudentInterventionsView.as_view(),
        name='student-interventions',
    ),
    path('grades/summary/', GradeSummaryView.as_view(), name='student-grade-summary'),
    path('progress/', ProgressAssessmentView.as_view(), name='student-progress'),
    path(
        'academic-goals/',
        AcademicGoalListCreateView.as_view(),
        name='academic-goal-list',
    ),
    path(
        'academic-goals/<int:goal_id>/',
        AcademicGoalDetailView.as_view(),
        name='academic-goal-detail',
    ),
    path(
        'academic-goals/<int:goal_id>/confirm-achievement/',
        AcademicGoalConfirmAchievementView.as_view(),
        name='academic-goal-confirm-achievement',
    ),
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
    path('plan/', LearnerPlanView.as_view(), name='learner-plan'),
    path(
        'plan/milestones/',
        PlanMilestoneListCreateView.as_view(),
        name='plan-milestone-list',
    ),
    path(
        'plan/milestones/<int:milestone_id>/',
        PlanMilestoneDetailView.as_view(),
        name='plan-milestone-detail',
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
