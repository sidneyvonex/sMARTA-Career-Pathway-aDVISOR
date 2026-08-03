from django.urls import path

from .views import LetterDetailView, LetterListView

urlpatterns = [
    path('letters/', LetterListView.as_view(), name='dev-letter-list'),
    path('letters/<int:pk>/', LetterDetailView.as_view(), name='dev-letter-detail'),
]
