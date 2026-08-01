"""Deterministic, advisory academic-progress derivation.

This module deliberately accepts evidence snapshots rather than querysets so the
rule table can be exercised without the database.  Views are responsible for
loading the related enrolments, frameworks, and level definitions efficiently.
"""

from collections import defaultdict


STATUS_DETAILS = {
    'support': {
        'label': 'Support',
        'suggested_action': (
            'Discuss support with a teacher, counsellor, or trusted adult and '
            'record the next available evidence.'
        ),
    },
    'insufficient_evidence': {
        'label': 'Insufficient evidence',
        'suggested_action': (
            'Record more academic evidence before drawing a progress trend.'
        ),
    },
    'needs_attention': {
        'label': 'Needs attention',
        'suggested_action': (
            'Review the recent evidence with a teacher, counsellor, or trusted '
            'adult and agree a support action.'
        ),
    },
    'strong': {
        'label': 'Strong',
        'suggested_action': (
            'Keep building on this progress and record the next available '
            'evidence.'
        ),
    },
    'on_track': {
        'label': 'On track',
        'suggested_action': (
            'Continue practising and record the next available evidence.'
        ),
    },
}

ADVISORY_DISCLAIMER = (
    'Academic progress is advisory only. It does not determine official CBE '
    'placement or admission.'
)

OVERALL_SEVERITY = (
    'support',
    'needs_attention',
    'insufficient_evidence',
    'on_track',
    'strong',
)


def _evidence_order(record):
    return (
        record['academic_grade'],
        record['year'],
        record['term'],
        record['created_at'],
        record['id'],
    )


def _has_coherent_verification(record):
    return bool(
        record.get('verified_by')
        and record.get('verified_at')
        and record.get('verified_school')
    )


def _confidence(records_used):
    if not records_used:
        return 'learner_entered'
    verified = [_has_coherent_verification(record) for record in records_used]
    if all(verified):
        return 'school_verified'
    if not any(verified):
        return 'learner_entered'
    return 'mixed'


def _outcome(
    continuity_code,
    subject_name,
    evidence,
    *,
    status,
    rule_code,
    explanation,
    records_used,
):
    detail = STATUS_DETAILS[status]
    return {
        'continuity_code': continuity_code,
        'subject_name': subject_name,
        'status': status,
        'label': detail['label'],
        'rule_code': rule_code,
        'explanation': explanation,
        'suggested_action': detail['suggested_action'],
        'evidence_confidence': _confidence(records_used),
        'records_used': records_used,
        'evidence': evidence,
    }


