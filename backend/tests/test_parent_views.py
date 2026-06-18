import pytest
from rest_framework.test import APIClient
from tests.factories import (
    ParentFactory, VerifiedUserFactory, StudentProfileFactory,
    ParentStudentLinkFactory, CounselorAssignmentFactory,
    RIASECAssessmentFactory, StudentSubjectFactory,
    SubjectFactory, CBCGradeFactory, CounselorFactory,
)
from riasec.models import RIASECScore, Recommendation, Pathway
from notifications.models import Notification

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
        student = VerifiedUserFactory(role='student', first_name='Tom', last_name='Doe', county='kiambu')
        profile = StudentProfileFactory(user=student, grade=9)
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
        profile = StudentProfileFactory(user=student, grade=9, bio='Loves math')
        ParentStudentLinkFactory(parent=parent, student=student)
        self.client.force_authenticate(user=parent)

        resp = self.client.get(self._url(student.id))
        assert resp.status_code == 200
        data = resp.json()['data']
        assert data['profile']['first_name'] == 'Tom'
        assert data['profile']['grade'] == 9
        assert data['profile']['bio'] == 'Loves math'

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
        profile = StudentProfileFactory(user=student, grade=9)
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
