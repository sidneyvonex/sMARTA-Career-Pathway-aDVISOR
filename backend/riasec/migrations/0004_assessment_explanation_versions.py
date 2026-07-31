from django.db import migrations, models


def label_existing_records(apps, schema_editor):
    Assessment = apps.get_model('riasec', 'RIASECAssessment')
    Recommendation = apps.get_model('riasec', 'Recommendation')
    Assessment.objects.filter(instrument_version='').update(
        instrument_version='legacy-unversioned'
    )
    Recommendation.objects.filter(algorithm_version='').update(
        algorithm_version='legacy-unversioned'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('riasec', '0003_seed_pathways'),
    ]

    operations = [
        migrations.AddField(
            model_name='riasecassessment',
            name='instrument_version',
            field=models.CharField(blank=True, default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recommendation',
            name='algorithm_version',
            field=models.CharField(blank=True, default='', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recommendation',
            name='explanation',
            field=models.JSONField(default=dict),
        ),
        migrations.RunPython(label_existing_records, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='riasecassessment',
            name='instrument_version',
            field=models.CharField(default='riasec-pilot-1.0', max_length=40),
        ),
        migrations.AlterField(
            model_name='recommendation',
            name='algorithm_version',
            field=models.CharField(default='interest-alignment-1.0', max_length=40),
        ),
    ]
