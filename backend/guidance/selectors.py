from django.db.models import Prefetch

from .models import SchoolOffering, SubjectCombination


def active_combination_queryset(framework, *, include_unverified_offerings=False):
    active_offerings = SchoolOffering.objects.filter(
        is_active=True,
        school__is_active=True,
    )
    if not include_unverified_offerings:
        active_offerings = active_offerings.filter(
            verification_status=SchoolOffering.VERIFICATION_VERIFIED,
            school__verification_status='verified',
        )
    active_offerings = active_offerings.select_related('school').order_by(
        'school__name'
    )
    return (
        SubjectCombination.objects.filter(
            framework_version=framework,
            is_active=True,
            track__is_active=True,
            verification_status=SubjectCombination.VERIFICATION_VERIFIED,
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
