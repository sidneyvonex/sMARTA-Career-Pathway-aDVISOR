from django.urls import path
from .views import ParentChildrenView

urlpatterns = [
    path('children/', ParentChildrenView.as_view(), name='parent-children'),
]
