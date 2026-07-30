from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_alter_notification_type'),
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
                ],
                max_length=30,
            ),
        ),
    ]
