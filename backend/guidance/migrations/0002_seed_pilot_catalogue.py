from datetime import date

from django.db import migrations


FRAMEWORK = {
    'code': 'CBC-SS-PILOT-2026',
    'title': 'CBC Senior School Pilot Catalogue 2026',
    'description': (
        'A curated presentation catalogue verified against the Ministry of Education '
        'Senior School subject-combination list on 2026-07-30. It covers representative '
        'options for the five-county pilot and is not the complete national catalogue.'
    ),
    'source_url': (
        'https://selection-placement.kemis.go.ke/uploads/'
        '1750333580754-subject-combinations-1750333524964.pdf'
    ),
    'effective_date': date(2026, 1, 1),
    'is_active': True,
}

TRACKS = [
    {
        'code': 'PURE-SCIENCES',
        'name': 'Pure Sciences',
        'pathway': 'STEM',
        'description': 'Combinations centred on scientific inquiry and laboratory sciences.',
    },
    {
        'code': 'APPLIED-SCIENCES',
        'name': 'Applied Sciences',
        'pathway': 'STEM',
        'description': 'Combinations applying science and technology to practical contexts.',
    },
    {
        'code': 'TECHNICAL-STUDIES',
        'name': 'Technical Studies',
        'pathway': 'STEM',
        'description': 'Combinations centred on technical design, making and technology.',
    },
    {
        'code': 'LANGUAGES-LITERATURE',
        'name': 'Languages & Literature',
        'pathway': 'Social Sciences',
        'description': 'Combinations centred on language, literature and communication.',
    },
    {
        'code': 'HUMANITIES-BUSINESS',
        'name': 'Humanities & Business Studies',
        'pathway': 'Social Sciences',
        'description': 'Combinations covering society, enterprise, geography and citizenship.',
    },
    {
        'code': 'ARTS',
        'name': 'Arts',
        'pathway': 'Arts & Sports Science',
        'description': 'Combinations centred on visual, musical and performance practice.',
    },
    {
        'code': 'SPORTS-RECREATION',
        'name': 'Sports & Recreation',
        'pathway': 'Arts & Sports Science',
        'description': 'Combinations centred on sport, recreation and supporting sciences.',
    },
]

COMBINATIONS = [
    {
        'code': 'ST1042',
        'title': 'Agriculture, Biology & Chemistry',
        'track': 'PURE-SCIENCES',
        'subjects': ('AGR10', 'BIO10', 'CHE10'),
    },
    {
        'code': 'ST2007',
        'title': 'Business Studies, Computer Studies & Physics',
        'track': 'APPLIED-SCIENCES',
        'subjects': ('BST10', 'CPS10', 'PHY10'),
    },
    {
        'code': 'ST2067',
        'title': 'Agriculture, Computer Studies & Physics',
        'track': 'APPLIED-SCIENCES',
        'subjects': ('AGR10', 'CPS10', 'PHY10'),
    },
    {
        'code': 'ST3074',
        'title': 'Computer Studies, General Science & Media Technology',
        'track': 'TECHNICAL-STUDIES',
        'subjects': ('CPS10', 'GSC10', 'MDT10'),
    },
    {
        'code': 'SS1006',
        'title': 'Arabic, Computer Studies & French',
        'track': 'LANGUAGES-LITERATURE',
        'subjects': ('ARA10', 'CPS10', 'FRN10'),
    },
    {
        'code': 'SS2019',
        'title': 'Religious Education, Geography & History',
        'track': 'HUMANITIES-BUSINESS',
        'subjects': ('CHR10', 'GEO10', 'HCT10'),
    },
    {
        'code': 'SS2033',
        'title': 'Computer Studies, Geography & Islamic Religious Education',
        'track': 'HUMANITIES-BUSINESS',
        'subjects': ('CPS10', 'GEO10', 'IRE10'),
    },
    {
        'code': 'AS1021',
        'title': 'Computer Studies, Fine Arts & Music and Dance',
        'track': 'ARTS',
        'subjects': ('CPS10', 'FAR10', 'MDA10'),
    },
    {
        'code': 'AS1049',
        'title': 'Literature, Music and Dance & Theatre and Film',
        'track': 'ARTS',
        'subjects': ('LIE10', 'MDA10', 'TFM10'),
    },
    {
        'code': 'AS2009',
        'title': 'Biology, Geography & Sports and Recreation',
        'track': 'SPORTS-RECREATION',
        'subjects': ('BIO10', 'GEO10', 'SRE10'),
    },
]

