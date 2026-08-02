import csv
from datetime import date

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from tertiary.models import (
    HistoricalAdmissionReference,
    Institution,
    LearnerEducationGoal,
    Programme,
    ProgrammeSubjectReference,
)
from tests.factories import (
    HistoricalAdmissionReferenceFactory,
    InstitutionFactory,
    LearnerEducationGoalFactory,
    ProgrammeFactory,
    ProgrammeSubjectReferenceFactory,
    StudentProfileFactory,
    VerifiedUserFactory,
)


INSTITUTIONS_URL = '/api/v1/tertiary/institutions/'
PROGRAMMES_URL = '/api/v1/tertiary/programmes/'
GOALS_URL = '/api/v1/students/education-goals/'
PROVENANCE = {
    'source_url', 'education_framework', 'admission_cycle', 'effective_date',
    'verification_status', 'source_scope', 'external_key',
}


def auth_client(profile=None):
    profile = profile or StudentProfileFactory(
        user=VerifiedUserFactory(role='student'), grade=10,
    )
    client = APIClient()
    client.force_authenticate(profile.user)
    return client, profile


def goal_payload(institution, *, programme=None, kind='primary', priority=1):
    payload = {
        'institution': institution.pk,
        'kind': kind,
        'priority': priority,
    }
    if programme is not None:
        payload['programme'] = programme.pk
    return payload


def nested_keys(value):
    if isinstance(value, dict):
        return set(value) | {
            key for child in value.values() for key in nested_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in nested_keys(child)}
    return set()


@pytest.mark.django_db
def test_catalogue_endpoints_require_auth_and_expose_provenance_without_decisions():
    """Catches public catalogue disclosure, missing audit fields, or admission decisions."""
    institution = InstitutionFactory()
    programme = ProgrammeFactory(institution=institution)
    ProgrammeSubjectReferenceFactory(programme=programme)
    HistoricalAdmissionReferenceFactory(programme=programme)

    assert APIClient().get(INSTITUTIONS_URL).status_code == 401
    client, _ = auth_client()
    institution_data = client.get(INSTITUTIONS_URL).data['data'][0]
    programme_data = client.get(f'{PROGRAMMES_URL}{programme.pk}/').data['data']

    assert PROVENANCE <= institution_data.keys()
    assert PROVENANCE <= programme_data.keys()
    assert PROVENANCE <= programme_data['subject_references'][0].keys()
    historical = programme_data['historical_admission_references'][0]
    assert PROVENANCE <= historical.keys()
    assert historical['reference_status'] == 'historical_reference'
    assert historical['reference_only'] is True
    forbidden = {'eligibility', 'eligible', 'ineligible', 'probability', 'cbc_score'}
    assert not forbidden.intersection(nested_keys(programme_data))


@pytest.mark.django_db
def test_catalogue_search_and_filters_are_bounded_and_exactly_scoped():
    """Catches unbounded responses or filters leaking unrelated catalogue records."""
    wanted = InstitutionFactory(name='Kisii University', county='Kisii')
    other = InstitutionFactory(name='Nairobi Institute', county='Nairobi')
    wanted_programme = ProgrammeFactory(institution=wanted, name='Bachelor of Education')
    ProgrammeFactory(institution=other, name='Bachelor of Education')
    for index in range(105):
        InstitutionFactory(name=f'College {index:03d}')
    client, _ = auth_client()

    searched = client.get(INSTITUTIONS_URL, {'search': 'Kisii', 'county': 'Kisii'})
    programmes = client.get(PROGRAMMES_URL, {'institution': wanted.pk, 'search': 'Education'})
    bounded = client.get(INSTITUTIONS_URL)

    assert [item['id'] for item in searched.data['data']] == [wanted.pk]
    assert [item['id'] for item in programmes.data['data']] == [wanted_programme.pk]
    assert len(bounded.data['data']) == 100


@pytest.mark.django_db
def test_goal_crud_is_learner_owned_and_supports_institution_only():
    """Catches forced programme selection, cross-learner disclosure, or destructive ownership gaps."""
    institution = InstitutionFactory()
    owner_client, owner = auth_client()
    created = owner_client.post(GOALS_URL, goal_payload(institution), format='json')
    assert created.status_code == 201
    assert created.data['data']['programme'] is None
    assert created.data['data']['created_by'] == owner.user_id

    other_client, _ = auth_client()
    goal_id = created.data['data']['id']
    assert other_client.get(GOALS_URL).data['data'] == []
    assert other_client.patch(f'{GOALS_URL}{goal_id}/', {'priority': 2}, format='json').status_code == 404
    assert other_client.delete(f'{GOALS_URL}{goal_id}/').status_code == 404

    assert owner_client.delete(f'{GOALS_URL}{goal_id}/').status_code == 200
    assert not LearnerEducationGoal.objects.filter(pk=goal_id).exists()


@pytest.mark.django_db
def test_goal_rejects_programme_from_another_institution():
    """Catches goals whose selected programme does not belong to the selected institution."""
    institution = InstitutionFactory()
    programme = ProgrammeFactory()
    client, _ = auth_client()
    response = client.post(
        GOALS_URL, goal_payload(institution, programme=programme), format='json'
    )
    assert response.status_code == 400
    assert 'institution' in str(response.data['message']).casefold()


