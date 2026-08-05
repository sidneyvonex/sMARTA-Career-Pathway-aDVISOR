from .models import AcademicPeriod


ENTRY_CLOSED_MESSAGE = (
    'Marks entry is not open for this term. A term must be complete and its '
    'submission window must still be active.'
)


def academic_period_for(*, year, term):
    try:
        return AcademicPeriod.objects.get(year=year, term=term)
    except AcademicPeriod.DoesNotExist:
        return None


def open_academic_period_for(*, year, term):
    period = academic_period_for(year=year, term=term)
    if period is None or not period.accepts_entries():
        return None
    return period


def serialize_academic_period(period):
    return {
        'id': period.id,
        'year': period.year,
        'term': period.term,
        'term_ends_at': period.term_ends_at.isoformat(),
        'entry_opens_at': period.entry_opens_at.isoformat(),
        'entry_closes_at': period.entry_closes_at.isoformat(),
        'published_at': (
            period.published_at.isoformat() if period.published_at else None
        ),
        'state': period.state,
        'can_submit': period.accepts_entries(),
    }
