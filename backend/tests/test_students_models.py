import pytest
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
