from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_admin', '0004_alter_auditlog_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('user_registered', 'User registered'),
                    ('email_verified', 'Email verified'),
                    ('password_reset', 'Password reset'),
                    ('account_deactivated', 'Account deactivated'),
                    ('account_activated', 'Account activated'),
                    ('invite_sent', 'Invite sent'),
                    ('invite_accepted', 'Invite accepted'),
                    ('school_created', 'School created'),
                    ('school_edited', 'School edited'),
                    ('school_deactivated', 'School deactivated'),
                    ('school_activated', 'School activated'),
                    ('counselor_added', 'Counselor added to school'),
                    ('counselor_removed', 'Counselor removed from school'),
                    ('counselor_assigned', 'Counselor assigned to student'),
                    ('grade_verified', 'Grade verified'),
                    (
                        'grade_verification_removed',
                        'Grade verification removed',
                    ),
                    (
                        'school_membership_approved',
                        'School membership approved',
                    ),
                    (
                        'school_membership_rejected',
                        'School membership rejected',
                    ),
                    (
                        'framework_combination_status_changed',
                        'Framework combination status changed',
                    ),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='target_type',
            field=models.CharField(
                choices=[
                    ('user', 'User'),
                    ('school', 'School'),
                    ('assignment', 'Assignment'),
                    ('grade', 'Grade'),
                    ('combination', 'Combination'),
                ],
                max_length=20,
            ),
        ),
    ]
