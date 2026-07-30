import pytest
from django.db import IntegrityError
from accounts.models import StudentProfile
from students.models import GRADE_LEVEL_CHOICES, GRADE_LEVEL_POINTS


class TestGradeLevelScale:
    def test_levels_are_ordered_from_highest_to_lowest(self):
        assert [code for code, _label in GRADE_LEVEL_CHOICES] == [
            'EE1', 'EE2', 'ME1', 'ME2', 'AE1', 'AE2', 'BE1', 'BE2',
        ]

    def test_level_one_is_higher_than_level_two_in_every_band(self):
        assert GRADE_LEVEL_POINTS == {
            'EE1': 8,
            'EE2': 7,
            'ME1': 6,
            'ME2': 5,
            'AE1': 4,
            'AE2': 3,
            'BE1': 2,
            'BE2': 1,
        }

    def test_labels_describe_level_numbers_without_reversing_them(self):
        labels = dict(GRADE_LEVEL_CHOICES)
        assert labels['EE1'] == 'Exceeding Expectation - Level 1'
        assert labels['EE2'] == 'Exceeding Expectation - Level 2'
        assert labels['BE1'] == 'Below Expectation - Level 1'
        assert labels['BE2'] == 'Below Expectation - Level 2'


@pytest.mark.django_db
class TestStudentProfileBioFields:
    def test_bio_field_exists_and_defaults_empty(self):
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory()
        assert profile.bio == ''
        assert profile.career_interests == ''
        assert profile.date_of_birth is None
        assert profile.photo_url is None

    def test_bio_field_persists(self):
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(bio='I love science')
        profile.refresh_from_db()
        assert profile.bio == 'I love science'

    def test_career_interests_persists(self):
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(career_interests='Medicine and biology')
        profile.refresh_from_db()
        assert profile.career_interests == 'Medicine and biology'

    def test_date_of_birth_and_photo_url_persist(self):
        from tests.factories import StudentProfileFactory
        import datetime
        profile = StudentProfileFactory(
            date_of_birth=datetime.date(2010, 3, 15),
            photo_url='https://cdn.example.com/photo.jpg',
        )
        profile.refresh_from_db()
        assert profile.date_of_birth == datetime.date(2010, 3, 15)
        assert profile.photo_url == 'https://cdn.example.com/photo.jpg'


@pytest.mark.django_db
class TestStudentSubjectConstraints:
    def test_duplicate_enrollment_raises_integrity_error(self):
        from students.models import Subject, StudentSubject
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(grade=9)
        subject = Subject.objects.create(name='Math', code='MTH9T', grade=9, category='Core')
        StudentSubject.objects.create(student_profile=profile, subject=subject)
        with pytest.raises(IntegrityError):
            StudentSubject.objects.create(student_profile=profile, subject=subject)

    def test_delete_student_subject_cascades_grades(self):
        from students.models import Subject, StudentSubject, CBCGrade
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(grade=9)
        subject = Subject.objects.create(name='Eng', code='ENG9T', grade=9, category='Core')
        ss = StudentSubject.objects.create(student_profile=profile, subject=subject)
        CBCGrade.objects.create(student_subject=ss, term=1, year=2026, level='ME1')
        ss_id = ss.pk
        ss.delete()
        assert CBCGrade.objects.filter(student_subject_id=ss_id).count() == 0

    def test_duplicate_grade_per_term_year_raises_integrity_error(self):
        from students.models import Subject, StudentSubject, CBCGrade
        from tests.factories import StudentProfileFactory
        profile = StudentProfileFactory(grade=9)
        subject = Subject.objects.create(name='Sci', code='SCI9T', grade=9, category='Core')
        ss = StudentSubject.objects.create(student_profile=profile, subject=subject)
        CBCGrade.objects.create(student_subject=ss, term=1, year=2026, level='ME1')
        with pytest.raises(IntegrityError):
            CBCGrade.objects.create(student_subject=ss, term=1, year=2026, level='EE1')


@pytest.mark.django_db
class TestSubjectSeed:
    def test_grade9_subjects_seeded(self):
        from students.models import Subject
        assert Subject.objects.filter(grade=9).count() == 14

    def test_grade10_active_catalogue_uses_senior_school_learning_areas(self):
        from students.models import Subject
        active = {
            subject.code: subject.name
            for subject in Subject.objects.filter(grade=10, is_active=True)
        }
        assert active == {
            'AGR10': 'Agriculture',
            'ARA10': 'Arabic',
            'AVT10': 'Aviation',
            'BCN10': 'Building Construction',
            'BIO10': 'Biology',
            'BST10': 'Business Studies',
            'CHE10': 'Chemistry',
            'CHR10': 'Christian Religious Education',
            'CMT10': 'Core Mathematics',
            'CPS10': 'Computer Studies',
            'CSL10': 'Community Service Learning',
            'ELC10': 'Electricity',
            'EMT10': 'Essential Mathematics',
            'ENG10': 'English',
            'FAR10': 'Fine Arts',
            'FKI10': 'Fasihi ya Kiswahili',
            'FRN10': 'French',
            'GEO10': 'Geography',
            'GER10': 'German',
            'GSC10': 'General Science',
            'HCT10': 'History & Citizenship',
            'HOM10': 'Home Science',
            'HRE10': 'Hindu Religious Education',
            'IRE10': 'Islamic Religious Education',
            'KIS10': 'Kiswahili',
            'LIE10': 'Literature in English',
            'MDT10': 'Media Technology',
            'MFT10': 'Marine & Fisheries',
            'MDA10': 'Music & Dance',
            'MTW10': 'Metal Work',
            'PED10': 'Physical Education',
            'PHY10': 'Physics',
            'PME10': 'Power Mechanics',
            'SRE10': 'Sports & Recreation',
            'TFM10': 'Theatre & Film',
            'WDW10': 'Woodwork',
        }

    def test_obsolete_junior_style_grade10_subjects_are_inactive(self):
        from students.models import Subject
        obsolete_codes = {'MTH10', 'INT10', 'HSS10', 'ART10', 'CRE10', 'MUS10'}
        assert set(
            Subject.objects.filter(grade=10, is_active=False).values_list('code', flat=True)
        ) == obsolete_codes

    def test_math_grade9_exists(self):
        from students.models import Subject
        s = Subject.objects.get(code='MTH9')
        assert s.name == 'Mathematics'
        assert s.category == 'Core'

    def test_optional_subject_exists(self):
        from students.models import Subject
        s = Subject.objects.get(code='FRN9')
        assert s.category == 'Optional'


@pytest.mark.django_db
class TestFactories:
    def test_subject_factory_creates_subject(self):
        from tests.factories import SubjectFactory
        s = SubjectFactory()
        assert s.pk is not None
        assert s.grade == 9

    def test_student_subject_factory_creates_enrollment(self):
        from tests.factories import StudentSubjectFactory
        ss = StudentSubjectFactory()
        assert ss.pk is not None
        assert ss.student_profile.grade == ss.subject.grade

    def test_cbc_grade_factory_creates_grade(self):
        from tests.factories import CBCGradeFactory
        g = CBCGradeFactory()
        assert g.pk is not None
        assert g.level == 'ME1'
        assert g.term == 1
        assert g.year == 2026
