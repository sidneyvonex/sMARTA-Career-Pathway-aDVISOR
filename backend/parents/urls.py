from django.urls import path
from .views import ParentChildrenView, ParentChildDetailView

urlpatterns = [
    path('children/', ParentChildrenView.as_view(), name='parent-children'),
    path('children/<int:student_id>/', ParentChildDetailView.as_view(), name='parent-child-detail'),
]
