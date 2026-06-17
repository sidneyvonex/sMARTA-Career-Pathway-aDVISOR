import pytest
from django.db import IntegrityError
from django.utils import timezone
from tests.factories import (
    CounselorFactory, SchoolFactory, StudentProfileFactory,
    VerifiedUserFactory,
)

pytestmark = pytest.mark.django_db


class TestCounselorAssignment:
    def test_create_assignment(self):
        from counselors.models import CounselorAssignment
        school = SchoolFactory()
        counselor = CounselorFactory(school=school)
        profile = StudentProfileFactory(school=school, mode='school_linked')
        assignment = CounselorAssignment.objects.create(
            counselor=counselor, student_profile=profile, school=school,
        )
        assert assignment.is_active is True
        assert assignment.counselor == counselor
        assert assignment.student_profile == profile

    def test_unique_active_assignment_per_student(self):
        from counselors.models import CounselorAssignment
        school = SchoolFactory()
        c1 = CounselorFactory(school=school)
        c2 = CounselorFactory(school=school)
        profile = StudentProfileFactory(school=school, mode='school_linked')
        CounselorAssignment.objects.create(
            counselor=c1, student_profile=profile, school=school,
        )
        with pytest.raises(IntegrityError):
            CounselorAssignment.objects.create(
                counselor=c2, student_profile=profile, school=school,
            )

    def test_reassignment_deactivate_old(self):
        from counselors.models import CounselorAssignment
        school = SchoolFactory()
        c1 = CounselorFactory(school=school)
        c2 = CounselorFactory(school=school)
        profile = StudentProfileFactory(school=school, mode='school_linked')
        old = CounselorAssignment.objects.create(
            counselor=c1, student_profile=profile, school=school,
        )
        old.is_active = False
        old.save()
        new = CounselorAssignment.objects.create(
            counselor=c2, student_profile=profile, school=school,
        )
        assert new.is_active is True
        assert CounselorAssignment.objects.filter(student_profile=profile).count() == 2

    def test_cascade_delete_counselor(self):
        from counselors.models import CounselorAssignment
        school = SchoolFactory()
        counselor = CounselorFactory(school=school)
        profile = StudentProfileFactory(school=school, mode='school_linked')
        CounselorAssignment.objects.create(
            counselor=counselor, student_profile=profile, school=school,
        )
        counselor.delete()
        assert CounselorAssignment.objects.count() == 0


class TestCounselorNote:
    def test_create_note(self):
        from counselors.models import CounselorNote
        counselor = CounselorFactory()
        student = VerifiedUserFactory(role='student')
        note = CounselorNote.objects.create(
            counselor=counselor, student=student, body='Great progress in math.',
        )
        assert note.body == 'Great progress in math.'
        assert note.deleted_at is None

    def test_soft_delete(self):
        from counselors.models import CounselorNote
        counselor = CounselorFactory()
        student = VerifiedUserFactory(role='student')
        note = CounselorNote.objects.create(
            counselor=counselor, student=student, body='Test note',
        )
        note.deleted_at = timezone.now()
        note.save()
        assert CounselorNote.objects.filter(deleted_at__isnull=True).count() == 0
        assert CounselorNote.objects.count() == 1

    def test_ordering_newest_first(self):
        from counselors.models import CounselorNote
        counselor = CounselorFactory()
        student = VerifiedUserFactory(role='student')
        n1 = CounselorNote.objects.create(counselor=counselor, student=student, body='First')
        n2 = CounselorNote.objects.create(counselor=counselor, student=student, body='Second')
        notes = list(CounselorNote.objects.all())
        assert notes[0].pk == n2.pk
