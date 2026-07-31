from django.db import migrations, models


def classify_demonstration_schools(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    School.objects.filter(school_code__startswith='PILOT-').update(
        verification_status='demonstration',
    )


def restore_unverified_schools(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    School.objects.filter(verification_status='demonstration').update(
        verification_status='unverified',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_studentprofile_school_membership_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='source_checked_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='source_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='school',
            name='verification_status',
            field=models.CharField(
                choices=[
                    ('unverified', 'Unverified'),
                    ('verified', 'Verified'),
                    ('demonstration', 'Demonstration'),
                ],
                default='unverified',
                max_length=20,
            ),
        ),
        migrations.RunPython(
            classify_demonstration_schools,
            restore_unverified_schools,
        ),
    ]
