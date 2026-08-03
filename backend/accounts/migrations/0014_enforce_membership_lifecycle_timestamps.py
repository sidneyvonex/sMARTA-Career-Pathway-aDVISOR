from django.db import migrations, models


def validate_learner_request_lifecycle_timestamps(apps, schema_editor):
    StudentSchoolMembership = apps.get_model(
        'accounts',
        'StudentSchoolMembership',
    )
    valid_lifecycle = (
        models.Q(
            status='pending',
            requested_at__isnull=False,
            decided_at__isnull=True,
            started_at__isnull=True,
            ended_at__isnull=True,
        )
        | models.Q(
            status='active',
            requested_at__isnull=False,
            decided_at__isnull=False,
            started_at__isnull=False,
            ended_at__isnull=True,
        )
        | models.Q(
            status='rejected',
            requested_at__isnull=False,
            decided_at__isnull=False,
            started_at__isnull=True,
            ended_at__isnull=True,
        )
        | models.Q(
            status='ended',
            requested_at__isnull=False,
            decided_at__isnull=False,
            started_at__isnull=False,
            ended_at__isnull=False,
        )
    )
    invalid_count = (
        StudentSchoolMembership.objects
        .filter(record_source='learner_request')
        .exclude(valid_lifecycle)
        .count()
    )
    if invalid_count:
        raise RuntimeError(
            f'{invalid_count} learner-request membership row(s) have '
            'incomplete membership lifecycle provenance. Supply audited '
            'timestamps before retrying this migration.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_studentschoolmembership'),
    ]

    operations = [
        migrations.RunPython(
            validate_learner_request_lifecycle_timestamps,
            migrations.RunPython.noop,
        ),
        migrations.RemoveConstraint(
            model_name='studentschoolmembership',
            name='accounts_membership_approval_time_ck',
        ),
        migrations.AddConstraint(
            model_name='studentschoolmembership',
            constraint=models.CheckConstraint(
                check=models.Q(
                    ('record_source', 'legacy_backfill'),
                    models.Q(
                        ('decided_at__isnull', True),
                        ('ended_at__isnull', True),
                        ('record_source', 'learner_request'),
                        ('started_at__isnull', True),
                        ('status', 'pending'),
                    ),
                    models.Q(
                        ('decided_at__isnull', False),
                        ('ended_at__isnull', True),
                        ('record_source', 'learner_request'),
                        ('started_at__isnull', False),
                        ('status', 'active'),
                    ),
                    models.Q(
                        ('decided_at__isnull', False),
                        ('ended_at__isnull', True),
                        ('record_source', 'learner_request'),
                        ('started_at__isnull', True),
                        ('status', 'rejected'),
                    ),
                    models.Q(
                        ('decided_at__isnull', False),
                        ('ended_at__isnull', False),
                        ('record_source', 'learner_request'),
                        ('started_at__isnull', False),
                        ('status', 'ended'),
                    ),
                    _connector='OR',
                ),
                name='accounts_membership_lifecycle_time_ck',
            ),
        ),
    ]
