from decimal import Decimal

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


PILOT_LEVELS = (
    ('EE1', 'Exceeding Expectation - Level 1', 8),
    ('EE2', 'Exceeding Expectation - Level 2', 7),
    ('ME1', 'Meeting Expectation - Level 1', 6),
    ('ME2', 'Meeting Expectation - Level 2', 5),
    ('AE1', 'Approaching Expectation - Level 1', 4),
    ('AE2', 'Approaching Expectation - Level 2', 3),
    ('BE1', 'Below Expectation - Level 1', 2),
    ('BE2', 'Below Expectation - Level 2', 1),
)

PILOT_FRAMEWORKS = (
    (
        'CBC-GRADE-9-LEGACY',
        'Grade 9 CBC Legacy Pilot Assessment Framework',
        'junior_school',
    ),
    (
        'CBC-SENIOR-SCHOOL',
        'Senior School CBC Pilot Assessment Framework',
        'senior_school',
    ),
)


def seed_pilot_framework_and_backfill_grades(apps, schema_editor):
    AssessmentFramework = apps.get_model('students', 'AssessmentFramework')
    PerformanceLevelDefinition = apps.get_model(
        'students', 'PerformanceLevelDefinition'
    )
    CBCGrade = apps.get_model('students', 'CBCGrade')

    frameworks = {}
    for framework_code, title, scope in PILOT_FRAMEWORKS:
        framework, _created = AssessmentFramework.objects.update_or_create(
            code=framework_code,
            version='pilot-2026',
            defaults={
                'title': title,
                'scope': scope,
                'source_url': 'https://kicd.ac.ke/curriculum-reform/',
                'effective_date': '2026-01-01',
                'status': 'active',
            },
        )
        frameworks[scope] = framework
        for code, label, rank in PILOT_LEVELS:
            PerformanceLevelDefinition.objects.update_or_create(
                framework=framework,
                code=code,
                defaults={
                    'label': label,
                    'description': label,
                    'rank': rank,
                    'official_min_score': None,
                    'official_max_score': None,
                    'official_points': None,
                },
            )

    grades = CBCGrade.objects.select_related('student_subject__subject')
    for grade in grades.iterator():
        grade.academic_grade = grade.student_subject.subject.grade
        scope = 'junior_school' if grade.academic_grade == 9 else 'senior_school'
        grade.framework_id = frameworks[scope].pk
        # Historical verifier membership is mutable and does not establish
        # which school verified this grade. Preserve unknown provenance as null.
        grade.verified_school_id = None
        grade.save(
            update_fields=['framework', 'academic_grade', 'verified_school']
        )


def remove_pilot_framework(apps, schema_editor):
    AssessmentFramework = apps.get_model('students', 'AssessmentFramework')
    CBCGrade = apps.get_model('students', 'CBCGrade')

    CBCGrade.objects.update(
        framework=None,
        academic_grade=None,
        verified_school=None,
    )
    AssessmentFramework.objects.filter(
        code__in=['CBC-GRADE-9-LEGACY', 'CBC-SENIOR-SCHOOL'],
        version='pilot-2026',
    ).delete()


class Migration(migrations.Migration):
    dependencies = [('students', '0008_full_catalogue_subjects')]

    operations = [
        migrations.CreateModel(
            name='AssessmentFramework',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('code', models.CharField(max_length=80)),
                ('version', models.CharField(max_length=40)),
                ('title', models.CharField(max_length=200)),
                ('scope', models.CharField(max_length=40)),
                ('source_url', models.URLField(max_length=500)),
                ('effective_date', models.DateField()),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('draft', 'Draft'),
                            ('active', 'Active'),
                            ('retired', 'Retired'),
                        ],
                        default='draft',
                        max_length=20,
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['scope', '-effective_date', 'code', 'version'],
            },
        ),
        migrations.AddConstraint(
            model_name='assessmentframework',
            constraint=models.UniqueConstraint(
                fields=('code', 'version'),
                name='students_framework_code_version_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='assessmentframework',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'active')),
                fields=('scope',),
                name='students_active_framework_scope_uniq',
            ),
        ),
        migrations.CreateModel(
            name='PerformanceLevelDefinition',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('code', models.CharField(max_length=10)),
                ('label', models.CharField(max_length=120)),
                ('description', models.TextField()),
                (
                    'rank',
                    models.PositiveSmallIntegerField(
                        validators=[django.core.validators.MinValueValidator(1)]
                    ),
                ),
                (
                    'official_min_score',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=7,
                        null=True,
                    ),
                ),
                (
                    'official_max_score',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=7,
                        null=True,
                    ),
                ),
                (
                    'official_points',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=7,
                        null=True,
                    ),
                ),
                (
                    'framework',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='level_definitions',
                        to='students.assessmentframework',
                    ),
                ),
            ],
            options={'ordering': ['-rank', 'code']},
        ),
        migrations.AddConstraint(
            model_name='performanceleveldefinition',
            constraint=models.UniqueConstraint(
                fields=('framework', 'code'),
                name='students_level_framework_code_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='performanceleveldefinition',
            constraint=models.UniqueConstraint(
                fields=('framework', 'rank'),
                name='students_level_framework_rank_uniq',
            ),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='framework',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grades',
                to='students.assessmentframework',
            ),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='academic_grade',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (9, 'Grade 9'),
                    (10, 'Grade 10'),
                    (11, 'Grade 11'),
                    (12, 'Grade 12'),
                ],
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(9),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='raw_score',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=7,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='verified_school',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='verified_cbc_grades',
                to='accounts.school',
            ),
        ),
        migrations.RunPython(
            seed_pilot_framework_and_backfill_grades,
            remove_pilot_framework,
        ),
        migrations.AlterField(
            model_name='cbcgrade',
            name='framework',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grades',
                to='students.assessmentframework',
            ),
        ),
        migrations.AlterField(
            model_name='cbcgrade',
            name='academic_grade',
            field=models.IntegerField(
                choices=[
                    (9, 'Grade 9'),
                    (10, 'Grade 10'),
                    (11, 'Grade 11'),
                    (12, 'Grade 12'),
                ],
                validators=[
                    django.core.validators.MinValueValidator(9),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
    ]
