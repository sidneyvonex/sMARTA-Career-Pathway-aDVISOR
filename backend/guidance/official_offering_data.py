from accounts.official_school_data import COUNTY_SUB_COUNTIES


OFFICIAL_COMBINATIONS_ENDPOINT = (
    'https://selection.education.go.ke/api/open/subject-combinations-by-track'
)
OFFICIAL_OFFERINGS_ENDPOINT = (
    'https://selection.education.go.ke/api/open/schools-by-combination'
)
OFFICIAL_CATALOGUE_URL = (
    'https://selection.education.go.ke/uploads/'
    '1750333580754-subject-combinations-1750333524964.pdf'
)

ROLLOUT_COUNTIES = tuple(COUNTY_SUB_COUNTIES)
OFFICIAL_COUNTY_QUERY_VALUES = {
    **{county: county.upper() for county in ROLLOUT_COUNTIES},
    'muranga': "MURANG'A",
}

OFFICIAL_TRACKS = {
    'PURE SCIENCES': 'PURE-SCIENCES',
    'APPLIED SCIENCES': 'APPLIED-SCIENCES',
    'TECHNICAL STUDIES': 'TECHNICAL-STUDIES',
    'LANGUAGES & LITERATURE': 'LANGUAGES-LITERATURE',
    'HUMANITIES & BUSINESS STUDIES': 'HUMANITIES-BUSINESS',
    'ARTS': 'ARTS',
    'SPORTS': 'SPORTS-RECREATION',
}

OFFICIAL_SUBJECT_CODES = {
    'Agriculture': 'AGR10',
    'Arabic': 'ARA10',
    'Aviation': 'AVT10',
    'Biology': 'BIO10',
    'Building & Construction': 'BCN10',
    'Business Studies': 'BST10',
    'Chemistry': 'CHE10',
    'Christian Religious Education': 'CHR10',
    # The Ministry endpoint currently returns "Code Mathematics" for one row.
    'Code Mathematics': 'CMT10',
    'Computer Studies': 'CPS10',
    'Core Mathematics': 'CMT10',
    'Electricity': 'ELC10',
    'Fasihi ya Kiswahili': 'FKI10',
    'Fine Arts': 'FAR10',
    'French': 'FRN10',
    'General Science': 'GSC10',
    'Geography': 'GEO10',
    'German': 'GER10',
    'Hindu Religious Education': 'HRE10',
    'History & Citizenship': 'HCT10',
    'Home Science': 'HOM10',
    'Indigenous Language': 'IND10',
    'Islamic Religious Education': 'IRE10',
    'Kenya Sign Language': 'KSL10',
    'Literature in English': 'LIE10',
    # Preserve the Ministry label in evidence; use the standard spelling locally.
    'Mandarine Chinese': 'MCH10',
    'Marine & Fisheries': 'MFT10',
    'Media Technology': 'MDT10',
    'Metal Work': 'MTW10',
    'Music & Dance': 'MDA10',
    'Physics': 'PHY10',
    'Power Mechanics': 'PME10',
    'Sports & Recreation': 'SRE10',
    'Theatre & Film': 'TFM10',
    'Wood Work': 'WDW10',
}

# UUIDs are resolved from the Ministry's public combination endpoint. They are
# source identifiers for queries, not locally invented catalogue identifiers.
OFFICIAL_COMBINATIONS = {
    'ST1042': {
        'id': '0cecfbd4-be11-4b36-afbf-9461b3f4f2c0',
        'track': 'PURE SCIENCES',
        'title': 'Agriculture,Biology,Chemistry',
    },
    'ST2007': {
        'id': '01f2264d-bb70-4342-8fe3-20455f3d1dab',
        'track': 'APPLIED SCIENCES',
        'title': 'Business Studies,Computer Studies,Physics',
    },
    'ST2067': {
        'id': '08cc411d-bb7c-46ac-bb73-581f94b1f311',
        'track': 'APPLIED SCIENCES',
        'title': 'Agriculture,Computer Studies,Physics',
    },
    'ST3074': {
        'id': '080d13b2-3cfe-45c0-a5b1-e1e139e06474',
        'track': 'TECHNICAL STUDIES',
        'title': 'Computer Studies,General Science,Media Technology',
    },
    'SS1006': {
        'id': '00c47cf5-d705-4bfe-ae8e-e90e83064146',
        'track': 'LANGUAGES & LITERATURE',
        'title': 'Arabic,Computer Studies,French',
    },
    'SS2019': {
        'id': '04c1e4c6-4212-4a58-8b12-4a23a817b5d4',
        'track': 'HUMANITIES & BUSINESS STUDIES',
        'title': (
            'Christian Religious Education,Geography,History & Citizenship'
        ),
    },
    'SS2033': {
        'id': '017eb67f-85db-4e78-939c-2a9b1b3d56b6',
        'track': 'HUMANITIES & BUSINESS STUDIES',
        'title': (
            'Computer Studies,Geography,Islamic Religious Education'
        ),
    },
    'AS1021': {
        'id': '04ea6325-cde4-47f3-99cf-33d1e1899d6c',
        'track': 'ARTS',
        'title': 'Computer Studies,Fine Arts,Music & Dance',
    },
    'AS1049': {
        'id': '0a667d78-92ce-4403-b0c4-5946aba878bc',
        'track': 'ARTS',
        'title': 'Literature in English,Music & Dance,Theatre & Film',
    },
    'AS2009': {
        'id': '000d9223-9952-4ad5-849e-e7988ea758ad',
        'track': 'SPORTS',
        'title': 'Biology,Geography,Sports & Recreation',
    },
}
