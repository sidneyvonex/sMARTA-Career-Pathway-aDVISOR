from django.db.models import Count, Prefetch

from riasec.models import RIASECAssessment

from .models import CBCGrade, StudentSubject


PROFILE_EVIDENCE_FIELDS = ('bio', 'date_of_birth', 'career_interests')


def academic_evidence_summary(profile):
    enrollments = list(
        StudentSubject.objects.filter(student_profile=profile)
        .annotate(grade_count=Count('grades'))
        .values('id', 'grade_count')
    )
    total_subjects = len(enrollments)
    subjects_with_evidence = sum(
        enrollment['grade_count'] > 0 for enrollment in enrollments
    )
    total_grade_records = sum(
        enrollment['grade_count'] for enrollment in enrollments
    )
    if total_subjects >= 3 and subjects_with_evidence == total_subjects:
        evidence_status = 'ready'
    elif total_subjects or total_grade_records:
        evidence_status = 'in_progress'
    else:
        evidence_status = 'not_started'
    return {
        'status': evidence_status,
        'total_subjects': total_subjects,
        'subjects_with_evidence': subjects_with_evidence,
        'total_grade_records': total_grade_records,
    }


def profile_completion_summary(profile):
    missing_fields = [
        field_name
        for field_name in PROFILE_EVIDENCE_FIELDS
        if not getattr(profile, field_name)
    ]
    total_fields = len(PROFILE_EVIDENCE_FIELDS)
    completed_fields = total_fields - len(missing_fields)
    return {
        'status': 'complete' if not missing_fields else 'incomplete',
        'completed_fields': completed_fields,
        'total_fields': total_fields,
        'percent': round((completed_fields / total_fields) * 100),
        'missing_fields': missing_fields,
    }


def assessment_summary(profile):
    assessment = (
        RIASECAssessment.objects.filter(student_profile=profile)
        .order_by('-submitted_at', '-pk')
        .first()
    )
    if assessment is None:
        return {
            'status': 'not_started',
            'instrument_version': None,
            'submitted_at': None,
        }
    return {
        'status': 'complete',
        'instrument_version': getattr(assessment, 'instrument_version', None),
        'submitted_at': assessment.submitted_at.isoformat(),
    }


def next_action_for(
    profile_completion,
    academic_evidence,
    assessment,
    saved_combination_count,
    has_provisional_choice=False,
    plan_status='not_started',
):
    if profile_completion['status'] != 'complete':
        return {
            'code': 'complete_profile',
            'title': 'Complete your learner profile',
            'href': '/profile',
        }
    if academic_evidence['status'] != 'ready':
        return {
            'code': 'add_academic_evidence',
            'title': 'Add your academic evidence',
            'href': '/grades',
        }
    if assessment['status'] != 'complete':
        return {
            'code': 'complete_interest_assessment',
            'title': 'Complete your interest assessment',
            'href': '/assessment',
        }
    if saved_combination_count == 0:
        return {
            'code': 'explore_combinations',
            'title': 'Explore subject combinations',
            'href': '/explore',
        }
    if not has_provisional_choice:
        return {
            'code': 'compare_combinations',
            'title': 'Compare your saved combinations',
            'href': '/compare',
        }
    if plan_status == 'not_started':
        return {
            'code': 'create_plan',
            'title': 'Turn your provisional choice into a plan',
            'href': '/plan',
        }
    return {
        'code': 'review_plan',
        'title': 'Review your plan and next milestone',
        'href': '/plan',
    }


def grade_summary(profile):
    grade_queryset = CBCGrade.objects.order_by('year', 'term', 'pk')
    enrollments = list(
        StudentSubject.objects.filter(student_profile=profile)
        .select_related('subject')
        .prefetch_related(
            Prefetch('grades', queryset=grade_queryset, to_attr='summary_grades')
        )
        .order_by('subject__name')
    )

    subjects = []
    total_grade_records = 0
    subjects_with_evidence = 0
    for enrollment in enrollments:
        grades = [
            {
                'id': grade.id,
                'term': grade.term,
                'year': grade.year,
                'level': grade.level,
                'created_at': grade.created_at.isoformat(),
                'updated_at': grade.updated_at.isoformat(),
            }
            for grade in enrollment.summary_grades
        ]
        total_grade_records += len(grades)
        if grades:
            subjects_with_evidence += 1
        subjects.append(
            {
                'enrollment_id': enrollment.id,
                'subject': {
                    'id': enrollment.subject.id,
                    'code': enrollment.subject.code,
                    'name': enrollment.subject.name,
                    'grade': enrollment.subject.grade,
                    'category': enrollment.subject.category,
                },
                'grades': grades,
                'latest_grade': grades[-1] if grades else None,
            }
        )

    total_subjects = len(enrollments)
    if total_subjects >= 3 and subjects_with_evidence == total_subjects:
        evidence_status = 'ready'
    elif total_subjects or total_grade_records:
        evidence_status = 'in_progress'
    else:
        evidence_status = 'not_started'
    return {
        'status': evidence_status,
        'total_subjects': total_subjects,
        'subjects_with_evidence': subjects_with_evidence,
        'total_grade_records': total_grade_records,
        'subjects': subjects,
    }
