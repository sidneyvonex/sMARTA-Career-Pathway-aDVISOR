from django.db import migrations, models


MATHEMATICS_CODES = ('CMT10', 'EMT10')
PHYSICAL_EDUCATION_CODE = 'PED10'


def correct_curriculum_roles(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')

    Subject.objects.filter(
        grade=10,
        category='Elective',
        is_active=True,
    ).update(is_selectable_in_combination=True)
    Subject.objects.filter(code__in=MATHEMATICS_CODES).update(
        category='Core',
        is_selectable_in_combination=True,
    )
    Subject.objects.filter(code=PHYSICAL_EDUCATION_CODE).update(
        category='Required',
        is_selectable_in_combination=False,
    )


def restore_previous_roles(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')

    Subject.objects.update(is_selectable_in_combination=False)
    Subject.objects.filter(code__in=MATHEMATICS_CODES).update(category='Elective')
    Subject.objects.filter(code=PHYSICAL_EDUCATION_CODE).update(category='Core')


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_cbcgrade_provenance'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_selectable_in_combination',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(correct_curriculum_roles, restore_previous_roles),
    ]
