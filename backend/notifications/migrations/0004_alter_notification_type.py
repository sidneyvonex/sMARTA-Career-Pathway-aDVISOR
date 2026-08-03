from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_alter_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[
                    ('assessment_submitted', 'Assessment Submitted'),
                    ('counselor_note', 'Counselor Note'),
                    ('parent_linked', 'Parent Linked'),
                    ('counselor_assigned', 'Counselor Assigned'),
                    ('child_assessment_complete', 'Child Assessment Complete'),
                    ('school_membership_decided', 'School Membership Decided'),
                    ('grade_verification_changed', 'Grade Verification Changed'),
                    ('school_transfer_decided', 'School Transfer Decided'),
                    ('counselor_intervention', 'Counselor Intervention'),
                    ('academic_goal_achieved', 'Academic Goal Achieved'),
                ],
                max_length=30,
            ),
        ),
    ]
