from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified


def _success(data=None, message=''):
    return Response({'data': data, 'error': None, 'message': message}, status=status.HTTP_200_OK)


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        # CounselorStudentAssignment model added in Sprint 6
        return _success(data=[])


class CounselorStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
        return _success(data={
            'total_students': 0,
            'assessments_done': 0,
            'students_needing_attention': 0,
            'notes_written': 0,
        })