@pytest.mark.django_db
def test_goal_limits_one_primary_and_two_distinct_alternative_slots():
    """Catches application-only goal cardinality or a third alternative slot."""
    client, profile = auth_client()
    institutions = [InstitutionFactory() for _ in range(5)]
    assert client.post(GOALS_URL, goal_payload(institutions[0]), format='json').status_code == 201
    assert client.post(GOALS_URL, goal_payload(institutions[1]), format='json').status_code == 400
    for slot in (1, 2):
        response = client.post(
            GOALS_URL,
            goal_payload(institutions[slot], kind='alternative', priority=slot),
            format='json',
        )
        assert response.status_code == 201
    third = client.post(
        GOALS_URL,
        goal_payload(institutions[3], kind='alternative', priority=3),
        format='json',
    )
    assert third.status_code == 400

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            LearnerEducationGoalFactory(
                learner=profile,
                institution=institutions[4],
                created_by=profile.user,
            )


@pytest.mark.django_db
def test_non_learner_cannot_manage_education_goals():
    """Catches role-only callers managing a learner-owned resource."""
    client = APIClient()
    client.force_authenticate(VerifiedUserFactory(role='counselor'))
    assert client.get(GOALS_URL).status_code == 403
    assert client.post(GOALS_URL, {}, format='json').status_code == 403


def write_catalogue(path, rows):
    fields = [
        'record_type', 'source_scope', 'external_key', 'parent_external_key',
        'name', 'code', 'institution_type', 'county', 'website_url',
        'description', 'subject_code', 'subject_name', 'mapping_kind',
        'requirement_summary', 'source_url', 'education_framework',
        'admission_cycle', 'effective_date', 'verification_status',
    ]
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def catalogue_rows():
    common = {
        'source_scope': 'kuccps-2025',
        'source_url': 'https://students.kuccps.net/',
        'education_framework': 'KCSE',
        'admission_cycle': '2025/2026',
        'effective_date': '2025-03-01',
        'verification_status': 'historical',
    }
    return [
        {**common, 'record_type': 'institution', 'external_key': 'UON',
         'name': 'University of Nairobi', 'institution_type': 'university',
         'county': 'Nairobi', 'website_url': 'https://uonbi.ac.ke/'},
        {**common, 'record_type': 'programme', 'external_key': 'UON-CS',
         'parent_external_key': 'UON', 'name': 'BSc Computer Science',
         'code': 'BSC-CS', 'description': 'Programme catalogue entry.'},
        {**common, 'record_type': 'programme_subject_reference',
         'external_key': 'UON-CS-MAT', 'parent_external_key': 'UON-CS',
         'subject_code': 'MAT', 'subject_name': 'Mathematics',
         'mapping_kind': 'historical_requirement',
         'description': 'Historical subject reference only.'},
        {**common, 'record_type': 'historical_admission_reference',
         'external_key': 'UON-CS-HIST', 'parent_external_key': 'UON-CS',
         'requirement_summary': 'Historical KCSE reference only.'},
    ]


@pytest.mark.django_db
def test_csv_import_is_idempotent_updates_changed_rows_and_dry_run_writes_nothing(tmp_path):
    """Catches duplicate imports, ignored catalogue changes, or dry-run writes."""
    path = tmp_path / 'catalogue.csv'
    rows = catalogue_rows()
    write_catalogue(path, rows)
    call_command('import_tertiary_catalogue', str(path))
    call_command('import_tertiary_catalogue', str(path))
    assert Institution.objects.count() == 1
    assert Programme.objects.count() == 1
    assert ProgrammeSubjectReference.objects.count() == 1
    assert HistoricalAdmissionReference.objects.count() == 1

    rows[0]['name'] = 'University of Nairobi (updated)'
    write_catalogue(path, rows)
    call_command('import_tertiary_catalogue', str(path))
    assert Institution.objects.get().name == 'University of Nairobi (updated)'

    rows[0]['name'] = 'Dry-run name'
    write_catalogue(path, rows)
    call_command('import_tertiary_catalogue', str(path), dry_run=True)
    assert Institution.objects.get().name == 'University of Nairobi (updated)'


@pytest.mark.django_db
def test_csv_import_validates_all_provenance_before_atomic_writes(tmp_path):
    """Catches partial writes when a later row is malformed or missing provenance."""
    path = tmp_path / 'bad.csv'
    rows = catalogue_rows()
    rows[-1]['source_url'] = ''
    write_catalogue(path, rows)

    with pytest.raises(CommandError, match='source_url'):
        call_command('import_tertiary_catalogue', str(path))
    assert Institution.objects.count() == 0
    assert Programme.objects.count() == 0


def test_reference_models_reject_decision_fields_and_limit_mapping_kinds():
    """Catches accidental admission-decision schema and unsupported mapping semantics."""
    model_fields = {
        field.name
        for model in (Institution, Programme, ProgrammeSubjectReference, HistoricalAdmissionReference)
        for field in model._meta.get_fields()
    }
    assert not {'eligibility', 'eligible', 'ineligible', 'probability', 'cbc_score'} & model_fields
    mapping = ProgrammeSubjectReference._meta.get_field('mapping_kind')
    assert {value for value, _label in mapping.choices} == {
        'historical_requirement', 'exploratory_alignment',
    }


@pytest.mark.django_db
def test_historical_admission_rows_are_database_labeled_kcse_references():
    """Catches historical admission rows being persisted as current or under CBE."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            HistoricalAdmissionReferenceFactory(
                education_framework='CBE',
                verification_status='verified',
            )
