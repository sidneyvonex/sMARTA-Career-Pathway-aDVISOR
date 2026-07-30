from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('guidance', '0004_subject_combination_related_routes'),
    ]

    operations = [
        migrations.CreateModel(
            name='LearnerPlan',
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
                ('learner_reason', models.TextField(blank=True, default='')),
                (
                    'review_status',
                    models.CharField(
                        choices=[
                            ('draft', 'Draft'),
                            ('ready_for_review', 'Ready for review'),
                            ('reviewed', 'Reviewed'),
                        ],
                        default='draft',
                        max_length=20,
                    ),
                ),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'provisional_choice',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='plans',
                        to='guidance.learnercombinationchoice',
                    ),
                ),
                (
                    'student_profile',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='learner_plan',
                        to='accounts.studentprofile',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='PlanMilestone',
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
                ('title', models.CharField(max_length=160)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('is_complete', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'plan',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='milestones',
                        to='guidance.learnerplan',
                    ),
                ),
            ],
            options={
                'ordering': ['position', 'created_at', 'pk'],
            },
        ),
    ]
