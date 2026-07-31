from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_studentprofile_school_membership_status'),
        ('students', '0005_correct_grade10_catalogue'),
    ]

    operations = [
        migrations.AddField(
            model_name='cbcgrade',
            name='source',
            field=models.CharField(
                choices=[('learner', 'Learner'), ('school', 'School')],
                default='learner',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cbcgrade',
            name='verified_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='verified_cbc_grades',
                to='accounts.user',
            ),
        ),
        migrations.AddConstraint(
            model_name='cbcgrade',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(
                        ('verified_at__isnull', True),
                        ('verified_by__isnull', True),
                    )
                    | models.Q(
                        ('verified_at__isnull', False),
                        ('verified_by__isnull', False),
                    )
                ),
                name='students_grade_verification_pair',
            ),
        ),
    ]
