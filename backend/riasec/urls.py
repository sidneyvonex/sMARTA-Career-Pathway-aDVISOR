from django.urls import path
from .views import QuestionListView, AssessmentView, AssessmentLatestView

urlpatterns = [
    path('questions/', QuestionListView.as_view(), name='riasec-questions'),
    path('', AssessmentView.as_view(), name='riasec-assessment'),
    path('latest/', AssessmentLatestView.as_view(), name='riasec-latest'),
]
