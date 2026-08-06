import pytest
from rest_framework.test import APIClient

from accounts.models import StudentSchoolMembership
from counselors.models import CounselorAssignment, CounselorIntervention
from notifications.models import Notification
from students.models import AcademicGoal, CBCGrade, Subject
from system_admin.models import AuditLog
from tertiary.models import LearnerEducationGoal
from tests.factories import (
    AcademicPeriodFactory,
    CounselorAssignmentFactory,
    CounselorFactory,
    InstitutionFactory,
    ProgrammeFactory,
    SchoolAdminFactory,
    SchoolFactory,
    StudentProfileFactory,
    StudentSchoolMembershipFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db


def test_seeded_grade_10_support_journey_survives_school_transfer():
    """Catches transfer approval dropping support history or former-school access."""
    AcademicPeriodFactory(year=2026, term=1)
    AcademicPeriodFactory(year=2026, term=2)
    old_school = SchoolFactory(name='Mwangaza Senior School')
    new_school = SchoolFactory(name='Tumaini Senior School')
    learner = StudentProfileFactory(
        user=VerifiedUserFactory(
            role='student',
            first_name='Amani',
            last_name='Otieno',
        ),
        grade=10,
        mode='school_linked',
        school=old_school,
        school_membership_status='active',
    )
    old_membership = StudentSchoolMembershipFactory(
        student_profile=learner,
        school=old_school,
        status=StudentSchoolMembership.STATUS_ACTIVE,
    )
    counselor = CounselorFactory(school=old_school)
    old_assignment = CounselorAssignmentFactory(
        counselor=counselor,
        student_profile=learner,
        school=old_school,
    )
    institution = InstitutionFactory(name='Sourced Technical University')
    programme = ProgrammeFactory(
        institution=institution,
        name='Bachelor of Science in Data Science',
    )

    learner_client = APIClient()
    learner_client.force_authenticate(learner.user)
    subject = Subject.objects.get(code='CMT10')
    enrolled = learner_client.post(
        '/api/v1/students/my-subjects/',
        {'subject_id': subject.id},
        format='json',
    )
    assert enrolled.status_code == 201
    enrollment_id = enrolled.data['data']['id']

    evidence_ids = []
    for term, level in ((1, 'AE1'), (2, 'AE2')):
        recorded = learner_client.post(
            f'/api/v1/students/my-subjects/{enrollment_id}/grades/',
            {'term': term, 'year': 2026, 'level': level},
            format='json',
        )
        assert recorded.status_code == 201
        evidence_ids.append(recorded.data['data']['id'])

    progress = learner_client.get('/api/v1/students/progress/')
    assert progress.status_code == 200
    subject_progress = progress.data['data']['subjects'][0]
    assert subject_progress['continuity_code'] == 'CMT'
    assert subject_progress['status'] == 'support'
    assert subject_progress['rule_code'] == 'two_ae_be_support'
    assert subject_progress['explanation'] == (
        'The two latest academic evidence records are approaching or below '
        'expectation.'
    )
    assert [row['id'] for row in subject_progress['records_used']] == evidence_ids

    academic_goal = learner_client.post(
        '/api/v1/students/academic-goals/',
        {
            'continuity_code': 'CMT',
            'target_level': 'ME2',
            'target_term': 3,
            'target_year': 2026,
            'target_academic_grade': 10,
            'action_plan': (
                'Attend weekly mathematics support and review marked work.'
            ),
        },
        format='json',
    )
    assert academic_goal.status_code == 201
    academic_goal_id = academic_goal.data['data']['id']
    assert academic_goal.data['data']['current_evidence'] == evidence_ids[-1]
    assert academic_goal.data['data']['target_level']['code'] == 'ME2'

    education_goal = learner_client.post(
        '/api/v1/students/education-goals/',
        {
            'institution': institution.id,
            'programme': programme.id,
            'kind': 'primary',
            'priority': 1,
        },
        format='json',
    )
    assert education_goal.status_code == 201
    education_goal_id = education_goal.data['data']['id']
    assert education_goal.data['data']['institution']['source_url'] == (
        institution.source_url
    )
    assert education_goal.data['data']['programme']['source_url'] == (
        programme.source_url
    )
    assert education_goal.data['data']['programme']['verification_status'] == (
        'historical'
    )

    counselor_client = APIClient()
    counselor_client.force_authenticate(counselor)
    intervention = counselor_client.post(
        '/api/v1/counselors/interventions/',
        {
            'student_id': learner.user_id,
            'category': 'academic_evidence',
            'action_agreed': (
                'Review both mathematics records and practise twice each week.'
            ),
            'learner_visible': True,
            'parent_visible': False,
        },
        format='json',
    )
    assert intervention.status_code == 201
    intervention_id = intervention.data['data']['id']
    assert intervention.data['data']['learner_visible'] is True

    transfer_request = learner_client.post(
        '/api/v1/students/school-memberships/',
        {'school_code': new_school.school_code},
        format='json',
    )
    assert transfer_request.status_code == 201
    new_membership_id = transfer_request.data['data']['id']
    assert transfer_request.data['data']['status'] == 'pending'

    new_school_admin = SchoolAdminFactory(school=new_school)
    admin_client = APIClient()
    admin_client.force_authenticate(new_school_admin)
    approved = admin_client.put(
        (
            '/api/v1/school-admin/membership-requests/'
            f'{learner.user_id}/decision/'
        ),
        {'decision': 'approve'},
        format='json',
    )
    assert approved.status_code == 200
    assert approved.data['data']['school_membership_status'] == 'active'

    old_membership.refresh_from_db()
    old_assignment.refresh_from_db()
    learner.refresh_from_db()
    new_membership = StudentSchoolMembership.objects.get(pk=new_membership_id)
    assert old_membership.status == StudentSchoolMembership.STATUS_ENDED
    assert old_membership.ended_at is not None
    assert old_assignment.is_active is False
    assert new_membership.status == StudentSchoolMembership.STATUS_ACTIVE
    assert new_membership.decided_by == new_school_admin
    assert learner.school == new_school
    assert learner.school_membership_status == 'active'
    assert list(
        StudentSchoolMembership.objects.filter(
            student_profile=learner,
            status=StudentSchoolMembership.STATUS_ACTIVE,
        ).values_list('school_id', flat=True)
    ) == [new_school.id]
    assert CounselorAssignment.objects.filter(
        pk=old_assignment.pk,
        is_active=False,
    ).exists()

    assert CBCGrade.objects.filter(pk__in=evidence_ids).count() == 2
    assert AcademicGoal.objects.filter(
        pk=academic_goal_id,
        current_evidence_id=evidence_ids[-1],
        learner=learner,
    ).exists()
    assert LearnerEducationGoal.objects.filter(
        pk=education_goal_id,
        learner=learner,
        institution=institution,
        programme=programme,
    ).exists()
    assert CounselorIntervention.objects.filter(
        pk=intervention_id,
        counselor=counselor,
        student=learner.user,
        category=CounselorIntervention.CATEGORY_ACADEMIC_EVIDENCE,
        learner_visible=True,
    ).exists()

    progress_after_transfer = learner_client.get('/api/v1/students/progress/')
    assert progress_after_transfer.status_code == 200
    assert progress_after_transfer.data['data']['subjects'][0]['rule_code'] == (
        'two_ae_be_support'
    )
    assert [
        row['id']
        for row in progress_after_transfer.data['data']['subjects'][0][
            'records_used'
        ]
    ] == evidence_ids
    academic_goals_after_transfer = learner_client.get(
        '/api/v1/students/academic-goals/'
    )
    assert academic_goals_after_transfer.status_code == 200
    assert [
        row['id'] for row in academic_goals_after_transfer.data['data']
    ] == [academic_goal_id]
    education_goals_after_transfer = learner_client.get(
        '/api/v1/students/education-goals/'
    )
    assert education_goals_after_transfer.status_code == 200
    assert [
        row['id'] for row in education_goals_after_transfer.data['data']
    ] == [education_goal_id]
    interventions_after_transfer = learner_client.get(
        '/api/v1/students/interventions/'
    )
    assert interventions_after_transfer.status_code == 200
    assert [
        row['id'] for row in interventions_after_transfer.data['data']
    ] == [intervention_id]
    assert interventions_after_transfer.data['data'][0]['learner_visible'] is True

    notifications = Notification.objects.filter(user=learner.user)
    assert set(notifications.values_list('type', flat=True)) == {
        'counselor_intervention',
        'school_transfer_decided',
    }
    assert notifications.count() == 2
    assert notifications.get(type='school_transfer_decided').message == (
        f'Your school link to {new_school.name} is now active.'
    )
    audit = AuditLog.objects.get(
        action='school_membership_approved',
        target_id=learner.user_id,
    )
    assert audit.actor == new_school_admin
    assert audit.details == {
        'school_id': new_school.id,
        'school_name': new_school.name,
        'decision': 'approve',
        'membership_id': new_membership.id,
        'previous_school_id': old_school.id,
    }
