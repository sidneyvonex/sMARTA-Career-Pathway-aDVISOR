from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import StudentProfile
from accounts.permissions import IsEmailVerified, IsStudent
from accounts.response import _success
from .models import AcademicPeriod
from .periods import serialize_academic_period


class AcademicPeriodListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStudent]

    def get(self, request):
        StudentProfile.objects.only('id').get(user=request.user)
        return _success(
            data=[
                serialize_academic_period(period)
                for period in AcademicPeriod.objects.all()
            ]
        )
