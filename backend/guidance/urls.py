from django.urls import path

from .views import (
    CombinationDetailView,
    CombinationListView,
    CurrentFrameworkView,
    PathwayListView,
)


urlpatterns = [
    path(
        'framework/current/',
        CurrentFrameworkView.as_view(),
        name='guidance-current-framework',
    ),
    path('pathways/', PathwayListView.as_view(), name='guidance-pathways'),
    path(
        'combinations/',
        CombinationListView.as_view(),
        name='guidance-combinations',
    ),
    path(
        'combinations/<int:combination_id>/',
        CombinationDetailView.as_view(),
        name='guidance-combination-detail',
    ),
]
