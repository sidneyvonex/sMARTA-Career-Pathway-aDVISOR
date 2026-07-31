from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('guidance', '0002_seed_pilot_catalogue'),
    ]

    operations = [
        migrations.CreateModel(
            name='LearnerCombinationChoice',
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
                (
                    'status',
                    models.CharField(
                        choices=[('saved', 'Saved'), ('provisional', 'Provisional')],
                        default='saved',
                        max_length=12,
                    ),
                ),
                ('learner_reason', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'combination',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='learner_choices',
                        to='guidance.subjectcombination',
                    ),
                ),
                (
                    'student_profile',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='combination_choices',
                        to='accounts.studentprofile',
                    ),
                ),
            ],
            options={
                'ordering': ['created_at', 'pk'],
            },
        ),
        migrations.AddConstraint(
            model_name='learnercombinationchoice',
            constraint=models.UniqueConstraint(
                fields=('student_profile', 'combination'),
                name='guidance_learner_combo_uniq',
            ),
        ),
        migrations.AddConstraint(
            model_name='learnercombinationchoice',
            constraint=models.UniqueConstraint(
                condition=models.Q(('status', 'provisional')),
                fields=('student_profile',),
                name='guidance_one_provisional_choice',
            ),
        ),
    ]
