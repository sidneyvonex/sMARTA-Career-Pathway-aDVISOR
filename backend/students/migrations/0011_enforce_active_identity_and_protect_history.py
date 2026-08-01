from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError
from django.db.models import Count
import django.db.models.deletion


def backfill_active_identity(apps, schema_editor):
    StudentSubject = apps.get_model('students', 'StudentSubject')

    has_duplicate = (
        StudentSubject.objects.filter(is_active=True)
        .values('student_profile_id', 'continuity_code', 'academic_grade')
        .annotate(total=Count('pk'))
        .filter(total__gt=1)
        .exists()
    )
    if has_duplicate:
        raise RuntimeError(
            'Resolve duplicate active subject enrollments before applying '
            'students.0011; no enrollment was archived automatically.'
        )

    for enrollment in StudentSubject.objects.all().iterator():
        active_identity = (
            f'{enrollment.continuity_code}:{enrollment.academic_grade}'
            if enrollment.is_active
            else None
        )
        StudentSubject.objects.filter(pk=enrollment.pk).update(
            active_identity=active_identity,
        )


def guard_incompatible_reverse(apps, schema_editor):
    StudentSubject = apps.get_model('students', 'StudentSubject')

    # The preceding schema cannot represent archived lifecycle state. Never
    # reactivate or discard that history implicitly during a rollback. An
    # operator must retain this migration or explicitly reconcile/export it.
    if StudentSubject.objects.filter(is_active=False).exists():
        raise IrreversibleError(
            'Cannot reverse longitudinal enrollment safety while archived '
            'enrollment history exists; retain this migration or explicitly '
            'reconcile the historical rows first.'
        )


class Migration(migrations.Migration):
    dependencies = [
        ('students', '0010_preserve_longitudinal_subject_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentsubject',
            name='active_identity',
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=96,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='subject',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='enrollments',
                to='students.subject',
            ),
        ),
        migrations.AlterField(
            model_name='cbcgrade',
            name='student_subject',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grades',
                to='students.studentsubject',
            ),
        ),
        migrations.RunPython(
            backfill_active_identity,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name='studentsubject',
            name='students_active_enroll_uniq',
        ),
        migrations.AddConstraint(
            model_name='studentsubject',
            constraint=models.UniqueConstraint(
                fields=('student_profile', 'active_identity'),
                name='students_active_identity_uniq',
            ),
        ),
        # This is deliberately last so its reverse runs before any schema
        # operation and can preserve valid archived/re-enrolled history.
        migrations.RunPython(
            migrations.RunPython.noop,
            guard_incompatible_reverse,
        ),
    ]
