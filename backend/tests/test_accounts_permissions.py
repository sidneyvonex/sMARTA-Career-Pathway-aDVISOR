import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory
from accounts.permissions import (
    IsStudent, IsCounselor, IsSchoolAdmin, IsParent, IsSystemAdmin, IsEmailVerified
)
from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(role, is_email_verified=True):
    return User(email=f'{role}@test.com', role=role, is_email_verified=is_email_verified)


def make_request(user):
    factory = APIRequestFactory()
    request = factory.get('/')
    request.user = user
    return request


class TestRolePermissions:
    def _check(self, permission_class, role, expected):
        user = make_user(role)
        request = make_request(user)
        assert permission_class().has_permission(request, None) == expected

    def test_is_student_allows_student(self):
        self._check(IsStudent, 'student', True)

    def test_is_student_blocks_counselor(self):
        self._check(IsStudent, 'counselor', False)

    def test_is_counselor_allows_counselor(self):
        self._check(IsCounselor, 'counselor', True)

    def test_is_counselor_blocks_student(self):
        self._check(IsCounselor, 'student', False)

    def test_is_school_admin_allows_school_admin(self):
        self._check(IsSchoolAdmin, 'school_admin', True)

    def test_is_school_admin_blocks_student(self):
        self._check(IsSchoolAdmin, 'student', False)

    def test_is_parent_allows_parent(self):
        self._check(IsParent, 'parent', True)

    def test_is_parent_blocks_student(self):
        self._check(IsParent, 'student', False)

    def test_is_system_admin_allows_system_admin(self):
        self._check(IsSystemAdmin, 'system_admin', True)

    def test_is_system_admin_blocks_student(self):
        self._check(IsSystemAdmin, 'student', False)


class TestIsEmailVerified:
    def test_allows_verified_user(self):
        user = make_user('student', is_email_verified=True)
        request = make_request(user)
        assert IsEmailVerified().has_permission(request, None) is True

    def test_blocks_unverified_user(self):
        user = make_user('student', is_email_verified=False)
        request = make_request(user)
        assert IsEmailVerified().has_permission(request, None) is False


class TestAnonymousUserBlocked:
    """All permission classes must reject anonymous/unauthenticated requests."""

    def _anon_request(self):
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        return request

    @pytest.mark.parametrize('permission_class', [
        IsStudent, IsCounselor, IsSchoolAdmin, IsParent, IsSystemAdmin, IsEmailVerified
    ])
    def test_blocks_anonymous_user(self, permission_class):
        request = self._anon_request()
        assert permission_class().has_permission(request, None) is False
