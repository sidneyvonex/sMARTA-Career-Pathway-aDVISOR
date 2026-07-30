from django.db import migrations, models


def activate_existing_school_links(apps, schema_editor):
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    StudentProfile.objects.filter(
        mode='school_linked',
        school__isnull=False,
    ).update(school_membership_status='active')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_school_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='school_membership_status',
            field=models.CharField(
                choices=[
                    ('not_applicable', 'Not Applicable'),
                    ('pending', 'Pending Approval'),
                    ('active', 'Active'),
                    ('rejected', 'Rejected'),
                ],
                default='not_applicable',
                max_length=20,
            ),
        ),
        migrations.RunPython(activate_existing_school_links, migrations.RunPython.noop),
    ]
