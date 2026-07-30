import pytest
from django.contrib.auth import authenticate
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.management.commands.seed_pilot_demo import (
    DEMO_DOMAIN,
    DEMO_SCHOOL_PREFIX,
    DEMO_USERS,
)
from accounts.models import School, StudentProfile, User
from counselors.models import CounselorAssignment, CounselorIntervention
from guidance.models import LearnerCombinationChoice, LearnerPlan, SchoolOffering
from notifications.models import Notification
from parents.models import ParentStudentLink
from riasec.models import Recommendation, RIASECAssessment, RIASECScore
from students.models import CBCGrade
from system_admin.models import AuditLog


pytestmark = pytest.mark.django_db

TEST_PASSWORD = 'PilotDemo123!'


def run_seed():
    call_command('seed_pilot_demo', password=TEST_PASSWORD)


def demo_counts():
    profiles = StudentProfile.objects.filter(user__email__endswith=f'@{DEMO_DOMAIN}')
    return {
        'schools': School.objects.filter(school_code__startswith=DEMO_SCHOOL_PREFIX).count(),
        'users': User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}').count(),
        'profiles': profiles.count(),
        'offerings': SchoolOffering.objects.filter(
            school__school_code__startswith=DEMO_SCHOOL_PREFIX,
            is_active=True,
        ).count(),
        'grades': CBCGrade.objects.filter(
            student_subject__student_profile__in=profiles
        ).count(),
        'assessments': RIASECAssessment.objects.filter(
            student_profile__in=profiles
        ).count(),
        'recommendations': Recommendation.objects.filter(
            assessment__student_profile__in=profiles
        ).count(),
        'choices': LearnerCombinationChoice.objects.filter(
            student_profile__in=profiles
        ).count(),
        'plans': LearnerPlan.objects.filter(student_profile__in=profiles).count(),
        'notifications': Notification.objects.filter(
            user__email__endswith=f'@{DEMO_DOMAIN}'
        ).count(),
        'audits': AuditLog.objects.filter(details__source='pilot_demo_seed').count(),
    }


def test_seed_requires_an_explicit_password(monkeypatch):
    monkeypatch.delenv('PILOT_DEMO_PASSWORD', raising=False)
    with pytest.raises(CommandError, match='PILOT_DEMO_PASSWORD'):
        call_command('seed_pilot_demo')


def test_seed_creates_a_complete_five_county_demo():
    run_seed()

    schools = School.objects.filter(school_code__startswith=DEMO_SCHOOL_PREFIX)
    assert schools.count() == 5
    assert set(schools.values_list('county', flat=True)) == {
        'kiambu',
        'muranga',
        'nyeri',
        'kirinyaga',
        'nyandarua',
    }
    assert User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}').count() == len(
        DEMO_USERS
    )
    assert StudentProfile.objects.filter(
        user__email__endswith=f'@{DEMO_DOMAIN}'
    ).count() == 3

    for spec in DEMO_USERS.values():
        assert authenticate(email=spec['email'], password=TEST_PASSWORD) is not None

    assert SchoolOffering.objects.filter(
        school__in=schools,
        is_active=True,
    ).count() == 20
    assert CBCGrade.objects.filter(
        student_subject__student_profile__user__email__endswith=f'@{DEMO_DOMAIN}',
        verified_by__email=DEMO_USERS['school_admin']['email'],
    ).count() == 15
    assert RIASECAssessment.objects.filter(
        student_profile__user__email__endswith=f'@{DEMO_DOMAIN}'
    ).count() == 2
    assert RIASECScore.objects.filter(
        assessment__student_profile__user__email__endswith=f'@{DEMO_DOMAIN}'
    ).count() == 12
    assert Recommendation.objects.filter(
        assessment__student_profile__user__email__endswith=f'@{DEMO_DOMAIN}'
    ).exists()

    profiles = StudentProfile.objects.filter(user__email__endswith=f'@{DEMO_DOMAIN}')
    assert LearnerCombinationChoice.objects.filter(
        student_profile__in=profiles,
        status=LearnerCombinationChoice.STATUS_PROVISIONAL,
    ).count() == 2
    assert LearnerPlan.objects.filter(
        student_profile__in=profiles,
        review_status=LearnerPlan.STATUS_REVIEWED,
    ).count() == 1
    assert LearnerPlan.objects.filter(
        student_profile__in=profiles,
        review_status=LearnerPlan.STATUS_READY,
    ).count() == 1
    assert CounselorAssignment.objects.filter(
        student_profile__in=profiles,
        is_active=True,
    ).count() == 3
    assert CounselorIntervention.objects.filter(
        student__email=DEMO_USERS['learner_review']['email'],
        status=CounselorIntervention.STATUS_OPEN,
    ).exists()
    assert ParentStudentLink.objects.filter(
        parent__email=DEMO_USERS['parent']['email'],
        student__email=DEMO_USERS['learner_ready']['email'],
        status=ParentStudentLink.STATUS_ACTIVE,
    ).exists()
    assert Notification.objects.filter(
        user__email__endswith=f'@{DEMO_DOMAIN}'
    ).count() == 4
    assert AuditLog.objects.filter(details__source='pilot_demo_seed').count() == 4


def test_seed_is_idempotent():
    run_seed()
    first_counts = demo_counts()
    first_ids = {
        'schools': list(
            School.objects.filter(
                school_code__startswith=DEMO_SCHOOL_PREFIX
            ).order_by('school_code').values_list('pk', flat=True)
        ),
        'users': list(
            User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}')
            .order_by('email')
            .values_list('pk', flat=True)
        ),
        'assessments': list(
            RIASECAssessment.objects.filter(
                student_profile__user__email__endswith=f'@{DEMO_DOMAIN}'
            ).order_by('student_profile__user__email').values_list('pk', flat=True)
        ),
    }

    run_seed()

    assert demo_counts() == first_counts
    assert list(
        School.objects.filter(
            school_code__startswith=DEMO_SCHOOL_PREFIX
        ).order_by('school_code').values_list('pk', flat=True)
    ) == first_ids['schools']
    assert list(
        User.objects.filter(email__endswith=f'@{DEMO_DOMAIN}')
        .order_by('email')
        .values_list('pk', flat=True)
    ) == first_ids['users']
    assert list(
        RIASECAssessment.objects.filter(
            student_profile__user__email__endswith=f'@{DEMO_DOMAIN}'
        ).order_by('student_profile__user__email').values_list('pk', flat=True)
    ) == first_ids['assessments']
