import csv
from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, connection, transaction
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
    reference = HistoricalAdmissionReferenceFactory()
    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'UPDATE tertiary_historicaladmissionreference '
                'SET education_framework = %s, verification_status = %s WHERE id = %s',
                ['CBE', 'verified', reference.pk],
            )


@pytest.mark.django_db
def test_subject_mapping_kinds_are_restricted_by_the_database():
    """Catches bulk or racing writes bypassing the two advisory mapping semantics."""
    reference = ProgrammeSubjectReferenceFactory()
    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'UPDATE tertiary_programmesubjectreference SET mapping_kind = %s '
                'WHERE id = %s',
                ['required_for_admission', reference.pk],
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('source_scope', ''),
        ('external_key', ''),
        ('source_url', ''),
        ('education_framework', ''),
        ('admission_cycle', ''),
        ('verification_status', 'invented'),
    ],
)
def test_catalogue_save_rejects_missing_or_unknown_provenance(field, value):
    """Catches ordinary model saves bypassing mandatory provenance semantics."""
    institution = InstitutionFactory.build(**{field: value})

    with pytest.raises(ValidationError):
        institution.save()


@pytest.mark.django_db
def test_catalogue_database_constraints_reject_provenance_bypass():
    """Catches direct SQL bypass of non-empty provenance and finite status checks."""
    institution = InstitutionFactory()

    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'UPDATE tertiary_institution SET source_url = %s WHERE id = %s',
                ['', institution.pk],
            )

    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'UPDATE tertiary_institution SET verification_status = %s WHERE id = %s',
                ['invented', institution.pk],
            )


@pytest.mark.django_db
def test_catalogue_manager_rejects_protected_bulk_write_bypasses():
    """Catches ORM bulk paths silently rewriting sourced identity or semantics."""
    institution = InstitutionFactory()

    with pytest.raises(ValidationError, match='validated instance saves'):
        Institution.objects.filter(pk=institution.pk).update(source_scope='other')
    with pytest.raises(ValidationError, match='validated instance saves'):
        Institution.objects.filter(pk=institution.pk).update(name='Bypassed identity')
    institution.source_url = 'https://example.ac.ke/changed/'
    with pytest.raises(ValidationError, match='validated instance saves'):
        Institution.objects.bulk_update([institution], ['source_url'])
    with pytest.raises(ValidationError, match='validated instance saves'):
        Institution.objects.bulk_create([InstitutionFactory.build()])


@pytest.mark.django_db
def test_historical_subject_reference_is_always_historical_kcse():
    """Catches historical requirements being relabelled as current CBE semantics."""
    programme = ProgrammeFactory()
    reference = ProgrammeSubjectReferenceFactory.build(
        programme=programme,
        mapping_kind=ProgrammeSubjectReference.KIND_HISTORICAL_REQUIREMENT,
        education_framework='CBE',
        verification_status='verified',
    )
    with pytest.raises(ValidationError):
        reference.save()

    with pytest.raises(IntegrityError):
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO tertiary_programmesubjectreference '
                '(source_scope, external_key, source_url, education_framework, '
                'admission_cycle, effective_date, verification_status, created_at, '
                'updated_at, programme_id, subject_code, subject_name, mapping_kind, notes) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, '
                'CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)',
                [
                    programme.source_scope, 'BAD-HIST', programme.source_url, 'CBE',
                    programme.admission_cycle, programme.effective_date, 'verified',
                    programme.pk, 'MAT', 'Mathematics', 'historical_requirement', '',
                ],
            )


@pytest.mark.django_db
def test_exploratory_subject_reference_keeps_its_parent_framework_and_cycle():
    """Catches exploratory alignment being needlessly forced to KCSE/historical."""
    institution = InstitutionFactory(
        source_scope='cbe-2026', education_framework='CBE',
        admission_cycle='2026/2027', verification_status='verified',
    )
    programme = ProgrammeFactory(
        institution=institution, source_scope='cbe-2026', education_framework='CBE',
        admission_cycle='2026/2027', verification_status='verified',
    )
    reference = ProgrammeSubjectReferenceFactory(
        programme=programme, source_scope='cbe-2026', education_framework='CBE',
        admission_cycle='2026/2027', verification_status='verified',
        mapping_kind=ProgrammeSubjectReference.KIND_EXPLORATORY_ALIGNMENT,
    )

    assert reference.pk is not None


@pytest.mark.django_db
def test_catalogue_children_reject_cross_source_framework_or_cycle_parents():
    """Catches nested catalogue rows combining contradictory source releases."""
    institution = InstitutionFactory()
    mismatches = [
        {'source_scope': 'other-source'},
        {'education_framework': 'CBE'},
        {'admission_cycle': '2026/2027'},
    ]
    for override in mismatches:
        with pytest.raises(ValidationError):
            ProgrammeFactory(institution=institution, **override)

    programme = ProgrammeFactory(institution=institution)
    with pytest.raises(ValidationError):
        ProgrammeSubjectReferenceFactory(programme=programme, source_scope='other-source')
    with pytest.raises(ValidationError):
        HistoricalAdmissionReferenceFactory(programme=programme, admission_cycle='2024/2025')


