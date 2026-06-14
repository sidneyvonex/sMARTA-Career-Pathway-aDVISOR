from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'


class IsCounselor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'counselor'


class IsSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'school_admin'


class IsParent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'parent'


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'system_admin'


class IsEmailVerified(BasePermission):
    message = 'Please verify your email address before continuing.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_email_verified
