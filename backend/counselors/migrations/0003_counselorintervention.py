from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counselors', '0002_counselornote_visible_to_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='CounselorIntervention',
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
                    'category',
                    models.CharField(
                        choices=[
                            ('assessment', 'Interest assessment'),
                            ('academic_evidence', 'Academic evidence'),
                            ('combination', 'Subject combination'),
                            ('plan', 'Learner plan'),
                            ('follow_up', 'Follow-up'),
                            ('other', 'Other'),
                        ],
                        max_length=24,
                    ),
                ),
                ('action_agreed', models.TextField(max_length=2000)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('open', 'Open'),
                            ('completed', 'Completed'),
                        ],
                        default='open',
                        max_length=12,
                    ),
                ),
                ('learner_visible', models.BooleanField(default=True)),
                ('parent_visible', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'counselor',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='counselor_interventions_written',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'student',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='counselor_interventions_received',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['status', 'follow_up_date', '-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='counselorintervention',
            index=models.Index(
                fields=['counselor', 'status', 'follow_up_date'],
                name='counselor_follow_up_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='counselorintervention',
            index=models.Index(
                fields=['student', 'learner_visible'],
                name='student_visible_action_idx',
            ),
        ),
    ]
