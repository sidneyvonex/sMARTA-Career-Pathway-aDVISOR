"""Journey-aware next-action guidance.

Covers the correction that RIASEC is only a prerequisite for pre-selection
learners: learners who already selected a pathway are routed to progress
tracking and the assessment stays optional. See
docs/superpowers/plans/2026-08-03-journey-aware-next-actions.md
"""
import pytest
from rest_framework.test import APIClient

from students.summaries import next_action_for
from tests.factories import (
    PathwayFactory,
    StudentProfileFactory,
    VerifiedUserFactory,
)


pytestmark = pytest.mark.django_db

PROFILE_URL = '/api/v1/students/profile/'
EVIDENCE_URL = '/api/v1/students/evidence-summary/'


def _next_action(
    *,
    journey_status,
    assessment='not_started',
    total_subjects=0,
    evidence_status='not_started',
    saved_combinations=0,
    has_provisional=False,
    plan_status='not_started',
):
    return next_action_for(
        {'status': 'complete'},
        {'status': evidence_status, 'total_subjects': total_subjects},
        {'status': assessment},
        saved_combinations,
        has_provisional_choice=has_provisional,
        plan_status=plan_status,
        journey_status=journey_status,
    )


# --- Pure-function scenarios (spec §10.1–§10.6) -----------------------------

def test_incomplete_profile_always_comes_first():
    action = next_action_for(
        {'status': 'incomplete'},
        {'status': 'not_started', 'total_subjects': 0},
        {'status': 'complete'},
        0,
        journey_status='selected',
    )
    assert action['code'] == 'complete_profile'


def test_undeclared_journey_is_asked_to_declare():
    assert _next_action(journey_status='')['code'] == 'declare_journey_stage'


def test_pre_selection_learner_is_recommended_the_assessment():
    # §10.1 Grade 9 without a selection.
    assert _next_action(journey_status='not_selected')['code'] == (
        'complete_interest_assessment'
    )


def test_unsure_learner_is_recommended_the_assessment():
    assert _next_action(journey_status='unsure')['code'] == (
        'complete_interest_assessment'
    )


def test_selected_learner_without_subjects_records_subjects():
    # §10.5
    assert _next_action(journey_status='selected')['code'] == (
        'record_current_subjects'
    )


def test_selected_learner_with_subjects_but_no_grades_adds_evidence():
    action = _next_action(
        journey_status='selected',
        total_subjects=3,
        evidence_status='in_progress',
    )
    assert action['code'] == 'add_academic_evidence'


def test_selected_learner_with_ready_evidence_goes_to_progress():
    # §10.2 / §10.3 externally selected learner is sent to progress, RIASEC skipped.
    action = _next_action(
        journey_status='selected',
        assessment='not_started',
        total_subjects=3,
        evidence_status='ready',
    )
    assert action['code'] == 'view_progress'
    assert action['href'] == '/grades'


def test_currently_enrolled_learner_is_treated_like_selected():
    action = _next_action(
        journey_status='currently_enrolled',
        total_subjects=3,
        evidence_status='ready',
    )
    assert action['code'] == 'view_progress'


def test_reconsidering_learner_gets_assessment_then_counsellor_review():
    # §10.6
    assert _next_action(journey_status='reconsidering')['code'] == (
        'complete_interest_assessment'
    )
    reviewed = _next_action(journey_status='reconsidering', assessment='complete')
    assert reviewed['code'] == 'request_counsellor_review'


def test_pre_selection_flow_progresses_through_exploration():
    explore = _next_action(journey_status='not_selected', assessment='complete')
    assert explore['code'] == 'explore_combinations'
    compare = _next_action(
        journey_status='unsure', assessment='complete', saved_combinations=2
    )
    assert compare['code'] == 'compare_combinations'


# --- Access is never blocked by an incomplete assessment (spec §10.4) --------

def test_incomplete_assessment_does_not_block_progress_for_selected_learner():
    """A selected learner with no assessment is still routed to progress, never
    to the assessment."""
    learner = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
        journey_status='selected',
        bio='Loves biology',
        date_of_birth='2010-05-01',
        career_interests='Medicine',
    )
    client = APIClient()
    client.force_authenticate(learner.user)

    response = client.get(EVIDENCE_URL)

    assert response.status_code == 200
    assert response.data['data']['assessment']['status'] == 'not_started'
    assert response.data['data']['next_action']['href'] != '/assessment'


# --- Provenance guard (spec §10.7 & §10.8) ----------------------------------

def test_learner_reported_selection_can_be_updated_by_the_learner():
    pathway = PathwayFactory()
    learner = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
        journey_status='selected',
        selection_source='learner_reported',
        selection_verified=False,
    )
    client = APIClient()
    client.force_authenticate(learner.user)

    response = client.patch(
        PROFILE_URL,
        {'current_pathway': pathway.id, 'current_subject_combination': 'STEM'},
        format='json',
    )

    assert response.status_code == 200
    learner.refresh_from_db()
    assert learner.current_pathway_id == pathway.id
    assert learner.selection_source == 'learner_reported'


def test_school_verified_selection_cannot_be_silently_changed():
    original = PathwayFactory()
    other = PathwayFactory()
    learner = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
        journey_status='selected',
        current_pathway=original,
        selection_source='school_verified',
        selection_verified=True,
    )
    client = APIClient()
    client.force_authenticate(learner.user)

    response = client.patch(
        PROFILE_URL,
        {'current_pathway': other.id},
        format='json',
    )

    assert response.status_code == 400
    learner.refresh_from_db()
    assert learner.current_pathway_id == original.id


def test_verified_provenance_is_reported_in_journey_summary():
    pathway = PathwayFactory()
    learner = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        grade=10,
        journey_status='currently_enrolled',
        current_pathway=pathway,
        selection_source='school_verified',
        selection_verified=True,
        bio='x',
        date_of_birth='2010-01-01',
        career_interests='y',
    )
    client = APIClient()
    client.force_authenticate(learner.user)

    journey = client.get(EVIDENCE_URL).data['data']['journey']

    assert journey['selection_source'] == 'school_verified'
    assert journey['selection_verified'] is True
    assert journey['current_pathway'] == {'id': pathway.id, 'name': pathway.name}


# --- Safe default for existing learners (spec §10.9) ------------------------

def test_new_profile_defaults_to_undeclared_journey():
    learner = StudentProfileFactory(user=VerifiedUserFactory(role='student'))
    assert learner.journey_status == ''
    assert learner.selection_source == ''
    assert learner.selection_verified is False
    assert learner.has_authoritative_selection is False
