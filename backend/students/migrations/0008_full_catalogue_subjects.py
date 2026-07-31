from django.db import migrations


SUBJECTS = (
    ('IND10', 'Indigenous Language'),
    ('KSL10', 'Kenya Sign Language'),
    ('MCH10', 'Mandarin Chinese'),
)


def add_full_catalogue_subjects(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')
    for code, name in SUBJECTS:
        Subject.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'grade': 10,
                'category': 'Elective',
                'is_active': True,
                'is_selectable_in_combination': True,
            },
        )


def remove_full_catalogue_subjects(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')
    Subject.objects.filter(code__in=[code for code, _name in SUBJECTS]).delete()


class Migration(migrations.Migration):
    dependencies = [('students', '0007_subject_combination_selectability')]

    operations = [
        migrations.RunPython(
            add_full_catalogue_subjects,
            remove_full_catalogue_subjects,
        ),
    ]

