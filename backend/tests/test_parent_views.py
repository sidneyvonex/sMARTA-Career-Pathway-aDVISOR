import pytest
from rest_framework.test import APIClient
from tests.factories import (
    ParentFactory, VerifiedUserFactory, StudentProfileFactory,
    ParentStudentLinkFactory, CounselorAssignmentFactory,
    RIASECAssessmentFactory, StudentSubjectFactory,
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
