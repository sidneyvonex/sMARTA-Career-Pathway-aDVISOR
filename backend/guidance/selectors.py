from django.db.models import Prefetch

from .models import SchoolOffering, SubjectCombination


def active_combination_queryset(framework):
    active_offerings = (
        SchoolOffering.objects.filter(is_active=True, school__is_active=True)
        .select_related('school')
        .order_by('school__name')
    )
    return (
        SubjectCombination.objects.filter(
            framework_version=framework,
            is_active=True,
            track__is_active=True,
        )
        .select_related(
            'framework_version',
            'track__pathway',
            'subject_one',
            'subject_two',
            'subject_three',
        )
        .prefetch_related(
            Prefetch(
                'school_offerings',
                queryset=active_offerings,
                to_attr='active_school_offerings',
            )
        )
    )
