from django.db import migrations, models
from django.db.models import F, Value
from django.db.models.functions import Length, Replace
from django.db.models.lookups import GreaterThan


PROVENANCE_FIELDS = (
    'source_scope', 'external_key', 'source_url', 'education_framework',
    'admission_cycle',
)
VALID_STATUSES = {'verified', 'historical', 'unavailable'}
AUTHORITY = {'unavailable': 0, 'historical': 1, 'verified': 2}
# Frozen copy of tertiary.models.SEMANTIC_WHITESPACE: Unicode White_Space plus
# the four additional C0 separators recognized by Python str.strip/isspace.
SEMANTIC_WHITESPACE = (
    '\t', '\n', '\v', '\f', '\r', '\x1c', '\x1d', '\x1e', '\x1f', ' ',
    '\x85', '\xa0', '\u1680', '\u2000', '\u2001', '\u2002', '\u2003',
    '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200a',
    '\u2028', '\u2029', '\u202f', '\u205f', '\u3000',
)


def has_semantic_content(value):
    return (
        isinstance(value, str)
        and any(character not in SEMANTIC_WHITESPACE for character in value)
    )


def parent_is_coherent(child, parent):
    return (
        child.source_scope == parent.source_scope
        and child.education_framework == parent.education_framework
        and child.admission_cycle == parent.admission_cycle
        and AUTHORITY.get(child.verification_status, -1)
        <= AUTHORITY.get(parent.verification_status, -1)
    )


def preflight_catalogue_integrity(apps, _schema_editor):
    model_names = (
        'Institution', 'Programme', 'ProgrammeSubjectReference',
        'HistoricalAdmissionReference',
    )
    invalid = []
    for model_name in model_names:
        Model = apps.get_model('tertiary', model_name)
        for record in Model.objects.all().iterator():
            missing = [
                field for field in PROVENANCE_FIELDS
                if not has_semantic_content(getattr(record, field))
            ]
            if missing or record.verification_status not in VALID_STATUSES:
                invalid.append(f'{model_name} {record.pk}')
    if invalid:
        joined = ', '.join(invalid[:10])
        raise RuntimeError(
            'Cannot enforce tertiary catalogue provenance; repair invalid records first: '
            f'{joined}.'
        )

    Institution = apps.get_model('tertiary', 'Institution')
    Programme = apps.get_model('tertiary', 'Programme')
    SubjectReference = apps.get_model('tertiary', 'ProgrammeSubjectReference')
    HistoricalReference = apps.get_model('tertiary', 'HistoricalAdmissionReference')
    contradictions = []
    for institution in Institution.objects.all().iterator():
        if institution.institution_type not in {'university', 'college', 'tvet', 'other'}:
            contradictions.append(f'Institution {institution.pk}')
    for programme in Programme.objects.select_related('institution').iterator():
        if not parent_is_coherent(programme, programme.institution):
            contradictions.append(f'Programme {programme.pk}')
    for reference in SubjectReference.objects.select_related('programme').iterator():
        invalid_historical = (
            reference.mapping_kind == 'historical_requirement'
            and (
                reference.education_framework != 'KCSE'
                or reference.verification_status != 'historical'
            )
        )
        if (
            reference.mapping_kind not in {
                'historical_requirement', 'exploratory_alignment',
            }
            or invalid_historical
            or not parent_is_coherent(reference, reference.programme)
        ):
            contradictions.append(f'ProgrammeSubjectReference {reference.pk}')
    for reference in HistoricalReference.objects.select_related('programme').iterator():
        if (
            reference.education_framework != 'KCSE'
            or reference.verification_status != 'historical'
            or not parent_is_coherent(reference, reference.programme)
        ):
            contradictions.append(f'HistoricalAdmissionReference {reference.pk}')
    if contradictions:
        joined = ', '.join(contradictions[:10])
        raise RuntimeError(
            'Cannot enforce tertiary parent coherence; repair invalid records first: '
            f'{joined}.'
        )

    Goal = apps.get_model('tertiary', 'LearnerEducationGoal')
    seen = {}
    duplicates = []
    mismatches = []
    for goal in Goal.objects.select_related('programme').order_by(
        'learner_id', 'pk'
    ).iterator():
        if (
            goal.programme_id is not None
            and goal.programme.institution_id != goal.institution_id
        ):
            mismatches.append(
                f'goal {goal.pk} programme {goal.programme_id} institution '
                f'{goal.programme.institution_id} selected institution '
                f'{goal.institution_id}'
            )
        programme = goal.programme_id if goal.programme_id is not None else 'none'
        identity = f'institution:{goal.institution_id}:programme:{programme}'
        key = (goal.learner_id, identity)
        if key in seen:
            duplicates.append(
                f'learner {goal.learner_id} goals {seen[key]} and {goal.pk}'
            )
        else:
            seen[key] = goal.pk
    if mismatches:
        joined = '; '.join(mismatches[:10])
        raise RuntimeError(
            'Cannot migrate incoherent education goals; repair these links first: '
            f'{joined}.'
        )
    if duplicates:
        joined = '; '.join(duplicates[:10])
        raise RuntimeError(
            'Cannot migrate duplicate education choices; resolve these learner goals first: '
            f'{joined}.'
        )


