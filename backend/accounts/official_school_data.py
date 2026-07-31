OFFICIAL_DIRECTORY_URL = 'https://selection.education.go.ke/schools'
OFFICIAL_SEARCH_ENDPOINT = (
    'https://selection.education.go.ke/api/open/school-search'
)

COUNTY_SUB_COUNTIES = {
    'kiambu': (
        'Thika East',
        'Thika West',
        'Gatundu South',
        'Gatundu North',
        'Ruiru',
        'Githunguri',
        'Kiambu',
        'Kiambaa',
        'Kabete',
        'Kikuyu',
        'Juja',
        'Limuru',
        'Lari',
        'Githurai',
        'Ndeiya',
    ),
    'muranga': (
        'Kangema',
        'Mathioya',
        'Kahuro',
        'Kigumo',
        'Ithanga/Kakuzi',
        'Kandara',
        'Gatanga',
        "Murang'a South",
        "Murang'a East",
        'Muranga East',
    ),
    'nyeri': (
        'Tetu',
        'Nyeri Central',
        'Kieni West',
        'Kieni East',
        'Mathira West',
        'Mathira East',
        'Nyeri South',
        'Mukurwe-ini',
        'Mukurweini',
    ),
    'kirinyaga': (
        'Kirinyaga Central',
        'Mwea East',
        'Mwea West',
        'Kirinyaga East',
        'Kirinyaga west',
    ),
    'nyandarua': (
        'South Kinangop',
        'North Kinangop',
        'Kipipiri',
        'Mirangine',
        'Nyandarua West',
        'Nyandarua Central',
        'Nyandarua North',
        'Gathanji',
        'Aberdare',
        'Wanjohi',
    ),
}


def normalize_whitespace(value):
    return ' '.join(str(value or '').split())

