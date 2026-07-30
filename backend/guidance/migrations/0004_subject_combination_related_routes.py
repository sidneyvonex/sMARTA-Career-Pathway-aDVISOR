from django.db import migrations, models


ROUTES_BY_CODE = {
    'ST1042': ['Agricultural science', 'Biological science', 'Laboratory technology'],
    'ST2007': ['Software and computing', 'Business technology', 'Applied physics'],
    'ST2067': ['Agricultural technology', 'Engineering foundations', 'Data and computing'],
    'ST3074': ['Media technology', 'Digital production', 'Technical communication'],
    'SS1006': ['Translation and interpretation', 'International relations', 'Language technology'],
    'SS2019': ['Education', 'Public service', 'Heritage and community work'],
    'SS2033': ['Geospatial services', 'Community development', 'Information systems'],
    'AS1021': ['Digital arts', 'Music production', 'Creative technology'],
    'AS1049': ['Performing arts', 'Film and theatre production', 'Creative writing'],
    'AS2009': ['Sports science', 'Coaching and recreation', 'Environmental fieldwork'],
}


def populate_related_routes(apps, schema_editor):
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    for code, routes in ROUTES_BY_CODE.items():
        SubjectCombination.objects.filter(code=code).update(related_routes=routes)


def clear_related_routes(apps, schema_editor):
    SubjectCombination = apps.get_model('guidance', 'SubjectCombination')
    SubjectCombination.objects.filter(code__in=ROUTES_BY_CODE).update(related_routes=[])


class Migration(migrations.Migration):

    dependencies = [
        ('guidance', '0003_learner_combination_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectcombination',
            name='related_routes',
            field=models.JSONField(default=list),
        ),
        migrations.RunPython(populate_related_routes, clear_related_routes),
    ]
