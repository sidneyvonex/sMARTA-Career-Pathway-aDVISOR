from datetime import date

from django.db import migrations, models


CATALOGUE_URL = (
    'https://selection.education.go.ke/uploads/'
    '1750333580754-subject-combinations-1750333524964.pdf'
)
LEGACY_CATALOGUE_URL = (
    'https://selection-placement.kemis.go.ke/uploads/'
    '1750333580754-subject-combinations-1750333524964.pdf'
)
PILOT_FRAMEWORK_CODE = 'CBC-SS-PILOT-2026'


def classify_seeded_catalogue(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    FrameworkVersion = apps.get_model('guidance', 'FrameworkVersion')
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    SchoolOffering = apps.get_model('guidance', 'SchoolOffering')

    School.objects.filter(school_code__startswith='PILOT-').update(
        verification_status='demonstration',
    )
    FrameworkVersion.objects.filter(code=PILOT_FRAMEWORK_CODE).update(
        source_url=CATALOGUE_URL,
    )
    SubjectCombination.objects.filter(
        framework_version__code=PILOT_FRAMEWORK_CODE,
    ).update(
        verification_status='verified',
        source_url=CATALOGUE_URL,
        source_checked_at=date(2026, 7, 31),
    )
    SchoolOffering.objects.filter(
        school__school_code__startswith='PILOT-',
    ).update(verification_status='demonstration')


def restore_unverified_catalogue(apps, schema_editor):
    School = apps.get_model('accounts', 'School')
    FrameworkVersion = apps.get_model('guidance', 'FrameworkVersion')
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    SchoolOffering = apps.get_model('guidance', 'SchoolOffering')

    School.objects.filter(verification_status='demonstration').update(
        verification_status='unverified',
    )
    FrameworkVersion.objects.filter(code=PILOT_FRAMEWORK_CODE).update(
        source_url=LEGACY_CATALOGUE_URL,
    )
    SubjectCombination.objects.filter(
        framework_version__code=PILOT_FRAMEWORK_CODE,
    ).update(
        verification_status='unverified',
        source_url='',
        source_checked_at=None,
    )
    SchoolOffering.objects.filter(
        verification_status='demonstration',
    ).update(verification_status='unverified')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_school_provenance'),
        ('guidance', '0005_learner_plan_and_milestones'),
    ]

    operations = [
        migrations.AddField(
            model_name='schooloffering',
            name='source_checked_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='schooloffering',
            name='source_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='schooloffering',
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
        migrations.AddField(
            model_name='subjectcombination',
            name='source_checked_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subjectcombination',
            name='source_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='subjectcombination',
            name='verification_status',
            field=models.CharField(
                choices=[
                    ('unverified', 'Unverified'),
                    ('verified', 'Verified'),
                ],
                default='unverified',
                max_length=20,
            ),
        ),
        migrations.RunPython(
            classify_seeded_catalogue,
            restore_unverified_catalogue,
        ),
    ]
