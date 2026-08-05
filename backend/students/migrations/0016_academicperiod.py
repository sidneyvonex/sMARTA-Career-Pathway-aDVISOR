from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('students', '0015_alter_performanceleveldefinition_options')]

    operations = [
        migrations.CreateModel(
            name='AcademicPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField()),
                ('term', models.PositiveSmallIntegerField(choices=[(1, 'Term 1'), (2, 'Term 2'), (3, 'Term 3')])),
                ('term_ends_at', models.DateTimeField()),
                ('entry_opens_at', models.DateTimeField()),
                ('entry_closes_at', models.DateTimeField()),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-year', '-term']},
        ),
        migrations.AddConstraint(
            model_name='academicperiod',
            constraint=models.UniqueConstraint(fields=('year', 'term'), name='students_academic_period_uniq'),
        ),
        migrations.AddConstraint(
            model_name='academicperiod',
            constraint=models.CheckConstraint(check=models.Q(('entry_opens_at__gte', models.F('term_ends_at'))), name='students_period_opens_after_term_ck'),
        ),
        migrations.AddConstraint(
            model_name='academicperiod',
            constraint=models.CheckConstraint(check=models.Q(('entry_closes_at__gt', models.F('entry_opens_at'))), name='students_period_closes_after_open_ck'),
        ),
    ]