def backfill_choice_identity(apps, _schema_editor):
    Goal = apps.get_model('tertiary', 'LearnerEducationGoal')
    for goal in Goal.objects.order_by('pk').iterator():
        programme = goal.programme_id if goal.programme_id is not None else 'none'
        goal.choice_identity = (
            f'institution:{goal.institution_id}:programme:{programme}'
        )
        goal.save(update_fields=['choice_identity'])


def noop(_apps, _schema_editor):
    pass


def clear_choice_identity(apps, _schema_editor):
    Goal = apps.get_model('tertiary', 'LearnerEducationGoal')
    Goal.objects.update(choice_identity=None)


def has_non_whitespace(field):
    expression = F(field)
    for whitespace in SEMANTIC_WHITESPACE:
        expression = Replace(expression, Value(whitespace), Value(''))
    return GreaterThan(Length(expression), 0)


def provenance_constraints(model_name, prefix):
    operations = []
    for field, suffix in (
        ('source_scope', 'scope'),
        ('external_key', 'key'),
        ('source_url', 'url'),
        ('education_framework', 'frame'),
        ('admission_cycle', 'cycle'),
    ):
        operations.append(migrations.AddConstraint(
            model_name=model_name,
            constraint=models.CheckConstraint(
                check=has_non_whitespace(field),
                name=f'{prefix}_{suffix}_nonempty_ck',
            ),
        ))
    operations.append(migrations.AddConstraint(
        model_name=model_name,
        constraint=models.CheckConstraint(
            check=models.Q(verification_status__in=['verified', 'historical', 'unavailable']),
            name=f'{prefix}_verification_ck',
        ),
    ))
    return operations


class Migration(migrations.Migration):

    dependencies = [
        ('tertiary', '0002_programmesubjectreference_tertiary_subj_mapping_kind_ck'),
    ]

    operations = [
        # Preflight precedes DDL so MySQL cannot be left with a partially
        # applied nullable column when existing data requires repair.
        migrations.RunPython(preflight_catalogue_integrity, noop),
        migrations.AddField(
            model_name='learnereducationgoal',
            name='choice_identity',
            field=models.CharField(max_length=80, null=True),
        ),
        migrations.RunPython(backfill_choice_identity, clear_choice_identity),
        migrations.AlterField(
            model_name='learnereducationgoal',
            name='choice_identity',
            field=models.CharField(max_length=80),
        ),
        migrations.AddConstraint(
            model_name='learnereducationgoal',
            constraint=models.UniqueConstraint(
                fields=('learner', 'choice_identity'),
                name='tertiary_goal_learner_choice_uniq',
            ),
        ),
        *provenance_constraints('institution', 'tert_inst'),
        migrations.AddConstraint(
            model_name='institution',
            constraint=models.CheckConstraint(
                check=models.Q(institution_type__in=['university', 'college', 'tvet', 'other']),
                name='tert_inst_type_ck',
            ),
        ),
        *provenance_constraints('programme', 'tert_prog'),
        *provenance_constraints('programmesubjectreference', 'tert_subj'),
        migrations.AddConstraint(
            model_name='programmesubjectreference',
            constraint=models.CheckConstraint(
                check=(
                    ~models.Q(mapping_kind='historical_requirement')
                    | (
                        models.Q(education_framework='KCSE')
                        & models.Q(verification_status='historical')
                    )
                ),
                name='tert_subj_historical_kcse_ck',
            ),
        ),
        *provenance_constraints('historicaladmissionreference', 'tert_hist'),
    ]
