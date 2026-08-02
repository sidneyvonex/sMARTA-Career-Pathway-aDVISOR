import pytest
from rest_framework.test import APIClient
from tests.factories import (
    AcademicGoalFactory, LearnerEducationGoalFactory,
    ParentFactory, VerifiedUserFactory, StudentProfileFactory,
    ParentStudentLinkFactory, CounselorAssignmentFactory,
    RIASECAssessmentFactory, StudentSubjectFactory,
    SubjectFactory, CBCGradeFactory, CounselorFactory,
    CounselorNoteFactory,
)
from riasec.models import RIASECScore, Recommendation, Pathway
from notifications.models import Notification
from guidance.models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    LearnerPlan,
    PlanMilestone,
    SubjectCombination,
)

pytestmark = pytest.mark.django_db


class TestParentChildrenView:
    URL = '/api/v1/parents/children/'

    def setup_method(self):
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(self.URL)
        assert resp.status_code == 401

    def test_non_parent_returns_403(self):
        user = VerifiedUserFactory(role='student')
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.URL)
        assert resp.status_code == 403

    def test_parent_no_children_returns_empty(self):
        parent = ParentFactory()
        self.client.force_authenticate(user=parent)
        resp = self.client.get(self.URL)
        assert resp.status_code == 200
        assert resp.json()['data'] == []

    def test_parent_with_one_child(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student', first_name='Tom',
                                      last_name='Doe', county='kiambu')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()['data']
        assert len(data) == 1
        child = data[0]
        assert child['first_name'] == 'Tom'
        assert child['last_name'] == 'Doe'
        assert child['grade'] == 9
        assert child['quiz_status'] == 'pending'
        assert child['subject_count'] == 0
        assert child['counselor_assigned'] is False

    def test_pending_child_is_not_visible(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(
            parent=parent,
            student=student,
            status='pending_learner',
        )
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)

        assert resp.status_code == 200
        assert resp.json()['data'] == []

    def test_parent_with_multiple_children(self):
        parent = ParentFactory()
        s1 = VerifiedUserFactory(role='student')
        s2 = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=s1, grade=9)
        StudentProfileFactory(user=s2, grade=10)
        ParentStudentLinkFactory(parent=parent, student=s1)
        ParentStudentLinkFactory(parent=parent, student=s2)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)
        assert resp.status_code == 200
        assert len(resp.json()['data']) == 2

    def test_child_with_assessment_shows_done(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        RIASECAssessmentFactory(student_profile=profile)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)
        child = resp.json()['data'][0]
        assert child['quiz_status'] == 'done'

    def test_child_with_subjects_shows_count(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        StudentSubjectFactory(student_profile=profile)
        StudentSubjectFactory(student_profile=profile)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)
        child = resp.json()['data'][0]
        assert child['subject_count'] == 2

    def test_child_with_counselor_shows_assigned(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        CounselorAssignmentFactory(student_profile=profile, is_active=True)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)
        child = resp.json()['data'][0]
        assert child['counselor_assigned'] is True

    def test_child_summary_includes_next_action_and_access_status(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)

        child = resp.json()['data'][0]
        assert child['access_status'] == 'active'
        assert child['next_action']['code'] == 'complete_profile'
        assert child['provisional_combination'] is None
        assert child['plan_status'] == 'not_started'
        assert child['plan_progress'] == {'completed': 0, 'total': 0}
        assert child['upcoming_milestone'] is None
        assert child['conversation_prompt']

    def test_child_summary_includes_provisional_plan_and_upcoming_milestone(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(
            user=student,
            grade=9,
            bio='Interested in practical science.',
            date_of_birth='2011-01-10',
            career_interests='Agriculture',
        )
        combination = SubjectCombination.objects.filter(
            framework_version=FrameworkVersion.objects.current(),
        ).first()
        choice = LearnerCombinationChoice.objects.create(
            student_profile=profile,
            combination=combination,
            status=LearnerCombinationChoice.STATUS_PROVISIONAL,
        )
        plan = LearnerPlan.objects.create(
            student_profile=profile,
            provisional_choice=choice,
        )
        PlanMilestone.objects.create(
            plan=plan,
            title='Review two pilot schools',
            due_date='2026-09-15',
            position=1,
        )
        PlanMilestone.objects.create(
            plan=plan,
            title='Complete interest conversation',
            is_complete=True,
            position=0,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self.URL)

        child = resp.json()['data'][0]
        assert child['provisional_combination']['code'] == combination.code
        assert child['plan_status'] == 'draft'
        assert child['plan_progress'] == {'completed': 1, 'total': 2}
        assert child['upcoming_milestone'] == {
            'id': child['upcoming_milestone']['id'],
            'title': 'Review two pilot schools',
            'due_date': '2026-09-15',
        }


class TestParentChildDetailView:
    def _url(self, student_id):
        return f'/api/v1/parents/children/{student_id}/'

    def setup_method(self):
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        resp = self.client.get(self._url(1))
        assert resp.status_code == 401

    def test_non_parent_returns_403(self):
        user = VerifiedUserFactory(role='student')
        self.client.force_authenticate(user=user)
        resp = self.client.get(self._url(1))
        assert resp.status_code == 403

    def test_unlinked_child_returns_404(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        self.client.force_authenticate(user=parent)
        resp = self.client.get(self._url(student.id))
        assert resp.status_code == 404

    def test_linked_child_returns_profile(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student', first_name='Tom', last_name='Doe')
        StudentProfileFactory(user=student, grade=9, bio='Loves math')
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        assert resp.status_code == 200
        data = resp.json()['data']
        assert data['profile']['first_name'] == 'Tom'
        assert data['profile']['grade'] == 9
        assert data['profile']['bio'] == 'Loves math'

    def test_pending_link_cannot_open_child_detail(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(
            parent=parent,
            student=student,
            status='pending_learner',
        )
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))

        assert resp.status_code == 404

    def test_linked_child_returns_subjects_with_grades(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        subj = SubjectFactory(name='Mathematics', grade=9)
        ss = StudentSubjectFactory(student_profile=profile, subject=subj)
        CBCGradeFactory(student_subject=ss, term=1, year=2026, level='ME1')
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        data = resp.json()['data']
        assert len(data['subjects']) == 1
        assert data['subjects'][0]['name'] == 'Mathematics'
        assert len(data['subjects'][0]['grades']) == 1
        assert data['subjects'][0]['grades'][0]['level'] == 'ME1'

    def test_linked_child_returns_assessment(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        assessment = RIASECAssessmentFactory(student_profile=profile)
        RIASECScore.objects.create(assessment=assessment, dimension='R', raw_score=25)
        RIASECScore.objects.create(assessment=assessment, dimension='I', raw_score=20)
        RIASECScore.objects.create(assessment=assessment, dimension='A', raw_score=15)
        RIASECScore.objects.create(assessment=assessment, dimension='S', raw_score=10)
        RIASECScore.objects.create(assessment=assessment, dimension='E', raw_score=12)
        RIASECScore.objects.create(assessment=assessment, dimension='C', raw_score=8)
        pathway = Pathway.objects.create(
            name='Engineering', description='Build things',
            weight_r=5, weight_i=4, weight_a=1, weight_s=1, weight_e=2, weight_c=3,
        )
        Recommendation.objects.create(
            assessment=assessment, pathway=pathway, rank=1, fit_score=80, fit_pct=90,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        data = resp.json()['data']
        assert data['assessment'] is not None
        assert data['assessment']['scores']['R'] == 25
        assert len(data['assessment']['recommendations']) == 1
        assert data['assessment']['recommendations'][0]['pathway']['name'] == 'Engineering'
        assert 'fit_pct' not in data['assessment']['recommendations'][0]
        assert 'fit_score' not in data['assessment']['recommendations'][0]

    def test_linked_child_no_assessment_returns_null(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        data = resp.json()['data']
        assert data['assessment'] is None

    def test_linked_child_returns_counselor_info(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        counselor = CounselorFactory(first_name='Dr', last_name='Smith')
        CounselorAssignmentFactory(
            counselor=counselor, student_profile=profile, is_active=True,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        data = resp.json()['data']
        assert data['counselor']['first_name'] == 'Dr'
        assert data['counselor']['last_name'] == 'Smith'

    def test_no_counselor_returns_null(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        data = resp.json()['data']
        assert data['counselor'] is None

    def test_detail_includes_academic_readiness_provisional_choice_and_plan(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        for index in range(3):
            enrollment = StudentSubjectFactory(
                student_profile=profile,
                subject=SubjectFactory(code=f'PAR{index}9', grade=9),
            )
            CBCGradeFactory(student_subject=enrollment)
        combination = SubjectCombination.objects.filter(
            framework_version=FrameworkVersion.objects.current(),
        ).first()
        choice = LearnerCombinationChoice.objects.create(
            student_profile=profile,
            combination=combination,
            status=LearnerCombinationChoice.STATUS_PROVISIONAL,
        )
        plan = LearnerPlan.objects.create(
            student_profile=profile,
            provisional_choice=choice,
            learner_reason='I want to explore practical science.',
        )
        PlanMilestone.objects.create(
            plan=plan,
            title='Visit a pilot school',
            due_date='2026-10-01',
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))

        data = resp.json()['data']
        assert data['academic_readiness']['status'] == 'ready'
        assert data['academic_readiness']['subjects_with_evidence'] == 3
        assert data['provisional_combination']['code'] == combination.code
        assert len(data['provisional_combination']['subjects']) == 3
        assert data['plan']['status'] == 'draft'
        assert data['plan']['learner_reason'] == (
            'I want to explore practical science.'
        )
        assert data['plan']['milestones'][0]['title'] == 'Visit a pilot school'

    def test_active_parent_sees_learner_progress_and_goals_without_private_notes(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        enrollment = StudentSubjectFactory(
            student_profile=profile,
            subject=SubjectFactory(code='PARPROG9', grade=9),
        )
        evidence = CBCGradeFactory(
            student_subject=enrollment,
            term=1,
            year=2026,
            level='ME2',
        )
        academic_goal = AcademicGoalFactory(
            learner=profile,
            current_evidence=evidence,
            target_academic_grade=9,
        )
        education_goal = LearnerEducationGoalFactory(learner=profile)
        counselor = CounselorFactory()
        CounselorAssignmentFactory(counselor=counselor, student_profile=profile)
        CounselorNoteFactory(
            counselor=counselor,
            student=student,
            body='Safeguarding note for counsellor only.',
            visible_to_parent=False,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        response = self.client.get(self._url(student.id))

        assert response.status_code == 200
        data = response.json()['data']
        assert data['academic_progress']['subjects'][0]['rule_code'] == (
            'one_non_be_insufficient'
        )
        assert data['academic_progress']['subjects'][0]['records_used'][0]['id'] == evidence.id
        assert data['academic_goals'][0]['id'] == academic_goal.id
        assert data['education_goals'][0]['id'] == education_goal.id
        assert data['parent_visible_notes'] == []
        assert 'Safeguarding note' not in str(data)


class TestRIASECParentNotification:
    def setup_method(self):
        self.client = APIClient()

    def _all_responses(self, score=3):
        """Build a valid 30-response payload using seeded question IDs."""
        from riasec.models import RIASECQuestion
        return [{'question_id': q.id, 'score': score} for q in RIASECQuestion.objects.all()]

    def test_parent_notified_on_child_assessment(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(parent=parent, student=student)

        self.client.force_authenticate(user=student)
        resp = self.client.post('/api/v1/students/assessment/', {
            'responses': self._all_responses(4),
        }, format='json')
        assert resp.status_code == 201

        notifs = Notification.objects.filter(
            user=parent, type='child_assessment_complete',
        )
        assert notifs.count() == 1
        assert student.first_name in notifs.first().message

    def test_no_parent_no_notification(self):
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)

        self.client.force_authenticate(user=student)
        resp = self.client.post('/api/v1/students/assessment/', {
            'responses': self._all_responses(3),
        }, format='json')
        assert resp.status_code == 201
        assert Notification.objects.filter(type='child_assessment_complete').count() == 0

    def test_pending_parent_is_not_notified(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        ParentStudentLinkFactory(
            parent=parent,
            student=student,
            status='pending_learner',
        )
        self.client.force_authenticate(user=student)

        resp = self.client.post('/api/v1/students/assessment/', {
            'responses': self._all_responses(3),
        }, format='json')

        assert resp.status_code == 201
        assert not Notification.objects.filter(
            user=parent,
            type='child_assessment_complete',
        ).exists()


class TestVisibleToParentNote:
    def setup_method(self):
        self.client = APIClient()

    def test_visible_note_appears_in_child_detail(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        counselor = CounselorFactory()
        CounselorAssignmentFactory(counselor=counselor, student_profile=profile)
        CounselorNoteFactory(
            counselor=counselor, student=student,
            body='Great progress this term!', visible_to_parent=True,
        )
        CounselorNoteFactory(
            counselor=counselor, student=student,
            body='Private note', visible_to_parent=False,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(f'/api/v1/parents/children/{student.id}/')
        data = resp.json()['data']
        assert data['latest_note'] is not None
        assert data['latest_note']['body'] == 'Great progress this term!'
        assert [note['body'] for note in data['parent_visible_notes']] == [
            'Great progress this term!',
        ]

    def test_no_visible_notes_returns_null(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        counselor = CounselorFactory()
        CounselorNoteFactory(
            counselor=counselor, student=student,
            body='Private', visible_to_parent=False,
        )
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(f'/api/v1/parents/children/{student.id}/')
        data = resp.json()['data']
        assert data['latest_note'] is None
        assert data['parent_visible_notes'] == []

    def test_counselor_can_toggle_visible_to_parent(self):
        counselor = CounselorFactory()
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        CounselorAssignmentFactory(counselor=counselor, student_profile=profile)
        note = CounselorNoteFactory(
            counselor=counselor, student=student,
            body='Some note', visible_to_parent=False,
        )
        self.client.force_authenticate(user=counselor)

        resp = self.client.patch(
            f'/api/v1/counselors/notes/{note.id}/',
            {'visible_to_parent': True},
            format='json',
        )
        assert resp.status_code == 200
        note.refresh_from_db()
        assert note.visible_to_parent is True
