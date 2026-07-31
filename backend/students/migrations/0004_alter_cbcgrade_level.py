from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_seed_subjects'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cbcgrade',
            name='level',
            field=models.CharField(
                choices=[
                    ('EE1', 'Exceeding Expectation - Level 1'),
                    ('EE2', 'Exceeding Expectation - Level 2'),
                    ('ME1', 'Meeting Expectation - Level 1'),
                    ('ME2', 'Meeting Expectation - Level 2'),
                    ('AE1', 'Approaching Expectation - Level 1'),
                    ('AE2', 'Approaching Expectation - Level 2'),
                    ('BE1', 'Below Expectation - Level 1'),
                    ('BE2', 'Below Expectation - Level 2'),
                ],
                max_length=10,
            ),
        ),
    ]