PILOT_SCHOOLS = [
    {
        'school_code': 'PILOT-KIA-001',
        'name': 'Smarta Shauri Pilot School — Kiambu',
        'county': 'kiambu',
        'offerings': ('ST1042', 'ST2007', 'SS2019', 'AS2009'),
    },
    {
        'school_code': 'PILOT-MUR-001',
        'name': "Smarta Shauri Pilot School — Murang'a",
        'county': 'muranga',
        'offerings': ('ST2067', 'ST3074', 'SS1006', 'AS1021'),
    },
    {
        'school_code': 'PILOT-NYE-001',
        'name': 'Smarta Shauri Pilot School — Nyeri',
        'county': 'nyeri',
        'offerings': ('ST1042', 'ST2067', 'SS2033', 'AS1049'),
    },
    {
        'school_code': 'PILOT-KIR-001',
        'name': 'Smarta Shauri Pilot School — Kirinyaga',
        'county': 'kirinyaga',
        'offerings': ('ST2007', 'ST3074', 'SS2019', 'AS2009'),
    },
    {
        'school_code': 'PILOT-NYA-001',
        'name': 'Smarta Shauri Pilot School — Nyandarua',
        'county': 'nyandarua',
        'offerings': ('ST1042', 'ST2007', 'SS1006', 'AS1021'),
    },
]


def seed_pilot_catalogue(apps, schema_editor):
    FrameworkVersion = apps.get_model('guidance', 'FrameworkVersion')
    PathwayTrack = apps.get_model('guidance', 'PathwayTrack')
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    SchoolOffering = apps.get_model('guidance', 'SchoolOffering')
    Pathway = apps.get_model('riasec', 'Pathway')
    Subject = apps.get_model('students', 'Subject')
    School = apps.get_model('accounts', 'School')

    FrameworkVersion.objects.exclude(code=FRAMEWORK['code']).update(is_active=False)
    framework, _created = FrameworkVersion.objects.update_or_create(
        code=FRAMEWORK['code'],
        defaults={key: value for key, value in FRAMEWORK.items() if key != 'code'},
    )

    pathways = {
        pathway.name: pathway
        for pathway in Pathway.objects.filter(
            name__in={track['pathway'] for track in TRACKS}
        )
    }
    if len(pathways) != 3:
        raise RuntimeError('The three seeded RIASEC pathways are required.')

    tracks = {}
    for track_data in TRACKS:
        track, _created = PathwayTrack.objects.update_or_create(
            framework_version=framework,
            code=track_data['code'],
            defaults={
                'name': track_data['name'],
                'pathway': pathways[track_data['pathway']],
                'description': track_data['description'],
                'is_active': True,
            },
        )
        tracks[track.code] = track

    required_subject_codes = {
        code for combination in COMBINATIONS for code in combination['subjects']
    }
    subjects = {
        subject.code: subject
        for subject in Subject.objects.filter(code__in=required_subject_codes)
    }
    missing_subjects = required_subject_codes - subjects.keys()
    if missing_subjects:
        raise RuntimeError(
            f'Missing Grade 10 subjects required by pilot catalogue: '
            f'{", ".join(sorted(missing_subjects))}'
        )

    combinations = {}
    for combination_data in COMBINATIONS:
        subject_one, subject_two, subject_three = (
            subjects[code] for code in combination_data['subjects']
        )
        combination, _created = SubjectCombination.objects.update_or_create(
            framework_version=framework,
            code=combination_data['code'],
            defaults={
                'track': tracks[combination_data['track']],
                'title': combination_data['title'],
                'description': (
                    'Curated pilot option from the official Senior School '
                    'subject-combination catalogue.'
                ),
                'subject_one': subject_one,
                'subject_two': subject_two,
                'subject_three': subject_three,
                'is_active': True,
            },
        )
        combinations[combination.code] = combination

    for school_data in PILOT_SCHOOLS:
        school, _created = School.objects.update_or_create(
            school_code=school_data['school_code'],
            defaults={
                'name': school_data['name'],
                'county': school_data['county'],
                'is_active': True,
            },
        )
        for combination_code in school_data['offerings']:
            SchoolOffering.objects.update_or_create(
                school=school,
                combination=combinations[combination_code],
                defaults={'is_active': True},
            )


def unseed_pilot_catalogue(apps, schema_editor):
    FrameworkVersion = apps.get_model('guidance', 'FrameworkVersion')
    PathwayTrack = apps.get_model('guidance', 'PathwayTrack')
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    SchoolOffering = apps.get_model('guidance', 'SchoolOffering')
    School = apps.get_model('accounts', 'School')

    framework = FrameworkVersion.objects.filter(code=FRAMEWORK['code']).first()
    school_codes = [school['school_code'] for school in PILOT_SCHOOLS]

    if framework:
        SchoolOffering.objects.filter(
            school__school_code__in=school_codes,
            combination__framework_version=framework,
        ).delete()
        SubjectCombination.objects.filter(framework_version=framework).delete()
        PathwayTrack.objects.filter(framework_version=framework).delete()
        framework.delete()

    School.objects.filter(school_code__in=school_codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('guidance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_pilot_catalogue, unseed_pilot_catalogue),
    ]
