from django.utils import timezone

from .models import CBCGrade


def rewrite_grade_definition_snapshot_for_history(
    *,
    grade_id,
    definition_id,
    audit_reason,
):
    """Narrow compatibility transition for legacy evidence snapshot repairs."""
    return CBCGrade.history.rewrite_definition_snapshot(
        grade_id=grade_id,
        definition_id=definition_id,
        audit_reason=audit_reason,
    )


def transition_grade_verification(
    grade,
    *,
    actor,
    school,
    should_verify,
    verified_at=None,
):
    """Persist the only supported verification-state transition."""
    update_fields = {'verified_by', 'verified_at', 'updated_at'}
    if should_verify:
        grade.verified_by = actor
        grade.verified_at = verified_at or timezone.now()
        if grade.verified_school_id is None:
            grade.verified_school = school
            update_fields.add('verified_school')
    else:
        grade.verified_by = None
        grade.verified_at = None
    grade._persist_verification_transition(update_fields=update_fields)
    return grade
