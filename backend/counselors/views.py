from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsCounselor, IsEmailVerified


def _success(data=None, message='', status_code=status.HTTP_200_OK):
    return Response({'data': data, 'error': None, 'message': message}, status=status_code)


def _error(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({'data': None, 'error': True, 'message': message}, status=status_code)


class CounselorStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsCounselor]

    def get(self, request):
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
