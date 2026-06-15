from django.db import migrations

SUBJECTS = [
    # Grade 9
    {'code': 'ENG9',  'name': 'English',               'grade': 9,  'category': 'Core'},
    {'code': 'KIS9',  'name': 'Kiswahili',              'grade': 9,  'category': 'Core'},
    {'code': 'MTH9',  'name': 'Mathematics',            'grade': 9,  'category': 'Core'},
    {'code': 'INT9',  'name': 'Integrated Science',     'grade': 9,  'category': 'Core'},
    {'code': 'HSS9',  'name': 'Social Studies',         'grade': 9,  'category': 'Core'},
    {'code': 'BST9',  'name': 'Business Studies',       'grade': 9,  'category': 'Core'},
    {'code': 'AGR9',  'name': 'Agriculture',            'grade': 9,  'category': 'Core'},
    {'code': 'HOM9',  'name': 'Home Science',           'grade': 9,  'category': 'Core'},
    {'code': 'ART9',  'name': 'Creative Arts & Sports', 'grade': 9,  'category': 'Core'},
    {'code': 'CRE9',  'name': 'CRE / IRE / HRE',       'grade': 9,  'category': 'Optional'},
    {'code': 'FRN9',  'name': 'French',                 'grade': 9,  'category': 'Optional'},
    {'code': 'GER9',  'name': 'German',                 'grade': 9,  'category': 'Optional'},
    {'code': 'ARA9',  'name': 'Arabic',                 'grade': 9,  'category': 'Optional'},
    {'code': 'MUS9',  'name': 'Music',                  'grade': 9,  'category': 'Optional'},
    # Grade 10
    {'code': 'ENG10', 'name': 'English',               'grade': 10, 'category': 'Core'},
    {'code': 'KIS10', 'name': 'Kiswahili',              'grade': 10, 'category': 'Core'},
    {'code': 'MTH10', 'name': 'Mathematics',            'grade': 10, 'category': 'Core'},
    {'code': 'INT10', 'name': 'Integrated Science',     'grade': 10, 'category': 'Core'},
    {'code': 'HSS10', 'name': 'Social Studies',         'grade': 10, 'category': 'Core'},
    {'code': 'BST10', 'name': 'Business Studies',       'grade': 10, 'category': 'Core'},
    {'code': 'AGR10', 'name': 'Agriculture',            'grade': 10, 'category': 'Core'},
    {'code': 'HOM10', 'name': 'Home Science',           'grade': 10, 'category': 'Core'},
    {'code': 'ART10', 'name': 'Creative Arts & Sports', 'grade': 10, 'category': 'Core'},
    {'code': 'CRE10', 'name': 'CRE / IRE / HRE',       'grade': 10, 'category': 'Optional'},
    {'code': 'FRN10', 'name': 'French',                 'grade': 10, 'category': 'Optional'},
    {'code': 'GER10', 'name': 'German',                 'grade': 10, 'category': 'Optional'},
    {'code': 'ARA10', 'name': 'Arabic',                 'grade': 10, 'category': 'Optional'},
    {'code': 'MUS10', 'name': 'Music',                  'grade': 10, 'category': 'Optional'},
]


def seed_subjects(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')
    for s in SUBJECTS:
        Subject.objects.get_or_create(code=s['code'], defaults=s)


def unseed_subjects(apps, schema_editor):
    Subject = apps.get_model('students', 'Subject')
    Subject.objects.filter(code__in=[s['code'] for s in SUBJECTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('students', '0002_add_grade_validators'),
    ]
    operations = [
        migrations.RunPython(seed_subjects, unseed_subjects),
    ]
