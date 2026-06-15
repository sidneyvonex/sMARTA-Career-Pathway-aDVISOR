from django.db import migrations

PATHWAYS = [
    {
        'name': 'STEM',
        'description': (
            'Science, Technology, Engineering & Mathematics — ideal for students who love '
            'investigating how things work and solving real-world technical problems. '
            'Includes Pure Sciences (Biology, Chemistry, Physics, Mathematics), '
            'Applied Sciences (Agriculture, Computer Science, Home Science), and '
            'Technical Studies (Aviation, Building, Electrical, Metal Work, Wood Work).'
        ),
        'weight_r': 0.25,
        'weight_i': 0.40,
        'weight_a': 0.05,
        'weight_s': 0.05,
        'weight_e': 0.15,
        'weight_c': 0.10,
    },
    {
        'name': 'Social Sciences',
        'description': (
            'Languages, Humanities & Business — ideal for students interested in law, '
            'economics, education, governance, languages, and human behaviour. '
            'Includes Languages & Literature (English, Kiswahili, French, Arabic, German) and '
            'Humanities & Business (History & Citizenship, Geography, Business Studies, '
            'Religious Education).'
        ),
        'weight_r': 0.05,
        'weight_i': 0.15,
        'weight_a': 0.10,
        'weight_s': 0.35,
        'weight_e': 0.25,
        'weight_c': 0.10,
    },
    {
        'name': 'Arts & Sports Science',
        'description': (
            'Creative Arts & Athletics — ideal for students drawn to music, dance, theatre, '
            'fine arts, or sports coaching. Includes Arts (Music & Dance, Theatre & Film, '
            'Fine Arts) and Sports (Sports & Recreation Science, Physical Education).'
        ),
        'weight_r': 0.20,
        'weight_i': 0.05,
        'weight_a': 0.45,
        'weight_s': 0.20,
        'weight_e': 0.05,
        'weight_c': 0.05,
    },
]


def seed_pathways(apps, schema_editor):
    Pathway = apps.get_model('riasec', 'Pathway')
    for p in PATHWAYS:
        Pathway.objects.get_or_create(name=p['name'], defaults=p)


def unseed_pathways(apps, schema_editor):
    Pathway = apps.get_model('riasec', 'Pathway')
    Pathway.objects.filter(name__in=[p['name'] for p in PATHWAYS]).delete()


class Migration(migrations.Migration):
    dependencies = [('riasec', '0002_seed_questions')]
    operations = [migrations.RunPython(seed_pathways, unseed_pathways)]
