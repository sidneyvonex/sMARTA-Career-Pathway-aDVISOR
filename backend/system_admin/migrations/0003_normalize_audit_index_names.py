from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system_admin', '0002_grade_verification_audit_choices'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='auditlog',
            new_name='system_admi_action_935381_idx',
            old_name='system_admin_action_0b1a2c_idx',
        ),
        migrations.RenameIndex(
            model_name='auditlog',
            new_name='system_admi_actor_i_69823f_idx',
            old_name='system_admin_actor_1d3e4f_idx',
        ),
        migrations.RenameIndex(
            model_name='auditlog',
            new_name='system_admi_target__058dfa_idx',
            old_name='system_admin_target_5a6b7c_idx',
        ),
    ]
