from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0011_school_official_identity')]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='grade',
            field=models.IntegerField(
                choices=[
                    (9, 'Grade 9'),
                    (10, 'Grade 10'),
                    (11, 'Grade 11'),
                    (12, 'Grade 12'),
                ]
            ),
        ),
    ]
