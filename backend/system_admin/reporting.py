"""Reusable platform dashboard and report statistics."""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import COUNTY_CHOICES, School, StudentProfile, User
from guidance.models import FrameworkVersion, LearnerPlan
from .models import AuditLog

VALID_COUNTIES = {value for value, _label in COUNTY_CHOICES}


def get_platform_stats():
    users_by_role = {
        row['role']: row['count']
        for row in User.objects.values('role').annotate(count=Count('id'))
    }
    schools_by_county = {
        row['county']: row['count']
        for row in School.objects.filter(is_active=True)
        .values('county').annotate(count=Count('id'))
    }
    learner_profiles = StudentProfile.objects.select_related('user')
    registered_learners = learner_profiles.count()
    verified_learners = learner_profiles.filter(user__is_email_verified=True).count()
    pending_school_links = learner_profiles.filter(
        mode='school_linked',
        school_membership_status='pending',
    ).count()
    learners_by_county = {county: 0 for county in VALID_COUNTIES}
    for row in (
        learner_profiles.exclude(user__county__isnull=True)
        .values('user__county').annotate(count=Count('id'))
    ):
        if row['user__county'] in learners_by_county:
            learners_by_county[row['user__county']] = row['count']
    eligible = learner_profiles.filter(
        mode='school_linked',
        school_membership_status='active',
        school__is_active=True,
    )
    eligible_count = eligible.count()
    assigned_count = eligible.filter(
        counselor_assignments__is_active=True,
    ).distinct().count()
    assignment_percent = round((assigned_count / eligible_count) * 100) if eligible_count else 0
    plans_completed = LearnerPlan.objects.filter(
        student_profile__in=eligible,
        review_status=LearnerPlan.STATUS_REVIEWED,
    ).count()
    framework = FrameworkVersion.objects.current()
    recent_audit = list(
        AuditLog.objects.select_related('actor')[:10].values(
            'id', 'action', 'target_type', 'target_id', 'created_at',
            'actor__email', 'actor__first_name', 'actor__last_name',
        )
    )
    for entry in recent_audit:
        entry['actor_email'] = entry.pop('actor__email')
        entry['actor_name'] = (
            f"{entry.pop('actor__first_name', '') or ''} "
            f"{entry.pop('actor__last_name', '') or ''}"
        ).strip()
        entry['created_at'] = entry['created_at'].isoformat()
    return {
        'users_by_role': users_by_role,
        'schools_by_county': schools_by_county,
        'total_schools': School.objects.filter(is_active=True).count(),
        'registered_learners': registered_learners,
        'learners_by_county': learners_by_county,
        'verified_learners': verified_learners,
        'pending_school_links': pending_school_links,
        'assignment_coverage': {
            'assigned': assigned_count,
            'eligible': eligible_count,
            'percent': assignment_percent,
        },
        'plans_completed': plans_completed,
        'framework': ({
            'code': framework.code,
            'title': framework.title,
            'source_url': framework.source_url,
            'effective_date': framework.effective_date.isoformat(),
        } if framework else None),
        'recent_signups': User.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7),
        ).count(),
        'recent_audit': recent_audit,
    }


def get_schools_directory():
    return list(
        School.objects.annotate(
            student_count=Count(
                'studentprofile',
                filter=Q(
                    studentprofile__mode='school_linked',
                    studentprofile__school_membership_status='active',
                ),
                distinct=True,
            ),
            counselor_count=Count(
                'staff',
                filter=Q(staff__role='counselor'),
                distinct=True,
            ),
        ).order_by('county', 'name').values(
            'id', 'name', 'county', 'is_active', 'student_count', 'counselor_count',
        )
    )