@pytest.mark.django_db
def test_catalogue_child_status_cannot_exceed_parent_but_dates_need_not_match():
    """Catches accidental status equality or a child claiming stronger source authority."""
    historical_parent = InstitutionFactory(verification_status='historical')
    with pytest.raises(ValidationError, match='more authoritative'):
        ProgrammeFactory(institution=historical_parent, verification_status='verified')

    verified_parent = InstitutionFactory(
        verification_status='verified', effective_date=date(2026, 1, 1)
    )
    programme = ProgrammeFactory(
        institution=verified_parent,
        verification_status='historical',
        effective_date=date(2025, 3, 1),
    )
    assert programme.pk is not None


@pytest.mark.django_db
def test_catalogue_parent_reassignment_and_referenced_provenance_changes_are_safe():
    """Catches admin/model edits silently invalidating existing descendants."""
    institution = InstitutionFactory()
    programme = ProgrammeFactory(institution=institution)
    ProgrammeSubjectReferenceFactory(programme=programme)
    other = InstitutionFactory()

    programme.institution = other
    programme.source_scope = other.source_scope
    with pytest.raises(ValidationError, match='cannot be changed once referenced'):
        programme.save()

    institution.education_framework = 'CBE'
    with pytest.raises(ValidationError, match='cannot be changed once referenced'):
        institution.save()

    with pytest.raises(ValidationError, match='validated instance saves'):
        Programme.objects.filter(pk=programme.pk).update(institution=other)


@pytest.mark.django_db
def test_child_save_reloads_a_parent_changed_after_the_child_was_prepared():
    """Catches a stale parent object winning a concurrent sourced-release change."""
    institution = InstitutionFactory()
    candidate_programme = ProgrammeFactory.build(institution=institution)
    changed_institution = Institution.objects.get(pk=institution.pk)
    changed_institution.source_scope = 'new-release'
    changed_institution.save()

    with pytest.raises(ValidationError, match='source release'):
        candidate_programme.save()

    stable_institution = InstitutionFactory(verification_status='verified')
    programme = ProgrammeFactory(
        institution=stable_institution, verification_status='historical'
    )
    candidate_reference = ProgrammeSubjectReferenceFactory.build(
        programme=programme, verification_status='historical'
    )
    changed_programme = Programme.objects.get(pk=programme.pk)
    changed_programme.verification_status = 'unavailable'
    changed_programme.save()

    with pytest.raises(ValidationError, match='more authoritative'):
        candidate_reference.save()


@pytest.mark.django_db
def test_goal_choices_are_distinct_across_slots_and_database_safe():
    """Catches the same institution-only or programme choice occupying multiple slots."""
    client, profile = auth_client()
    institution = InstitutionFactory()
    programme = ProgrammeFactory(institution=institution)

    assert client.post(GOALS_URL, goal_payload(institution), format='json').status_code == 201
    duplicate_institution = client.post(
        GOALS_URL,
        goal_payload(institution, kind='alternative', priority=1),
        format='json',
    )
    assert duplicate_institution.status_code == 400
    assert duplicate_institution.data['message'] == (
        'That institution or programme is already saved as another education goal.'
    )

    programme_goal = LearnerEducationGoalFactory(
        learner=profile, institution=institution, programme=programme,
        kind='alternative', priority=1, created_by=profile.user,
    )
    assert programme_goal.choice_identity != LearnerEducationGoal.objects.get(
        learner=profile, kind='primary'
    ).choice_identity

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            LearnerEducationGoalFactory(
                learner=profile, institution=institution, programme=programme,
                kind='alternative', priority=2, created_by=profile.user,
            )

    other_client, _ = auth_client()
    assert other_client.post(
        GOALS_URL,
        goal_payload(institution, programme=programme),
        format='json',
    ).status_code == 201
    duplicate_programme = other_client.post(
        GOALS_URL,
        goal_payload(
            institution, programme=programme, kind='alternative', priority=1
        ),
        format='json',
    )
    assert duplicate_programme.status_code == 400
    assert duplicate_programme.data['message'] == (
        'That institution or programme is already saved as another education goal.'
    )


@pytest.mark.django_db
def test_goal_update_recomputes_identity_and_rejects_choice_conflict():
    """Catches PATCH retaining stale identity or merging two distinct slots into one choice."""
    client, _profile = auth_client()
    first = InstitutionFactory()
    second = InstitutionFactory()
    created_primary = client.post(GOALS_URL, goal_payload(first), format='json').data['data']
    created_alternative = client.post(
        GOALS_URL,
        goal_payload(second, kind='alternative', priority=1),
        format='json',
    ).data['data']

    conflict = client.patch(
        f"{GOALS_URL}{created_alternative['id']}/",
        {'institution': first.pk},
        format='json',
    )
    assert conflict.status_code == 400
    assert conflict.data['message'] == (
        'That institution or programme is already saved as another education goal.'
    )
    assert LearnerEducationGoal.objects.get(pk=created_primary['id']).institution_id == first.pk
    assert LearnerEducationGoal.objects.get(pk=created_alternative['id']).institution_id == second.pk


