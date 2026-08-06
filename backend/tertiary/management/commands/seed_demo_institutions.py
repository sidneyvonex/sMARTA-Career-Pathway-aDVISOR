"""
Seed ~100 real Kenyan institutions scraped from KUCCPS (kuccps.net) for demo use.

Run:
    python manage.py seed_demo_institutions
    python manage.py seed_demo_institutions --clear   # wipe existing demo records first
"""

from datetime import date

from django.core.management.base import BaseCommand

from tertiary.models import Institution

SCOPE = 'KUCCPS-DEMO'
SOURCE_URL = 'https://kuccps.net'
FRAMEWORK = 'CBC'
CYCLE = '2024/2025'
EFFECTIVE = date(2024, 1, 1)
STATUS = 'verified'

# (external_key, name, institution_type, county, website_url)
INSTITUTIONS = [
    # ── Public Universities ───────────────────────────────────────────────
    ('UON',   'University of Nairobi',                                    'university', 'Nairobi',        'https://www.uonbi.ac.ke'),
    ('KU',    'Kenyatta University',                                       'university', 'Nairobi',        'https://www.ku.ac.ke'),
    ('JKUAT', 'Jomo Kenyatta University of Agriculture and Technology',    'university', 'Kiambu',         'https://www.jkuat.ac.ke'),
    ('MU',    'Moi University',                                            'university', 'Uasin Gishu',    'https://www.mu.ac.ke'),
    ('EGU',   'Egerton University',                                        'university', 'Nakuru',         'https://www.egerton.ac.ke'),
    ('MSU',   'Maseno University',                                         'university', 'Kisumu',         'https://www.maseno.ac.ke'),
    ('MMUST', 'Masinde Muliro University of Science and Technology',       'university', 'Kakamega',       'https://www.mmust.ac.ke'),
    ('TUK',   'Technical University of Kenya',                             'university', 'Nairobi',        'https://www.tukenya.ac.ke'),
    ('TUM',   'Technical University of Mombasa',                           'university', 'Mombasa',        'https://www.tum.ac.ke'),
    ('DKUT',  'Dedan Kimathi University of Technology',                    'university', 'Nyeri',          'https://www.dkut.ac.ke'),
    ('JOOUST','Jaramogi Oginga Odinga University of Science and Technology','university','Siaya',          'https://www.jooust.ac.ke'),
    ('SEKU',  'South Eastern Kenya University',                            'university', 'Kitui',          'https://www.seku.ac.ke'),
    ('MUST',  'Meru University of Science and Technology',                 'university', 'Meru',           'https://www.must.ac.ke'),
    ('KSU',   'Kisii University',                                          'university', 'Kisii',          'https://www.kisiiuniversity.ac.ke'),
    ('MMU',   'Multimedia University of Kenya',                            'university', 'Nairobi',        'https://www.mmu.ac.ke'),
    ('UOE',   'University of Eldoret',                                     'university', 'Uasin Gishu',    'https://www.uoeld.ac.ke'),
    ('PU',    'Pwani University',                                          'university', 'Kilifi',         'https://www.pu.ac.ke'),
    ('MARU',  'Maasai Mara University',                                    'university', 'Narok',          'https://www.mmarau.ac.ke'),
    ('MKSU',  'Machakos University',                                       'university', 'Machakos',       'https://www.mksu.ac.ke'),
    ('KAU',   'Karatina University',                                       'university', 'Nyeri',          'https://www.karatinauniversity.ac.ke'),
    ('LU',    'Laikipia University',                                       'university', 'Laikipia',       'https://www.laikipiauniversity.ac.ke'),
    ('CHUKA', 'Chuka University',                                          'university', 'Tharaka Nithi',  'https://www.chuka.ac.ke'),
    ('KIBABII','Kibabii University',                                       'university', 'Bungoma',        'https://www.kibabiiuniversity.ac.ke'),
    ('KYU',   'Kirinyaga University',                                      'university', 'Kirinyaga',      'https://www.kyu.ac.ke'),
    ('TTU',   'Taita Taveta University',                                   'university', 'Taita Taveta',   'https://www.ttu.ac.ke'),
    ('RU',    'Rongo University',                                          'university', 'Migori',         'https://www.rongo.ac.ke'),
    ('GU',    'Garissa University',                                        'university', 'Garissa',        'https://www.garissauniversity.ac.ke'),
    ('CUK',   'Co-operative University of Kenya',                          'university', 'Nairobi',        'https://www.cuk.ac.ke'),
    ('UOK',   'University of Kabianga',                                    'university', 'Kericho',        'https://www.kabianga.ac.ke'),
    ('EMBUNI','University of Embu',                                        'university', 'Embu',           'https://www.embuni.ac.ke'),
    ('MUT',   "Murang'a University of Technology",                         'university', "Murang'a",       'https://www.mut.ac.ke'),
    ('KSUC',  'Koitaleel Samoei University College',                       'college',    'Nandi',          'https://www.ksuc.ac.ke'),
    # ── Public University Constituent Colleges ────────────────────────────
    ('ALUPE', 'Alupe University College',                                  'college',    'Busia',          ''),
    ('KFUC',  'Kaimosi Friends University College',                        'college',    'Vihiga',         ''),
    ('TMBOYA','Tom Mboya University College',                              'college',    'Homa Bay',       ''),
    ('TURKUC','Turkana University College',                                'college',    'Turkana',        ''),
    ('BOMUC', 'Bomet University College',                                  'college',    'Bomet',          'https://www.bomuc.ac.ke'),
    ('THARUC','Tharaka University College',                                'college',    'Tharaka Nithi',  ''),
    # ── Private Universities ──────────────────────────────────────────────
    ('USIU',  'United States International University — Africa',           'university', 'Nairobi',        'https://www.usiu.ac.ke'),
    ('MKU',   'Mount Kenya University',                                    'university', 'Nyeri',          'https://www.mku.ac.ke'),
    ('KABARAK','Kabarak University',                                       'university', 'Nakuru',         'https://www.kabarak.ac.ke'),
    ('DAYSTAR','Daystar University',                                       'university', 'Nairobi',        'https://www.daystar.ac.ke'),
    ('CUEA',  'Catholic University of Eastern Africa',                     'university', 'Nairobi',        'https://www.cuea.edu'),
    ('ZETECH','Zetech University',                                         'university', 'Nairobi',        'https://www.zetech.ac.ke'),
    ('KCAU',  'KCA University',                                            'university', 'Nairobi',        'https://www.kcau.ac.ke'),
    ('KEMU',  'Kenya Methodist University',                                'university', 'Meru',           'https://www.kemu.ac.ke'),
    ('SPU',   "St Paul's University",                                      'university', 'Kiambu',         'https://www.spu.ac.ke'),
    ('ANU',   'Africa Nazarene University',                                'university', 'Kajiado',        'https://www.anu.ac.ke'),
    ('MUA',   'The Management University of Africa',                       'university', 'Nairobi',        'https://www.mua.ac.ke'),
    ('AIU',   'Africa International University',                           'university', 'Nairobi',        'https://www.aiu.ac.ke'),
    ('KIRIRI','Kiriri Women\'s University of Science and Technology',      'university', 'Nairobi',        'https://www.kiriri.ac.ke'),
    ('PACU',  'Pan Africa Christian University',                           'university', 'Nairobi',        'https://www.pacuniversity.ac.ke'),
    ('GLUK',  'Great Lakes University of Kisumu',                          'university', 'Kisumu',         'https://www.gluk.ac.ke'),
    ('BARATON','University of Eastern Africa, Baraton',                    'university', 'Uasin Gishu',    'https://www.uea.ac.ke'),
    ('PUEA',  'The Presbyterian University of East Africa',                'university', 'Nairobi',        'https://www.puea.ac.ke'),
    ('TANGAZA','Tangaza University College',                               'university', 'Nairobi',        'https://www.tangaza.ac.ke'),
    ('PIONEER','Pioneer International University',                         'university', 'Nairobi',        'https://www.pioneerinternational.ac.ke'),
    ('RIARA', 'Riara University',                                          'university', 'Nairobi',        'https://www.riarauniversity.ac.ke'),
    ('UMMA',  'Umma University',                                           'university', 'Kajiado',        'https://www.umma.ac.ke'),
    ('SCOTT', 'Scott Christian University',                                'university', 'Marsabit',       'https://www.scott.ac.ke'),
    ('UZIMA', 'Uzima University College',                                  'university', 'Kisumu',         'https://www.uzimauniversity.ac.ke'),
    ('LUKENYA','Lukenya University',                                       'university', 'Machakos',       'https://www.lukenya.ac.ke'),
    ('ILU',   'International Leadership University',                       'university', 'Nairobi',        'https://www.ilu.ac.ke'),
    ('INOORERO','Inoorero University',                                     'university', 'Nairobi',        'https://www.inoorero.ac.ke'),
    ('KHEU',  'Kenya Highlands Evangelical University',                    'university', 'Kericho',        'https://www.khe.ac.ke'),
    ('KAGEAST','KAG East University',                                      'university', 'Nairobi',        ''),
    ('GRETSA','Gretsa University',                                         'university', 'Kiambu',         ''),
    ('MARIST','Marist International University College',                   'university', 'Nairobi',        'https://www.marist.ac.ke'),
    ('REGPACIS','Regina Pacis University College',                         'university', 'Nairobi',        ''),
    ('ALU',   'African Leadership University',                             'university', 'Nairobi',        'https://www.alueducation.com'),
    ('TEAU',  'The East Africa University',                                'university', 'Isiolo',         ''),
    ('RAF',   'RAF International University',                              'university', 'Nairobi',        ''),
    # ── National Polytechnics & Technical Colleges ─────────────────────
    ('ELDOPOLY','Eldoret Polytechnic',                                     'tvet',       'Uasin Gishu',    ''),
    ('KABETEPOLY','Kabete National Polytechnic',                           'tvet',       'Nairobi',        ''),
    ('KISIPOLY','Kisii National Polytechnic',                              'tvet',       'Kisii',          ''),
    ('KSMPOLY','Kisumu Polytechnic',                                       'tvet',       'Kisumu',         ''),
    ('KITALEPOLY','Kitale National Polytechnic',                           'tvet',       'Trans Nzoia',    ''),
    ('NYERIPOLY','Nyeri National Polytechnic',                             'tvet',       'Nyeri',          ''),
    ('NAKPOLY','Nakuru National Polytechnic',                              'tvet',       'Nakuru',         ''),
    ('MOMBTTI','Mombasa Technical Training Institute',                     'tvet',       'Mombasa',        ''),
    ('BARINGO','Baringo Technical College',                                'tvet',       'Baringo',        ''),
    ('KIST',   'Kiambu Institute of Science and Technology',               'tvet',       'Kiambu',         ''),
    ('CIT',    'Coast Institute of Technology',                            'tvet',       'Mombasa',        ''),
    ('KITI',   'Kenya Industrial Training Institute',                      'tvet',       'Nairobi',        ''),
    ('KIMC',   'Kenya Institute of Mass Communication',                    'college',    'Nairobi',        'https://www.kimc.ac.ke'),
    ('KMTC',   'Kenya Medical Training College',                           'college',    'Nairobi',        'https://www.kmtc.ac.ke'),
    ('KSA',    'Kenya School of Agriculture',                              'college',    'Kiambu',         ''),
    ('KEWI',   'Kenya Water Institute',                                    'college',    'Nairobi',        'https://www.kewi.or.ke'),
    ('EASA',   'East African School of Aviation',                          'college',    'Nairobi',        ''),
    ('KFC',    'Kenya Forestry College',                                   'college',    'Nyeri',          ''),
    ('CTTR',   'Centre for Tourism Training and Research',                 'college',    'Nairobi',        ''),
    ('KTTC',   'Kenya Technical Trainers College',                         'college',    'Nairobi',        ''),
    ('BAC',    'Bukura Agricultural College',                              'college',    'Kakamega',       ''),
    ('KIHBT',  'Kenya Institute of Highways and Building Technology',      'college',    'Nairobi',        'https://www.kihbt.go.ke'),
    ('KWSTI',  'Kenya Wildlife Service Training Institute',                'college',    'Nakuru',         ''),
    ('KESRA',  'Kenya School of Revenue Administration',                   'college',    'Nairobi',        'https://www.kesra.or.ke'),
    ('FCK',    'Friends College Kaimosi',                                  'college',    'Vihiga',         ''),
    ('JNTI',   'Jeremiah Nyagah Technical Institute',                      'tvet',       'Embu',           ''),
    ('KICDT',  'Kisumu Institute of Community Development Training',       'college',    'Kisumu',         ''),
    ('KCNP',   'Kenya Coast National Polytechnic',                         'tvet',       'Mombasa',        ''),
]


class Command(BaseCommand):
    help = 'Seed ~100 real Kenyan institutions from KUCCPS for demo use.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing KUCCPS-DEMO records before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Institution.objects.filter(source_scope=SCOPE).delete()
            self.stdout.write(f'Cleared {deleted} existing demo institution(s).')

        created = skipped = 0
        for ext_key, name, inst_type, county, website in INSTITUTIONS:
            if Institution.objects.filter(source_scope=SCOPE, external_key=ext_key).exists():
                skipped += 1
                continue
            inst = Institution(
                source_scope=SCOPE,
                external_key=ext_key,
                name=name,
                institution_type=inst_type,
                county=county,
                website_url=website,
                source_url=SOURCE_URL,
                education_framework=FRAMEWORK,
                admission_cycle=CYCLE,
                effective_date=EFFECTIVE,
                verification_status=STATUS,
            )
            inst.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created}  Skipped (already exist): {skipped}'
        ))
