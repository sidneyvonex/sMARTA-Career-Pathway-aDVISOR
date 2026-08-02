from tertiary.placement import OfficialCriteriaUnavailableEvaluator, PlacementEvaluator
from tests.factories import ProgrammeFactory


def test_unavailable_evaluator_implements_versioned_interface_without_calculation(db):
    """Catches placement heuristics or learner evidence changing an unavailable result."""
    programme = ProgrammeFactory()
    evaluator: PlacementEvaluator = OfficialCriteriaUnavailableEvaluator()

    empty = evaluator.evaluate(programme, {}, 'cbe-senior-school-v1')
    detailed = evaluator.evaluate(
        programme,
        {'levels': ['EE1', 'ME1'], 'raw_scores': [99, 100]},
        'cbe-senior-school-v1',
    )

    assert empty == detailed
    assert empty == {
        'adapter_version': 'v1',
        'status': 'official_criteria_unavailable',
        'framework': {
            'requested_version': 'cbe-senior-school-v1',
            'catalogue_framework': programme.education_framework,
            'admission_cycle': programme.admission_cycle,
        },
        'source': {
            'url': programme.source_url,
            'effective_date': programme.effective_date.isoformat(),
            'verification_status': programme.verification_status,
            'source_scope': programme.source_scope,
            'external_key': programme.external_key,
        },
        'explanation': (
            'Official placement criteria are unavailable for this framework and '
            'catalogue reference. Smarta Shauri does not substitute a formula or threshold.'
        ),
    }
    assert not {
        'score', 'threshold', 'formula', 'eligible', 'ineligible', 'probability'
    }.intersection(empty)
