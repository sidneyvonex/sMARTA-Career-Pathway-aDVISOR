"""Reusable school reporting statistics and roster queries."""

from django.db.models import Count, Exists, F, OuterRef, Q

from accounts.models import StudentProfile, StudentSchoolMembership, User
from counselors.models import CounselorAssignment
from guidance.models import FrameworkVersion, SchoolOffering
from riasec.models import RIASECAssessment
from reports.reporting import cohort_roster_queryset, cohort_roster_rows
from students.models import CBCGrade


def active_school_profiles(school):
    return StudentProfile.objects.filter(
        school=school,
        mode='school_linked',
        school_membership_status='active',
    )


def get_school_stats(school):
    has_assessment = RIASECAssessment.objects.filter(student_profile=OuterRef('pk'))
    profiles = active_school_profiles(school).annotate(
        has_assessment=Exists(has_assessment),
        enrolled_subject_count=Count('enrolled_subjects', distinct=True),
        subjects_with_evidence=Count(
            'enrolled_subjects',
            filter=Q(enrolled_subjects__grades__isnull=False),
            distinct=True,
        ),
    )
    total_students = profiles.count()
    assessed = profiles.filter(has_assessment=True).count()
    evidence_complete = profiles.filter(
        enrolled_subject_count__gte=3,
        subjects_with_evidence=F('enrolled_subject_count'),
    ).count()
    choices_saved = profiles.filter(combination_choices__isnull=False).distinct().count()
    plans_created = profiles.filter(learner_plan__isnull=False).count()
    reviews_completed = profiles.filter(learner_plan__review_status='reviewed').count()
    pending_memberships = StudentSchoolMembership.objects.filter(
        school=school,
        status=StudentSchoolMembership.STATUS_PENDING,
    ).count()
    pending_memberships += StudentProfile.objects.filter(
        school=school,
        mode='school_linked',
        school_membership_status='pending',
        school_memberships__isnull=True,
    ).count()
    assigned_ids = CounselorAssignment.objects.filter(
        school=school,
        is_active=True,
    ).values_list('student_profile_id', flat=True)
    unassigned = profiles.exclude(pk__in=assigned_ids).count()
    counselors = list(
        User.objects.filter(school=school, role='counselor')
        .annotate(
            active_student_count=Count(
                'student_assignments',
                filter=Q(
                    student_assignments__is_active=True,
                    student_assignments__school=school,
                    student_assignments__student_profile__school_membership_status='active',
                ),
                distinct=True,
            ),
        )
        .order_by('first_name', 'last_name', 'pk')
    )
    framework = FrameworkVersion.objects.current()
    offerings_count = (
        SchoolOffering.objects.filter(
            school=school,
            is_active=True,
            combination__framework_version=framework,
            combination__is_active=True,
            combination__track__is_active=True,
        ).count()
        if framework is not None else 0
    )
    academic_progress = list(
        CBCGrade.objects.filter(
            student_subject__student_profile__in=profiles,
        )
        .values(
            'year',
            'term',
            'level',
            'student_subject__continuity_code',
            'student_subject__subject__name',
        )
        .annotate(count=Count('id'))
        .order_by(
            'year',
            'term',
            'student_subject__subject__name',
            'level',
        )
    )
    return {
        'total_students': total_students,
        'total_counselors': len(counselors),
        'assessed': assessed,
        'unassigned': unassigned,
        'pending_memberships': pending_memberships,
        'evidence_complete': evidence_complete,
        'choices_saved': choices_saved,
        'plans_created': plans_created,
        'reviews_completed': reviews_completed,
        'offerings_count': offerings_count,
        'offerings_configured': offerings_count > 0,
        'academic_progress': [
            {
                'year': row['year'],
                'term': row['term'],
                'level': row['level'],
                'continuity_code': row['student_subject__continuity_code'],
                'subject_name': row['student_subject__subject__name'],
                'count': row['count'],
            }
            for row in academic_progress
        ],
        'counselor_workload': [
            {
                'counselor_id': counselor.id,
                'counselor_name': f'{counselor.first_name} {counselor.last_name}'.strip(),
                'student_count': counselor.active_student_count,
            }
            for counselor in counselors
        ],
    }


def get_school_roster(school, grade=None):
    queryset = cohort_roster_queryset(active_school_profiles(school), grade)
    return cohort_roster_rows(queryset, include_counselor=True)
