import pytest
from django.db import IntegrityError
from django.test import override_settings
from accounts.tokens import make_parent_invite_token, make_invite_token
from parents.models import ParentStudentLink
from tests.factories import ParentFactory, VerifiedUserFactory, ParentStudentLinkFactory

pytestmark = pytest.mark.django_db


class TestParentStudentLink:
    def test_create_link(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        link = ParentStudentLinkFactory(parent=parent, student=student)
        assert link.parent == parent
        assert link.student == student
        assert link.created_at is not None

    def test_unique_together(self):
        parent = ParentFactory()
        student = VerifiedUserFactory(role='student')
        ParentStudentLinkFactory(parent=parent, student=student)
        with pytest.raises(IntegrityError):
            ParentStudentLinkFactory(parent=parent, student=student)

    def test_parent_can_link_multiple_students(self):
        parent = ParentFactory()
        s1 = VerifiedUserFactory(role='student')
        s2 = VerifiedUserFactory(role='student')
        ParentStudentLinkFactory(parent=parent, student=s1)
        ParentStudentLinkFactory(parent=parent, student=s2)
        assert parent.linked_children.count() == 2

    def test_student_can_have_multiple_parents(self):
        student = VerifiedUserFactory(role='student')
        p1 = ParentFactory()
        p2 = ParentFactory()
        ParentStudentLinkFactory(parent=p1, student=student)
        ParentStudentLinkFactory(parent=p2, student=student)
        assert student.linked_parents.count() == 2

    def test_str_representation(self):
        parent = ParentFactory(first_name='Jane', last_name='Doe')
        student = VerifiedUserFactory(role='student', first_name='Tom', last_name='Doe')
        link = ParentStudentLinkFactory(parent=parent, student=student)
        assert 'Jane Doe' in str(link)
        assert 'Tom Doe' in str(link)


class TestAcceptInviteCreatesLink:
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_accepting_parent_invite_creates_link(self, client):
        student = VerifiedUserFactory(role='student')
        token = make_parent_invite_token(student_id=student.id, email='parent@test.com')
        resp = client.post('/api/v1/auth/accept-invite/', {
            'token': token,
            'password': 'SecurePass123!',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'county': 'kiambu',
        }, content_type='application/json')
        assert resp.status_code == 201
        assert ParentStudentLink.objects.filter(
            parent__email='parent@test.com',
            student=student,
        ).exists()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_accepting_staff_invite_does_not_create_link(self, client):
        token = make_invite_token(email='counselor@test.com', role='counselor')
        resp = client.post('/api/v1/auth/accept-invite/', {
            'token': token,
            'password': 'SecurePass123!',
            'first_name': 'Bob',
            'last_name': 'Smith',
            'county': 'nairobi',
        }, content_type='application/json')
        assert resp.status_code == 201
        assert ParentStudentLink.objects.count() == 0
