from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsStudent, IsEmailVerified


def _success(data=None, message='', status_code=status.HTTP_200_OK):
    return Response({'data': data, 'error': None, 'message': message}, status=status_code)


def _error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({'data': None, 'error': True, 'message': message}, status=status_code)


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def get(self, request): return _success()
    def patch(self, request): return _success()


class PhotoUploadView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def post(self, request): return _success()
    def delete(self, request): return _success()


class SubjectListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    def get(self, request): return _success()


class MySubjectListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def get(self, request): return _success()
    def post(self, request): return _success()


class MySubjectRemoveView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def post(self, request, pk): return _success()


class CBCGradeListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def get(self, request, subject_pk): return _success()
    def post(self, request, subject_pk): return _success()


class CBCGradeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]
    def put(self, request, subject_pk, grade_pk): return _success()
    def delete(self, request, subject_pk, grade_pk): return _success()