@pytest.mark.django_db
def test_goal_partial_model_save_persists_recomputed_choice_identity():
    """Catches update_fields persisting a new choice with its old unique identity."""
    goal = LearnerEducationGoalFactory()
    replacement = InstitutionFactory()

    goal.institution = replacement
    goal.save(update_fields=['institution'])
    goal.refresh_from_db()

    assert goal.choice_identity == (
        f'institution:{replacement.pk}:programme:none'
    )
    with pytest.raises(ValidationError, match='validated instance saves'):
        LearnerEducationGoal.objects.filter(pk=goal.pk).update(kind='alternative')


@pytest.mark.django_db
def test_goal_validation_returns_clean_error_envelope():
    """Catches DRF ErrorDetail dictionaries being exposed as user-facing strings."""
    institution = InstitutionFactory()
    programme = ProgrammeFactory()
    client, _ = auth_client()

    response = client.post(
        GOALS_URL, goal_payload(institution, programme=programme), format='json'
    )

    assert response.status_code == 400
    assert response.data == {
        'data': None,
        'error': True,
        'message': 'The programme must belong to the selected institution.',
    }


@pytest.mark.django_db
def test_student_without_profile_gets_same_non_disclosing_404_for_all_goal_writes():
    """Catches profile lookup exceptions leaking as 500s or model details."""
    user = VerifiedUserFactory(role='student')
    client = APIClient()
    client.force_authenticate(user)
    other_goal = LearnerEducationGoalFactory()

    responses = [
        client.get(GOALS_URL),
        client.post(GOALS_URL, {}, format='json'),
        client.patch(f'{GOALS_URL}{other_goal.pk}/', {}, format='json'),
        client.delete(f'{GOALS_URL}{other_goal.pk}/'),
    ]
    assert [response.status_code for response in responses] == [404, 404, 404, 404]
    assert {
        response.data['message'] for response in responses
    } == {'That item no longer exists.'}


@pytest.mark.django_db
def test_csv_rejects_schema_width_quote_and_length_errors_before_writes(tmp_path):
    """Catches parser crashes, backend-dependent truncation, and partial late-row imports."""
    valid_path = tmp_path / 'valid.csv'
    rows = catalogue_rows()
    write_catalogue(valid_path, rows)
    header, first, *_rest = valid_path.read_text().splitlines()

    cases = {
        'header.csv': f'{header},unexpected\n{first},\n',
        'overflow.csv': f'{header}\n{first},EXTRA\n',
        'underflow.csv': f"{header}\n{','.join(first.split(',')[:-1])}\n",
        'quote.csv': f'{header}\n"unterminated\n',
    }
    for filename, contents in cases.items():
        path = tmp_path / filename
        path.write_text(contents, encoding='utf-8')
        with pytest.raises(CommandError):
            call_command('import_tertiary_catalogue', str(path))
        assert Institution.objects.count() == 0

    invalid_encoding = tmp_path / 'invalid-encoding.csv'
    invalid_encoding.write_bytes(b'\xff\xfe\x00')
    with pytest.raises(CommandError, match='Malformed CSV'):
        call_command('import_tertiary_catalogue', str(invalid_encoding))

    rows[-1]['requirement_summary'] = 'valid late row'
    rows[0]['name'] = 'N' * 241
    write_catalogue(valid_path, rows)
    with pytest.raises(CommandError, match='name'):
        call_command('import_tertiary_catalogue', str(valid_path))
    assert Institution.objects.count() == 0


@pytest.mark.django_db
def test_csv_identity_is_type_aware_and_same_type_duplicates_are_rejected(tmp_path):
    """Catches global cross-type key rejection or same-model duplicate ambiguity."""
    path = tmp_path / 'catalogue.csv'
    rows = catalogue_rows()
    rows[1]['external_key'] = rows[0]['external_key']
    rows[2]['parent_external_key'] = rows[1]['external_key']
    rows[3]['parent_external_key'] = rows[1]['external_key']
    write_catalogue(path, rows)

    call_command('import_tertiary_catalogue', str(path))
    assert Institution.objects.get().external_key == 'UON'
    assert Programme.objects.get().external_key == 'UON'

    rows.append({**rows[0]})
    rows[-1]['name'] = 'Duplicate institution'
    write_catalogue(path, rows)
    with pytest.raises(CommandError, match='duplicate'):
        call_command('import_tertiary_catalogue', str(path), dry_run=True)