def derive_continuity_progress(continuity_code, subject_name, evidence):
    """Evaluate the approved rule table for one continuity-code evidence trend."""
    evidence = sorted(evidence, key=_evidence_order)
    if not evidence:
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='insufficient_evidence',
            rule_code='missing_evidence',
            explanation='No academic evidence is available for this subject.',
            records_used=[],
        )

    latest = evidence[-1]
    latest_level = latest['level']
    if latest_level in {'BE1', 'BE2'}:
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='support',
            rule_code='latest_be_support',
            explanation='The latest academic evidence is below expectation.',
            records_used=[latest],
        )

    if len(evidence) == 1:
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='insufficient_evidence',
            rule_code='one_non_be_insufficient',
            explanation=(
                'One non-below-expectation record is available, so a progress '
                'trend is not yet established.'
            ),
            records_used=[latest],
        )

    previous = evidence[-2]
    if previous['level'] in {'AE1', 'AE2', 'BE1', 'BE2'} and latest_level in {
        'AE1', 'AE2', 'BE1', 'BE2'
    }:
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='support',
            rule_code='two_ae_be_support',
            explanation=(
                'The two latest academic evidence records are approaching or '
                'below expectation.'
            ),
            records_used=[previous, latest],
        )

    two_declines = (
        len(evidence) >= 3
        and evidence[-3]['rank'] > previous['rank'] > latest['rank']
    )
    if latest_level in {'AE1', 'AE2'} or two_declines:
        records_used = evidence[-3:] if two_declines else [latest]
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='needs_attention',
            rule_code='latest_ae_or_two_declines_attention',
            explanation=(
                'The latest evidence needs attention.'
                if latest_level in {'AE1', 'AE2'}
                else 'The two latest directional comparisons are declines.'
            ),
            records_used=records_used,
        )

    improves_to_me2 = (
        latest['rank'] > previous['rank']
        and latest.get('me2_rank') is not None
        and latest['rank'] >= latest['me2_rank']
    )
    if latest_level in {'EE1', 'EE2'} or improves_to_me2:
        return _outcome(
            continuity_code,
            subject_name,
            evidence,
            status='strong',
            rule_code='latest_ee_or_improving_to_me2_strong',
            explanation=(
                'The latest academic evidence is exceeding expectation.'
                if latest_level in {'EE1', 'EE2'}
                else 'The latest directional comparison is an improvement to at '
                'least meeting expectation level 2.'
            ),
            records_used=[latest] if latest_level in {'EE1', 'EE2'} else [previous, latest],
        )

    return _outcome(
        continuity_code,
        subject_name,
        evidence,
        status='on_track',
        rule_code='otherwise_me_on_track',
        explanation='The available academic evidence is meeting expectation.',
        records_used=[latest],
    )


def derive_overall_progress(subjects):
    """Select the explicit severity winner without ranking or averaging evidence."""
    for status in OVERALL_SEVERITY:
        subject_codes = [
            subject['continuity_code']
            for subject in subjects
            if subject['status'] == status
        ]
        if subject_codes:
            return {
                'status': status,
                'label': STATUS_DETAILS[status]['label'],
                'subject_continuity_codes': subject_codes,
            }
    return {
        'status': 'insufficient_evidence',
        'label': STATUS_DETAILS['insufficient_evidence']['label'],
        'subject_continuity_codes': [],
    }


def derive_progress_for_enrolments(enrolments):
    """Group prefetched enrolments by active continuity identity and derive rows."""
    active_by_continuity = {}
    evidence_by_continuity = defaultdict(list)
    for enrolment in enrolments:
        continuity_code = enrolment.continuity_code
        if enrolment.is_active:
            current = active_by_continuity.get(continuity_code)
            if current is None or (
                enrolment.academic_grade,
                enrolment.academic_year,
                enrolment.pk,
            ) > (
                current.academic_grade,
                current.academic_year,
                current.pk,
            ):
                active_by_continuity[continuity_code] = enrolment

        for grade in enrolment.grades.all():
            rank_by_level = {
                definition.code: definition.rank
                for definition in grade.framework.level_definitions.all()
            }
            rank = rank_by_level.get(grade.level)
            if rank is None:
                continue
            evidence_by_continuity[continuity_code].append(
                {
                    'id': grade.pk,
                    'academic_grade': grade.academic_grade,
                    'year': grade.year,
                    'term': grade.term,
                    'level': grade.level,
                    'rank': rank,
                    'me2_rank': rank_by_level.get('ME2'),
                    'framework': {
                        'code': grade.framework.code,
                        'version': grade.framework.version,
                    },
                    'source': grade.source,
                    'verified_by': grade.verified_by_id,
                    'verified_school': grade.verified_school_id,
                    'verified_at': grade.verified_at.isoformat()
                    if grade.verified_at
                    else None,
                    'created_at': grade.created_at.isoformat(),
                }
            )

    subjects = [
        derive_continuity_progress(
            continuity_code,
            enrolment.subject.name,
            evidence_by_continuity[continuity_code],
        )
        for continuity_code, enrolment in sorted(active_by_continuity.items())
    ]
    return {
        'subjects': subjects,
        'overall': derive_overall_progress(subjects),
        'advisory_disclaimer': ADVISORY_DISCLAIMER,
    }
