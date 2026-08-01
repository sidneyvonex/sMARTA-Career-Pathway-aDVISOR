import django.core.validators
from django.db import migrations, models


SUPPORTED_GRADES = (
    (9, 'Grade 9'),
    (10, 'Grade 10'),
    (11, 'Grade 11'),
    (12, 'Grade 12'),
)


def _continuity_code(subject):
    grade_suffix = str(subject.grade)
    if subject.code.endswith(grade_suffix):
        return subject.code[: -len(grade_suffix)]
    return subject.code


def backfill_longitudinal_identity(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')
    StudentSubject = apps.get_model('students', 'StudentSubject')
    CBCGrade = apps.get_model('students', 'CBCGrade')

    continuity_by_subject = {}
    for subject in Subject.objects.all().iterator():
        continuity_code = _continuity_code(subject)
        Subject.objects.filter(pk=subject.pk).update(
            continuity_code=continuity_code,
        )
        continuity_by_subject[subject.pk] = continuity_code

    for enrollment in StudentSubject.objects.all().iterator():
        earliest_evidence_year = (
            CBCGrade.objects.filter(student_subject_id=enrollment.pk)
            .order_by('year', 'term', 'pk')
            .values_list('year', flat=True)
            .first()
        )
        academic_year = earliest_evidence_year or enrollment.created_at.year
        StudentSubject.objects.filter(pk=enrollment.pk).update(
            continuity_code=continuity_by_subject[enrollment.subject_id],
            academic_grade=enrollment.subject.grade,
            academic_year=academic_year,
            is_active=True,
            ended_at=None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0012_expand_student_profile_grades'),
        ('students', '0009_version_assessment_evidence'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='continuity_code',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='subject',
            name='grade',
            field=models.IntegerField(
                choices=SUPPORTED_GRADES,
                validators=[
                    django.core.validators.MinValueValidator(9),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.AddField(
            model_name='studentsubject',
            name='continuity_code',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='studentsubject',
            name='academic_grade',
            field=models.IntegerField(
                blank=True,
                choices=SUPPORTED_GRADES,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(9),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.AddField(
            model_name='studentsubject',
            name='academic_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentsubject',
            name='ended_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='studentsubject',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            backfill_longitudinal_identity,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='subject',
            name='continuity_code',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='continuity_code',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='academic_grade',
            field=models.IntegerField(
                choices=SUPPORTED_GRADES,
                validators=[
                    django.core.validators.MinValueValidator(9),
                    django.core.validators.MaxValueValidator(12),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='academic_year',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterUniqueTogether(
            name='studentsubject',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='studentsubject',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=(
                    'student_profile',
                    'continuity_code',
                    'academic_grade',
                ),
                name='students_active_enroll_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentsubject',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(is_active=True, ended_at__isnull=True)
                    | models.Q(is_active=False, ended_at__isnull=False)
                ),
                name='students_enrollment_state_ck',
            ),
        ),
    ]
