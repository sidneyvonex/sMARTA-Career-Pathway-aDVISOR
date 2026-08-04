"""
Seed ~350 real Kenyan degree, diploma and certificate programmes across the
demo institutions seeded by seed_demo_institutions.

Run:
    python manage.py seed_demo_programmes
    python manage.py seed_demo_programmes --clear   # wipe existing demo records first
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from tertiary.models import Institution, Programme

SCOPE = 'KUCCPS-DEMO'
SOURCE_URL = 'https://kuccps.net'
FRAMEWORK = 'CBC'
CYCLE = '2024/2025'
EFFECTIVE = date(2024, 1, 1)
STATUS = 'verified'

# (prog_suffix, code, name, description)
# external_key = f'{INST_KEY}-{prog_suffix}'
#
# Grouped by institution external_key.  Programmes that many universities share
# (e.g. BCom, BEd Science) are given the same suffix so the naming stays
# consistent even though each copy gets its own unique external_key.

PROGRAMMES_BY_INSTITUTION = {
    # ══════════════════════════════════════════════════════════════════════
    # MAJOR PUBLIC UNIVERSITIES
    # ══════════════════════════════════════════════════════════════════════
    'UON': [
        ('MEDICINE',   'J001', 'Bachelor of Medicine and Surgery (MBChB)', 'Six-year programme training medical doctors; includes clinical rotations at KNH.'),
        ('LAW',        'J100', 'Bachelor of Laws (LLB)', 'Four-year programme covering common law, statute and constitutional law.'),
        ('ARCH',       'J200', 'Bachelor of Architecture', 'Five-year programme accredited by the Board of Registration of Architects and Quantity Surveyors.'),
        ('NURSING',    'J300', 'Bachelor of Science in Nursing', 'Four-year programme combining clinical practice and health sciences theory.'),
        ('PHARMACY',   'J400', 'Bachelor of Pharmacy (BPharm)', 'Four-year pharmaceutical sciences programme.'),
        ('CS',         'J500', 'Bachelor of Science in Computer Science', 'Covers algorithms, software engineering, AI and systems programming.'),
        ('EE',         'J600', 'Bachelor of Engineering (Electrical and Electronics)', 'Four-year engineering programme accredited by EBK.'),
        ('CIVIL',      'J601', 'Bachelor of Engineering (Civil)', 'Structural, water and transport engineering with industry attachments.'),
        ('BCOM',       'J700', 'Bachelor of Commerce', 'Covers accounting, marketing, management and finance.'),
        ('ECON',       'J800', 'Bachelor of Arts in Economics', 'Micro- and macroeconomic theory, econometrics and policy analysis.'),
        ('ACTUARIAL',  'J900', 'Bachelor of Science in Actuarial Science', 'Mathematics of risk, probability and financial modelling.'),
        ('ENV',        'J950', 'Bachelor of Science in Environmental Studies', 'Interdisciplinary study of environment, policy and sustainability.'),
    ],

    'KU': [
        ('BED_ARTS',   'E001', 'Bachelor of Education (Arts)', 'Trains secondary school teachers of arts and humanities subjects.'),
        ('BED_SCI',    'E002', 'Bachelor of Education (Science)', 'Trains secondary school teachers of science subjects.'),
        ('CS',         'E100', 'Bachelor of Science in Computer Science', 'Software development, networks and information systems.'),
        ('NURSING',    'E200', 'Bachelor of Science in Nursing', 'Clinical nursing and community health sciences.'),
        ('BCOM',       'E300', 'Bachelor of Commerce', 'Business administration, accounting and marketing.'),
        ('BBA',        'E301', 'Bachelor of Business Administration', 'Management, entrepreneurship and strategic planning.'),
        ('MATH',       'E400', 'Bachelor of Science in Mathematics', 'Pure and applied mathematics with computing.'),
        ('LAW',        'E500', 'Bachelor of Laws (LLB)', 'Legal studies with Kenyan and East African context.'),
        ('PH',         'E600', 'Bachelor of Science in Public Health', 'Epidemiology, biostatistics, health policy and promotion.'),
        ('COMM',       'E700', 'Bachelor of Arts in Communication', 'Journalism, public relations and digital media.'),
        ('ENV',        'E800', 'Bachelor of Science in Environmental Studies', 'Conservation, environmental policy and ecology.'),
    ],

    'JKUAT': [
        ('CS',         'F001', 'Bachelor of Science in Computer Science', 'Software engineering, AI and cloud computing.'),
        ('IT',         'F002', 'Bachelor of Science in Information Technology', 'Systems administration, networking and cybersecurity.'),
        ('CIVIL',      'F100', 'Bachelor of Engineering (Civil)', 'Infrastructure design, geotechnics and water resources.'),
        ('EE',         'F101', 'Bachelor of Engineering (Electrical and Electronics)', 'Power systems, electronics and embedded systems.'),
        ('MECH',       'F102', 'Bachelor of Engineering (Mechanical)', 'Thermodynamics, manufacturing and machine design.'),
        ('CHEM_ENG',   'F103', 'Bachelor of Engineering (Chemical)', 'Process engineering, materials and industrial chemistry.'),
        ('FOOD',       'F200', 'Bachelor of Science in Food Science and Technology', 'Food processing, quality control and nutrition.'),
        ('AGRI',       'F300', 'Bachelor of Science in Agriculture', 'Agronomy, soil science and crop production.'),
        ('PHARMACY',   'F400', 'Bachelor of Pharmacy (BPharm)', 'Pharmaceutical sciences and drug development.'),
        ('ACTUARIAL',  'F500', 'Bachelor of Science in Actuarial Science', 'Risk modelling, insurance mathematics and statistics.'),
    ],

    'MU': [
        ('MEDICINE',   'G001', 'Bachelor of Medicine and Surgery (MBChB)', 'Medical training at Moi Teaching and Referral Hospital.'),
        ('LAW',        'G100', 'Bachelor of Laws (LLB)', 'Legal practice with focus on East African jurisprudence.'),
        ('BED_ARTS',   'G200', 'Bachelor of Education (Arts)', 'Arts teacher training for secondary schools.'),
        ('BED_SCI',    'G201', 'Bachelor of Education (Science)', 'Science teacher training for secondary schools.'),
        ('CS',         'G300', 'Bachelor of Science in Computer Science', 'Computing, software development and data science.'),
        ('BCOM',       'G400', 'Bachelor of Commerce', 'Accounting, finance and business management.'),
        ('AGRI',       'G500', 'Bachelor of Science in Agriculture', 'Crop science, animal production and agribusiness.'),
        ('NURSING',    'G600', 'Bachelor of Science in Nursing', 'Clinical nursing, midwifery and community health.'),
        ('CIVIL',      'G700', 'Bachelor of Engineering (Civil)', 'Structural and environmental engineering.'),
        ('ENV',        'G800', 'Bachelor of Science in Environmental Studies', 'Natural resource management and environmental law.'),
    ],

    'EGU': [
        ('AGRI',       'H001', 'Bachelor of Science in Agriculture', 'Crop production, agronomy and soil science.'),
        ('FOOD',       'H002', 'Bachelor of Science in Food Science and Technology', 'Food analysis, preservation and nutrition.'),
        ('BED_ARTS',   'H100', 'Bachelor of Education (Arts)', 'Humanities teacher education.'),
        ('BED_SCI',    'H101', 'Bachelor of Education (Science)', 'Science teacher education.'),
        ('BCOM',       'H200', 'Bachelor of Commerce', 'Business management and accounting.'),
        ('HORT',       'H300', 'Bachelor of Science in Horticulture', 'Fruit, vegetable and ornamental crop production.'),
        ('ENV',        'H400', 'Bachelor of Science in Environmental Studies', 'Ecology, conservation and environmental policy.'),
        ('NURSING',    'H500', 'Bachelor of Science in Nursing', 'Nursing sciences and community health.'),
        ('ANIMAL',     'H600', 'Bachelor of Science in Animal Science', 'Livestock production, veterinary pathology and animal nutrition.'),
        ('ECON',       'H700', 'Bachelor of Arts in Economics', 'Agricultural economics and rural development.'),
    ],

    'MSU': [
        ('BED_ARTS',   'I001', 'Bachelor of Education (Arts)', 'Humanities teacher education.'),
        ('BED_SCI',    'I002', 'Bachelor of Education (Science)', 'Science teacher education.'),
        ('CS',         'I100', 'Bachelor of Science in Computer Science', 'Software engineering and information systems.'),
        ('BCOM',       'I200', 'Bachelor of Commerce', 'Finance, accounting and marketing.'),
        ('PH',         'I300', 'Bachelor of Science in Public Health', 'Community health and disease surveillance.'),
        ('ECON',       'I400', 'Bachelor of Arts in Economics', 'Economic theory, statistics and policy.'),
        ('BIO',        'I500', 'Bachelor of Science in Biological Sciences', 'Genetics, microbiology and ecology.'),
        ('MATH',       'I600', 'Bachelor of Science in Mathematics', 'Analysis, algebra and applied mathematics.'),
    ],

    'MMUST': [
        ('CS',         'K001', 'Bachelor of Science in Computer Science', 'Networks, software development and AI.'),
        ('BED_ARTS',   'K100', 'Bachelor of Education (Arts)', 'Arts teacher training.'),
        ('BED_SCI',    'K101', 'Bachelor of Education (Science)', 'Science teacher training.'),
        ('NURSING',    'K200', 'Bachelor of Science in Nursing', 'Nursing sciences.'),
        ('AGRI',       'K300', 'Bachelor of Science in Agriculture', 'Crop and animal sciences.'),
        ('CIVIL',      'K400', 'Bachelor of Engineering (Civil)', 'Civil and structural engineering.'),
        ('ENV',        'K500', 'Bachelor of Science in Environmental Studies', 'Environmental conservation and management.'),
        ('BCOM',       'K600', 'Bachelor of Commerce', 'Business and financial management.'),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # TECHNICAL UNIVERSITIES
    # ══════════════════════════════════════════════════════════════════════
    'TUK': [
        ('CS',         'L001', 'Bachelor of Science in Computer Science', 'Software, networks and systems.'),
        ('IT',         'L002', 'Bachelor of Science in Information Technology', 'IT management and security.'),
        ('EE',         'L100', 'Bachelor of Engineering (Electrical and Electronics)', 'Power and control engineering.'),
        ('CIVIL',      'L101', 'Bachelor of Engineering (Civil)', 'Structural and transport engineering.'),
        ('MECH',       'L102', 'Bachelor of Engineering (Mechanical)', 'Manufacturing and thermal systems.'),
        ('ARCH',       'L200', 'Bachelor of Science in Architecture', 'Architectural design and construction.'),
        ('BCOM',       'L300', 'Bachelor of Commerce', 'Business and entrepreneurship.'),
        ('SURVEY',     'L400', 'Bachelor of Science in Geospatial Engineering', 'Land surveying, GIS and remote sensing.'),
    ],

    'TUM': [
        ('CS',         'M001', 'Bachelor of Science in Computer Science', 'Software and network engineering.'),
        ('EE',         'M100', 'Bachelor of Engineering (Electrical and Electronics)', 'Electrical power and communication systems.'),
        ('CIVIL',      'M101', 'Bachelor of Engineering (Civil)', 'Coastal and port engineering.'),
        ('MECH',       'M102', 'Bachelor of Engineering (Mechanical)', 'Marine and mechanical systems.'),
        ('MARITIME',   'M200', 'Bachelor of Science in Maritime Management', 'Port operations, shipping and logistics.'),
        ('BBA',        'M300', 'Bachelor of Business Administration', 'Business strategy and supply chain.'),
    ],

    'DKUT': [
        ('CS',         'N001', 'Bachelor of Science in Computer Science', 'Embedded systems, AI and software engineering.'),
        ('EE',         'N100', 'Bachelor of Engineering (Electrical and Electronics)', 'Electronics and control systems.'),
        ('CIVIL',      'N101', 'Bachelor of Engineering (Civil)', 'Infrastructure and water resources.'),
        ('MECH',       'N102', 'Bachelor of Engineering (Mechanical)', 'Manufacturing and energy systems.'),
        ('IT',         'N200', 'Bachelor of Science in Information Technology', 'Systems and network management.'),
        ('BBA',        'N300', 'Bachelor of Business Administration', 'Technology management.'),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # MEDIUM PUBLIC UNIVERSITIES
    # ══════════════════════════════════════════════════════════════════════
    'JOOUST': [
        ('AGRI',       'O001', 'Bachelor of Science in Agriculture', ''),
        ('BED_SCI',    'O002', 'Bachelor of Education (Science)', ''),
        ('CS',         'O003', 'Bachelor of Science in Computer Science', ''),
        ('NURSING',    'O004', 'Bachelor of Science in Nursing', ''),
        ('ENV',        'O005', 'Bachelor of Science in Environmental Studies', ''),
        ('BBA',        'O006', 'Bachelor of Business Administration', ''),
    ],

    'SEKU': [
        ('BED_ARTS',   'P001', 'Bachelor of Education (Arts)', ''),
        ('CS',         'P002', 'Bachelor of Science in Computer Science', ''),
        ('AGRI',       'P003', 'Bachelor of Science in Agriculture', ''),
        ('ENV',        'P004', 'Bachelor of Science in Environmental Studies', ''),
        ('BCOM',       'P005', 'Bachelor of Commerce', ''),
    ],

    'MUST': [
        ('CS',         'Q001', 'Bachelor of Science in Computer Science', ''),
        ('EE',         'Q002', 'Bachelor of Engineering (Electrical and Electronics)', ''),
        ('CIVIL',      'Q003', 'Bachelor of Engineering (Civil)', ''),
        ('BED_SCI',    'Q004', 'Bachelor of Education (Science)', ''),
        ('FOOD',       'Q005', 'Bachelor of Science in Food Science and Technology', ''),
        ('BCOM',       'Q006', 'Bachelor of Commerce', ''),
    ],

    'KSU': [
        ('BED_ARTS',   'R001', 'Bachelor of Education (Arts)', ''),
        ('BED_SCI',    'R002', 'Bachelor of Education (Science)', ''),
        ('BCOM',       'R003', 'Bachelor of Commerce', ''),
        ('CS',         'R004', 'Bachelor of Science in Computer Science', ''),
        ('NURSING',    'R005', 'Bachelor of Science in Nursing', ''),
        ('ENV',        'R006', 'Bachelor of Science in Environmental Studies', ''),
    ],

    'MMU': [
        ('CS',         'S001', 'Bachelor of Science in Computer Science', ''),
        ('IT',         'S002', 'Bachelor of Science in Information Technology', ''),
        ('COMM',       'S003', 'Bachelor of Arts in Communication', ''),
        ('BBA',        'S004', 'Bachelor of Business Administration', ''),
        ('EE',         'S005', 'Bachelor of Engineering (Electrical and Electronics)', ''),
    ],

    'UOE': [
        ('AGRI',       'T001', 'Bachelor of Science in Agriculture', ''),
        ('BED_SCI',    'T002', 'Bachelor of Education (Science)', ''),
        ('CS',         'T003', 'Bachelor of Science in Computer Science', ''),
        ('ENV',        'T004', 'Bachelor of Science in Environmental Studies', ''),
        ('BBA',        'T005', 'Bachelor of Business Administration', ''),
    ],

    'PU': [
        ('CS',         'U001', 'Bachelor of Science in Computer Science', ''),
        ('ENV',        'U002', 'Bachelor of Science in Environmental Studies', ''),
        ('BED_ARTS',   'U003', 'Bachelor of Education (Arts)', ''),
        ('NURSING',    'U004', 'Bachelor of Science in Nursing', ''),
        ('BCOM',       'U005', 'Bachelor of Commerce', ''),
    ],

    'MARU': [
        ('AGRI',       'V001', 'Bachelor of Science in Agriculture', ''),
        ('BED_ARTS',   'V002', 'Bachelor of Education (Arts)', ''),
        ('CS',         'V003', 'Bachelor of Science in Computer Science', ''),
        ('NURSING',    'V004', 'Bachelor of Science in Nursing', ''),
        ('BCOM',       'V005', 'Bachelor of Commerce', ''),
    ],

    'MKSU': [
        ('CS',         'W001', 'Bachelor of Science in Computer Science', ''),
        ('BED_ARTS',   'W002', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'W003', 'Bachelor of Commerce', ''),
        ('CIVIL',      'W004', 'Bachelor of Engineering (Civil)', ''),
        ('ENV',        'W005', 'Bachelor of Science in Environmental Studies', ''),
    ],

    'KAU': [
        ('BED_ARTS',   'X001', 'Bachelor of Education (Arts)', ''),
        ('AGRI',       'X002', 'Bachelor of Science in Agriculture', ''),
        ('CS',         'X003', 'Bachelor of Science in Computer Science', ''),
        ('BCOM',       'X004', 'Bachelor of Commerce', ''),
    ],

    'LU': [
        ('BED_ARTS',   'Y001', 'Bachelor of Education (Arts)', ''),
        ('CS',         'Y002', 'Bachelor of Science in Computer Science', ''),
        ('ENV',        'Y003', 'Bachelor of Science in Environmental Studies', ''),
        ('BCOM',       'Y004', 'Bachelor of Commerce', ''),
    ],

    'CHUKA': [
        ('BED_ARTS',   'Z001', 'Bachelor of Education (Arts)', ''),
        ('CS',         'Z002', 'Bachelor of Science in Computer Science', ''),
        ('BCOM',       'Z003', 'Bachelor of Commerce', ''),
        ('ENV',        'Z004', 'Bachelor of Science in Environmental Studies', ''),
    ],

    'KIBABII': [
        ('CS',         'AA001', 'Bachelor of Science in Computer Science', ''),
        ('BED_ARTS',   'AA002', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'AA003', 'Bachelor of Commerce', ''),
        ('ENV',        'AA004', 'Bachelor of Science in Environmental Studies', ''),
    ],

    'KYU': [
        ('CS',         'AB001', 'Bachelor of Science in Computer Science', ''),
        ('AGRI',       'AB002', 'Bachelor of Science in Agriculture', ''),
        ('BCOM',       'AB003', 'Bachelor of Commerce', ''),
        ('BED_SCI',    'AB004', 'Bachelor of Education (Science)', ''),
    ],

    'TTU': [
        ('CS',         'AC001', 'Bachelor of Science in Computer Science', ''),
        ('ENV',        'AC002', 'Bachelor of Science in Environmental Studies', ''),
        ('BED_ARTS',   'AC003', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'AC004', 'Bachelor of Commerce', ''),
    ],

    'RU': [
        ('BED_ARTS',   'AD001', 'Bachelor of Education (Arts)', ''),
        ('CS',         'AD002', 'Bachelor of Science in Computer Science', ''),
        ('AGRI',       'AD003', 'Bachelor of Science in Agriculture', ''),
        ('BCOM',       'AD004', 'Bachelor of Commerce', ''),
    ],

    'GU': [
        ('BED_ARTS',   'AE001', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'AE002', 'Bachelor of Commerce', ''),
        ('CS',         'AE003', 'Bachelor of Science in Computer Science', ''),
    ],

    'CUK': [
        ('BCOM',       'AF001', 'Bachelor of Commerce (Cooperatives)', 'Cooperative management, business and finance.'),
        ('BBA',        'AF002', 'Bachelor of Business Administration', ''),
        ('CS',         'AF003', 'Bachelor of Science in Computer Science', ''),
        ('AGRI',       'AF004', 'Bachelor of Science in Agriculture', ''),
    ],

    'UOK': [
        ('AGRI',       'AG001', 'Bachelor of Science in Agriculture', ''),
        ('BED_ARTS',   'AG002', 'Bachelor of Education (Arts)', ''),
        ('CS',         'AG003', 'Bachelor of Science in Computer Science', ''),
        ('ENV',        'AG004', 'Bachelor of Science in Environmental Studies', ''),
    ],

    'EMBUNI': [
        ('CS',         'AH001', 'Bachelor of Science in Computer Science', ''),
        ('BED_SCI',    'AH002', 'Bachelor of Education (Science)', ''),
        ('AGRI',       'AH003', 'Bachelor of Science in Agriculture', ''),
        ('BCOM',       'AH004', 'Bachelor of Commerce', ''),
    ],

    'MUT': [
        ('CS',         'AI001', 'Bachelor of Science in Computer Science', ''),
        ('EE',         'AI002', 'Bachelor of Engineering (Electrical and Electronics)', ''),
        ('CIVIL',      'AI003', 'Bachelor of Engineering (Civil)', ''),
        ('BCOM',       'AI004', 'Bachelor of Commerce', ''),
    ],

    'KSUC': [
        ('BED_ARTS',   'AJ001', 'Bachelor of Education (Arts)', ''),
        ('AGRI',       'AJ002', 'Bachelor of Science in Agriculture', ''),
        ('BCOM',       'AJ003', 'Bachelor of Commerce', ''),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # CONSTITUENT COLLEGES
    # ══════════════════════════════════════════════════════════════════════
    'ALUPE': [
        ('NURSING',    'AK001', 'Bachelor of Science in Nursing', ''),
        ('BED_SCI',    'AK002', 'Bachelor of Education (Science)', ''),
        ('PH',         'AK003', 'Bachelor of Science in Public Health', ''),
    ],
    'KFUC': [
        ('BED_ARTS',   'AL001', 'Bachelor of Education (Arts)', ''),
        ('AGRI',       'AL002', 'Bachelor of Science in Agriculture', ''),
        ('CS',         'AL003', 'Bachelor of Science in Computer Science', ''),
    ],
    'TMBOYA': [
        ('BED_ARTS',   'AM001', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'AM002', 'Bachelor of Commerce', ''),
        ('PH',         'AM003', 'Bachelor of Science in Public Health', ''),
    ],
    'TURKUC': [
        ('BED_ARTS',   'AN001', 'Bachelor of Education (Arts)', ''),
        ('ENV',        'AN002', 'Bachelor of Science in Environmental Studies', ''),
    ],
    'BOMUC': [
        ('AGRI',       'AO001', 'Bachelor of Science in Agriculture', ''),
        ('BED_ARTS',   'AO002', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'AO003', 'Bachelor of Commerce', ''),
    ],
    'THARUC': [
        ('BED_ARTS',   'AP001', 'Bachelor of Education (Arts)', ''),
        ('AGRI',       'AP002', 'Bachelor of Science in Agriculture', ''),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # MAJOR PRIVATE UNIVERSITIES
    # ══════════════════════════════════════════════════════════════════════
    'USIU': [
        ('BBA',        'B001', 'Bachelor of Business Administration', 'International business with global management focus.'),
        ('CS',         'B002', 'Bachelor of Science in Computer Science', 'Software engineering and AI.'),
        ('COMM',       'B003', 'Bachelor of Arts in Communication', 'Journalism and strategic communication.'),
        ('ECON',       'B004', 'Bachelor of Arts in Economics', 'International economics and development.'),
        ('PSYCH',      'B005', 'Bachelor of Science in Psychology', 'Human behaviour, counselling and organisational psychology.'),
        ('IT',         'B006', 'Bachelor of Science in Information Technology', 'Cybersecurity and cloud computing.'),
    ],

    'MKU': [
        ('NURSING',    'C001', 'Bachelor of Science in Nursing', ''),
        ('MEDICINE',   'C002', 'Bachelor of Medicine and Surgery (MBChB)', ''),
        ('BBA',        'C003', 'Bachelor of Business Administration', ''),
        ('CS',         'C004', 'Bachelor of Science in Computer Science', ''),
        ('LAW',        'C005', 'Bachelor of Laws (LLB)', ''),
        ('PHARMACY',   'C006', 'Bachelor of Pharmacy (BPharm)', ''),
    ],

    'KABARAK': [
        ('LAW',        'D001', 'Bachelor of Laws (LLB)', ''),
        ('NURSING',    'D002', 'Bachelor of Science in Nursing', ''),
        ('BED_ARTS',   'D003', 'Bachelor of Education (Arts)', ''),
        ('BBA',        'D004', 'Bachelor of Business Administration', ''),
        ('CS',         'D005', 'Bachelor of Science in Computer Science', ''),
    ],

    'DAYSTAR': [
        ('COMM',       'DA001', 'Bachelor of Arts in Communication', ''),
        ('BBA',        'DA002', 'Bachelor of Business Administration', ''),
        ('CS',         'DA003', 'Bachelor of Science in Computer Science', ''),
        ('PSYCH',      'DA004', 'Bachelor of Science in Psychology', ''),
    ],

    'CUEA': [
        ('LAW',        'CA001', 'Bachelor of Laws (LLB)', ''),
        ('BED_ARTS',   'CA002', 'Bachelor of Education (Arts)', ''),
        ('NURSING',    'CA003', 'Bachelor of Science in Nursing', ''),
        ('BBA',        'CA004', 'Bachelor of Business Administration', ''),
        ('CS',         'CA005', 'Bachelor of Science in Computer Science', ''),
    ],

    'ZETECH': [
        ('CS',         'ZT001', 'Bachelor of Science in Computer Science', ''),
        ('IT',         'ZT002', 'Bachelor of Science in Information Technology', ''),
        ('BBA',        'ZT003', 'Bachelor of Business Administration', ''),
        ('COMM',       'ZT004', 'Bachelor of Arts in Communication', ''),
    ],

    'KCAU': [
        ('BBA',        'KC001', 'Bachelor of Business Administration', ''),
        ('BCOM',       'KC002', 'Bachelor of Commerce', ''),
        ('IT',         'KC003', 'Bachelor of Science in Information Technology', ''),
        ('ACTUARIAL',  'KC004', 'Bachelor of Science in Actuarial Science', ''),
    ],

    'KEMU': [
        ('BED_ARTS',   'KM001', 'Bachelor of Education (Arts)', ''),
        ('NURSING',    'KM002', 'Bachelor of Science in Nursing', ''),
        ('BBA',        'KM003', 'Bachelor of Business Administration', ''),
        ('CS',         'KM004', 'Bachelor of Science in Computer Science', ''),
    ],

    'SPU': [
        ('COMM',       'SP001', 'Bachelor of Arts in Communication', ''),
        ('BED_ARTS',   'SP002', 'Bachelor of Education (Arts)', ''),
        ('BBA',        'SP003', 'Bachelor of Business Administration', ''),
        ('CS',         'SP004', 'Bachelor of Science in Computer Science', ''),
    ],

    'ANU': [
        ('NURSING',    'AN001X', 'Bachelor of Science in Nursing', ''),
        ('BBA',        'AN002X', 'Bachelor of Business Administration', ''),
        ('CS',         'AN003X', 'Bachelor of Science in Computer Science', ''),
    ],

    'MUA': [
        ('BBA',        'MU001', 'Bachelor of Business Administration', ''),
        ('BCOM',       'MU002', 'Bachelor of Commerce', ''),
        ('IT',         'MU003', 'Bachelor of Science in Information Technology', ''),
    ],

    'AIU': [
        ('THEOL',      'AI001X', 'Bachelor of Theology', 'Biblical studies and Christian ministry.'),
        ('BBA',        'AI002X', 'Bachelor of Business Administration', ''),
        ('CS',         'AI003X', 'Bachelor of Science in Computer Science', ''),
    ],

    'KIRIRI': [
        ('CS',         'KR001', 'Bachelor of Science in Computer Science', ''),
        ('NURSING',    'KR002', 'Bachelor of Science in Nursing', ''),
        ('BBA',        'KR003', 'Bachelor of Business Administration', ''),
    ],

    'PACU': [
        ('BBA',        'PA001', 'Bachelor of Business Administration', ''),
        ('COMM',       'PA002', 'Bachelor of Arts in Communication', ''),
        ('THEOL',      'PA003', 'Bachelor of Theology', ''),
    ],

    'GLUK': [
        ('NURSING',    'GL001', 'Bachelor of Science in Nursing', ''),
        ('PH',         'GL002', 'Bachelor of Science in Public Health', ''),
        ('BBA',        'GL003', 'Bachelor of Business Administration', ''),
    ],

    'BARATON': [
        ('NURSING',    'BR001', 'Bachelor of Science in Nursing', ''),
        ('BED_ARTS',   'BR002', 'Bachelor of Education (Arts)', ''),
        ('BBA',        'BR003', 'Bachelor of Business Administration', ''),
    ],

    'PUEA': [
        ('THEOL',      'PU001', 'Bachelor of Theology', ''),
        ('BED_ARTS',   'PU002', 'Bachelor of Education (Arts)', ''),
        ('BBA',        'PU003', 'Bachelor of Business Administration', ''),
    ],

    'TANGAZA': [
        ('COMM',       'TG001', 'Bachelor of Arts in Communication', ''),
        ('THEOL',      'TG002', 'Bachelor of Theology', ''),
        ('BBA',        'TG003', 'Bachelor of Business Administration', ''),
    ],

    'PIONEER': [
        ('BBA',        'PI001', 'Bachelor of Business Administration', ''),
        ('CS',         'PI002', 'Bachelor of Science in Computer Science', ''),
        ('BCOM',       'PI003', 'Bachelor of Commerce', ''),
    ],

    'RIARA': [
        ('LAW',        'RI001', 'Bachelor of Laws (LLB)', ''),
        ('BBA',        'RI002', 'Bachelor of Business Administration', ''),
        ('CS',         'RI003', 'Bachelor of Science in Computer Science', ''),
    ],

    'UMMA': [
        ('BED_ARTS',   'UM001', 'Bachelor of Education (Arts)', ''),
        ('BBA',        'UM002', 'Bachelor of Business Administration', ''),
        ('CS',         'UM003', 'Bachelor of Science in Computer Science', ''),
    ],

    'SCOTT': [
        ('BED_ARTS',   'SC001', 'Bachelor of Education (Arts)', ''),
        ('THEOL',      'SC002', 'Bachelor of Theology', ''),
        ('BBA',        'SC003', 'Bachelor of Business Administration', ''),
    ],

    'UZIMA': [
        ('NURSING',    'UZ001', 'Bachelor of Science in Nursing', ''),
        ('PH',         'UZ002', 'Bachelor of Science in Public Health', ''),
        ('BBA',        'UZ003', 'Bachelor of Business Administration', ''),
    ],

    'LUKENYA': [
        ('CS',         'LK001', 'Bachelor of Science in Computer Science', ''),
        ('BBA',        'LK002', 'Bachelor of Business Administration', ''),
    ],

    'ILU': [
        ('BBA',        'IL001', 'Bachelor of Business Administration', ''),
        ('THEOL',      'IL002', 'Bachelor of Theology', ''),
        ('CS',         'IL003', 'Bachelor of Science in Computer Science', ''),
    ],

    'INOORERO': [
        ('BBA',        'IN001', 'Bachelor of Business Administration', ''),
        ('CS',         'IN002', 'Bachelor of Science in Computer Science', ''),
    ],

    'KHEU': [
        ('BED_ARTS',   'KH001', 'Bachelor of Education (Arts)', ''),
        ('THEOL',      'KH002', 'Bachelor of Theology', ''),
        ('BBA',        'KH003', 'Bachelor of Business Administration', ''),
    ],

    'KAGEAST': [
        ('THEOL',      'KA001', 'Bachelor of Theology', ''),
        ('BBA',        'KA002', 'Bachelor of Business Administration', ''),
    ],

    'GRETSA': [
        ('BBA',        'GR001', 'Bachelor of Business Administration', ''),
        ('CS',         'GR002', 'Bachelor of Science in Computer Science', ''),
    ],

    'MARIST': [
        ('BED_ARTS',   'MA001', 'Bachelor of Education (Arts)', ''),
        ('BCOM',       'MA002', 'Bachelor of Commerce', ''),
    ],

    'REGPACIS': [
        ('NURSING',    'RP001', 'Bachelor of Science in Nursing', ''),
        ('BBA',        'RP002', 'Bachelor of Business Administration', ''),
    ],

    'ALU': [
        ('BBA',        'AL001X', 'Bachelor of Business Administration', 'Entrepreneurship and African leadership track.'),
        ('CS',         'AL002X', 'Bachelor of Science in Computer Science', ''),
    ],

    'TEAU': [
        ('BED_ARTS',   'TE001', 'Bachelor of Education (Arts)', ''),
        ('AGRI',       'TE002', 'Bachelor of Science in Agriculture', ''),
    ],

    'RAF': [
        ('BBA',        'RF001', 'Bachelor of Business Administration', ''),
        ('CS',         'RF002', 'Bachelor of Science in Computer Science', ''),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # NATIONAL POLYTECHNICS & TECHNICAL COLLEGES (Diploma programmes)
    # ══════════════════════════════════════════════════════════════════════
    'ELDOPOLY': [
        ('DIP_EE',     'EP001', 'Diploma in Electrical and Electronic Engineering', ''),
        ('DIP_CIVIL',  'EP002', 'Diploma in Civil Engineering', ''),
        ('DIP_MECH',   'EP003', 'Diploma in Mechanical Engineering', ''),
    ],
    'KABETEPOLY': [
        ('DIP_IT',     'KB001', 'Diploma in Information Technology', ''),
        ('DIP_EE',     'KB002', 'Diploma in Electrical and Electronic Engineering', ''),
        ('DIP_CIVIL',  'KB003', 'Diploma in Civil Engineering', ''),
    ],
    'KISIPOLY': [
        ('DIP_BIZ',    'KP001', 'Diploma in Business Management', ''),
        ('DIP_IT',     'KP002', 'Diploma in Information Technology', ''),
        ('DIP_EE',     'KP003', 'Diploma in Electrical Engineering', ''),
    ],
    'KSMPOLY': [
        ('DIP_IT',     'KSP001', 'Diploma in Information Technology', ''),
        ('DIP_BIZ',    'KSP002', 'Diploma in Business Management', ''),
        ('DIP_EE',     'KSP003', 'Diploma in Electrical Engineering', ''),
    ],
    'KITALEPOLY': [
        ('DIP_CIVIL',  'KTP001', 'Diploma in Civil Engineering', ''),
        ('DIP_EE',     'KTP002', 'Diploma in Electrical Engineering', ''),
        ('DIP_BIZ',    'KTP003', 'Diploma in Business Management', ''),
    ],
    'NYERIPOLY': [
        ('DIP_IT',     'NYP001', 'Diploma in Information Technology', ''),
        ('DIP_CIVIL',  'NYP002', 'Diploma in Civil Engineering', ''),
    ],
    'NAKPOLY': [
        ('DIP_EE',     'NAP001', 'Diploma in Electrical Engineering', ''),
        ('DIP_MECH',   'NAP002', 'Diploma in Mechanical Engineering', ''),
        ('DIP_IT',     'NAP003', 'Diploma in Information Technology', ''),
    ],
    'MOMBTTI': [
        ('DIP_CIVIL',  'MTI001', 'Diploma in Civil Engineering', ''),
        ('DIP_EE',     'MTI002', 'Diploma in Electrical Engineering', ''),
    ],
    'BARINGO': [
        ('DIP_IT',     'BAR001', 'Diploma in Information Technology', ''),
        ('DIP_BIZ',    'BAR002', 'Diploma in Business Management', ''),
    ],
    'KIST': [
        ('DIP_IT',     'KIS001', 'Diploma in Information Technology', ''),
        ('DIP_BIZ',    'KIS002', 'Diploma in Business Management', ''),
    ],
    'CIT': [
        ('DIP_CIVIL',  'CIT001', 'Diploma in Civil Engineering', ''),
        ('DIP_EE',     'CIT002', 'Diploma in Electrical Engineering', ''),
    ],
    'KITI': [
        ('DIP_EE',     'KIT001', 'Diploma in Electrical Engineering', ''),
        ('DIP_MECH',   'KIT002', 'Diploma in Mechanical Engineering', ''),
    ],
    'JNTI': [
        ('DIP_IT',     'JNT001', 'Diploma in Information Technology', ''),
        ('DIP_CIVIL',  'JNT002', 'Diploma in Civil Engineering', ''),
    ],
    'KCNP': [
        ('DIP_MARITIME','KCN001', 'Diploma in Maritime Studies', ''),
        ('DIP_EE',     'KCN002', 'Diploma in Electrical Engineering', ''),
    ],

    # ══════════════════════════════════════════════════════════════════════
    # SPECIALIST COLLEGES
    # ══════════════════════════════════════════════════════════════════════
    'KIMC': [
        ('BCOM_MEDIA', 'KI001', 'Bachelor of Arts in Journalism and Mass Communication', 'Print, broadcast and digital journalism.'),
        ('DIP_MEDIA',  'KI002', 'Diploma in Journalism', ''),
    ],
    'KMTC': [
        ('DIP_NURSING', 'KMT001', 'Diploma in Kenya Registered Community Health Nursing', ''),
        ('DIP_PHARM',  'KMT002', 'Diploma in Pharmacy', ''),
        ('DIP_MED_LAB','KMT003', 'Diploma in Medical Laboratory Sciences', ''),
        ('DIP_CLIN',   'KMT004', 'Diploma in Clinical Medicine and Surgery', ''),
    ],
    'KSA': [
        ('DIP_AGRI',   'KSA001', 'Diploma in Agriculture', ''),
        ('CERT_AGRI',  'KSA002', 'Certificate in Agriculture', ''),
    ],
    'KEWI': [
        ('DIP_WATER',  'KW001', 'Diploma in Water and Environmental Engineering', ''),
        ('CERT_WATER', 'KW002', 'Certificate in Water and Sanitation', ''),
    ],
    'EASA': [
        ('DIP_AV',     'EA001', 'Diploma in Aviation Management', ''),
        ('CERT_AV',    'EA002', 'Certificate in Aviation Operations', ''),
    ],
    'KFC': [
        ('DIP_FOREST', 'KF001', 'Diploma in Forestry', ''),
        ('CERT_FOREST','KF002', 'Certificate in Forestry', ''),
    ],
    'CTTR': [
        ('DIP_TOUR',   'CT001', 'Diploma in Tourism Management', ''),
        ('DIP_HOTEL',  'CT002', 'Diploma in Hotel and Hospitality Management', ''),
    ],
    'KTTC': [
        ('DIP_TECH_ED','KT001', 'Diploma in Technical Education', 'Trains TVET instructors.'),
        ('CERT_TECH',  'KT002', 'Certificate in Technical Education', ''),
    ],
    'BAC': [
        ('DIP_AGRI',   'BA001', 'Diploma in Agriculture', ''),
        ('CERT_AGRI',  'BA002', 'Certificate in Agribusiness', ''),
    ],
    'KIHBT': [
        ('DIP_CONST',  'KIH001', 'Diploma in Building and Construction Technology', ''),
        ('DIP_ROAD',   'KIH002', 'Diploma in Roads and Infrastructure', ''),
    ],
    'KWSTI': [
        ('DIP_WILD',   'KW001X', 'Diploma in Wildlife Management', ''),
        ('CERT_WILD',  'KW002X', 'Certificate in Wildlife Conservation', ''),
    ],
    'KESRA': [
        ('DIP_TAX',    'KE001', 'Diploma in Taxation', ''),
        ('CERT_CUSTOM','KE002', 'Certificate in Customs and Excise', ''),
    ],
    'FCK': [
        ('DIP_AGRI',   'FC001', 'Diploma in Agriculture', ''),
        ('DIP_BIZ',    'FC002', 'Diploma in Business Management', ''),
    ],
    'KICDT': [
        ('DIP_DEV',    'KID001', 'Diploma in Community Development', ''),
        ('CERT_COUNS', 'KID002', 'Certificate in Counselling', ''),
    ],
}


class Command(BaseCommand):
    help = 'Seed ~350 real Kenyan degree and diploma programmes for demo use.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing KUCCPS-DEMO programme records before seeding.',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = Programme.objects.filter(source_scope=SCOPE).delete()
            self.stdout.write(f'Cleared {deleted} existing demo programme(s).')

        institutions = {
            inst.external_key: inst
            for inst in Institution.objects.filter(source_scope=SCOPE)
        }

        missing = [k for k in PROGRAMMES_BY_INSTITUTION if k not in institutions]
        if missing:
            raise CommandError(
                f'These institution external_keys were not found in the DB '
                f'(run seed_demo_institutions first): {missing}'
            )

        created = skipped = 0
        for inst_key, progs in PROGRAMMES_BY_INSTITUTION.items():
            institution = institutions[inst_key]
            for suffix, code, name, description in progs:
                ext_key = f'{inst_key}-{suffix}'
                if Programme.objects.filter(source_scope=SCOPE, external_key=ext_key).exists():
                    skipped += 1
                    continue
                prog = Programme(
                    source_scope=SCOPE,
                    external_key=ext_key,
                    institution=institution,
                    code=code,
                    name=name,
                    description=description,
                    source_url=SOURCE_URL,
                    education_framework=FRAMEWORK,
                    admission_cycle=CYCLE,
                    effective_date=EFFECTIVE,
                    verification_status=STATUS,
                )
                prog.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created}  Skipped (already exist): {skipped}'
        ))
