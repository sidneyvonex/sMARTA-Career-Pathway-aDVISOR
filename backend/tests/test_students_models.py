import pytest
from django.db import IntegrityError
from accounts.models import StudentProfile


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
