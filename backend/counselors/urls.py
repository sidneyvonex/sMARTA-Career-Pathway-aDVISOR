from django.urls import path
from .views import CounselorStudentsView, CounselorStatsView

urlpatterns = [
    path('students/', CounselorStudentsView.as_view(), name='counselor-students'),
    path('stats/', CounselorStatsView.as_view(), name='counselor-stats'),
]
