from django.urls import path
from . import views

urlpatterns = [
    path('school/', views.SchoolProfileView.as_view(), name='school-admin-profile'),
]
