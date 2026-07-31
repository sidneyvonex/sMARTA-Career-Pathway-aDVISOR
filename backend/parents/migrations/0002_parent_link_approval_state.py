from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentstudentlink',
            name='claimed_relationship',
            field=models.CharField(
                choices=[
                    ('mother', 'Mother'),
                    ('father', 'Father'),
                    ('guardian', 'Guardian'),
                    ('relative', 'Other relative'),
                    ('other', 'Other'),
                ],
                default='guardian',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='parentstudentlink',
            name='learner_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parentstudentlink',
            name='revoked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parentstudentlink',
            name='status',
            field=models.CharField(
                choices=[
                    ('invited', 'Invited'),
                    ('pending_learner', 'Pending learner approval'),
                    ('active', 'Active'),
                    ('revoked', 'Revoked'),
                ],
                default='active',
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='parentstudentlink',
            name='status',
            field=models.CharField(
                choices=[
                    ('invited', 'Invited'),
                    ('pending_learner', 'Pending learner approval'),
                    ('active', 'Active'),
                    ('revoked', 'Revoked'),
                ],
                default='pending_learner',
                max_length=20,
            ),
        ),
    ]
