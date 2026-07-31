from django.db import migrations, models


# Curated from the KICD Grade 10 curriculum designs and the Ministry of
# Education Senior School subject-combination catalogue, checked 2026-07-30:
# https://kicd.ac.ke/cbc-materials/curriculum-designs/grade-ten/
# https://selection.education.go.ke/files/subject-combinations-senior-schools.pdf
GRADE10_SUBJECTS = [
    {'code': 'ENG10', 'name': 'English', 'category': 'Core'},
    {'code': 'KIS10', 'name': 'Kiswahili', 'category': 'Core'},
    {'code': 'CSL10', 'name': 'Community Service Learning', 'category': 'Core'},
    {'code': 'PED10', 'name': 'Physical Education', 'category': 'Core'},
    {'code': 'CMT10', 'name': 'Core Mathematics', 'category': 'Elective'},
    {'code': 'EMT10', 'name': 'Essential Mathematics', 'category': 'Elective'},
    {'code': 'BIO10', 'name': 'Biology', 'category': 'Elective'},
    {'code': 'CHE10', 'name': 'Chemistry', 'category': 'Elective'},
    {'code': 'PHY10', 'name': 'Physics', 'category': 'Elective'},
    {'code': 'GSC10', 'name': 'General Science', 'category': 'Elective'},
    {'code': 'AGR10', 'name': 'Agriculture', 'category': 'Elective'},
    {'code': 'CPS10', 'name': 'Computer Studies', 'category': 'Elective'},
    {'code': 'HOM10', 'name': 'Home Science', 'category': 'Elective'},
    {'code': 'AVT10', 'name': 'Aviation', 'category': 'Elective'},
    {'code': 'BCN10', 'name': 'Building Construction', 'category': 'Elective'},
    {'code': 'ELC10', 'name': 'Electricity', 'category': 'Elective'},
    {'code': 'MTW10', 'name': 'Metal Work', 'category': 'Elective'},
    {'code': 'PME10', 'name': 'Power Mechanics', 'category': 'Elective'},
    {'code': 'WDW10', 'name': 'Woodwork', 'category': 'Elective'},
    {'code': 'MDT10', 'name': 'Media Technology', 'category': 'Elective'},
    {'code': 'MFT10', 'name': 'Marine & Fisheries', 'category': 'Elective'},
    {'code': 'BST10', 'name': 'Business Studies', 'category': 'Elective'},
    {'code': 'HCT10', 'name': 'History & Citizenship', 'category': 'Elective'},
    {'code': 'GEO10', 'name': 'Geography', 'category': 'Elective'},
    {'code': 'LIE10', 'name': 'Literature in English', 'category': 'Elective'},
    {'code': 'FKI10', 'name': 'Fasihi ya Kiswahili', 'category': 'Elective'},
    {'code': 'FRN10', 'name': 'French', 'category': 'Elective'},
    {'code': 'GER10', 'name': 'German', 'category': 'Elective'},
    {'code': 'ARA10', 'name': 'Arabic', 'category': 'Elective'},
    {'code': 'CHR10', 'name': 'Christian Religious Education', 'category': 'Elective'},
    {'code': 'IRE10', 'name': 'Islamic Religious Education', 'category': 'Elective'},
    {'code': 'HRE10', 'name': 'Hindu Religious Education', 'category': 'Elective'},
    {'code': 'FAR10', 'name': 'Fine Arts', 'category': 'Elective'},
    {'code': 'MDA10', 'name': 'Music & Dance', 'category': 'Elective'},
    {'code': 'TFM10', 'name': 'Theatre & Film', 'category': 'Elective'},
    {'code': 'SRE10', 'name': 'Sports & Recreation', 'category': 'Elective'},
]

OBSOLETE_GRADE10_CODES = ['MTH10', 'INT10', 'HSS10', 'ART10', 'CRE10', 'MUS10']


def correct_grade10_catalogue(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')

    for subject in GRADE10_SUBJECTS:
        Subject.objects.update_or_create(
            code=subject['code'],
            defaults={
                'name': subject['name'],
                'grade': 10,
                'category': subject['category'],
                'is_active': True,
            },
        )

    Subject.objects.filter(code__in=OBSOLETE_GRADE10_CODES).update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_alter_cbcgrade_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(correct_grade10_catalogue, migrations.RunPython.noop),
    ]
