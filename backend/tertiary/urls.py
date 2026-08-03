from django.urls import path

from .views import InstitutionListView, ProgrammeDetailView, ProgrammeListView


urlpatterns = [
    path('institutions/', InstitutionListView.as_view(), name='tertiary-institutions'),
    path('programmes/', ProgrammeListView.as_view(), name='tertiary-programmes'),
    path('programmes/<int:programme_id>/', ProgrammeDetailView.as_view(), name='tertiary-programme-detail'),
]
