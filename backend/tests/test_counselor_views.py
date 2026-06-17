import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from tests.factories import (
    CounselorFactory, SchoolFactory, StudentProfileFactory,
    VerifiedUserFactory, CounselorAssignmentFactory, CounselorNoteFactory,
    SubjectFactory, StudentSubjectFactory, CBCGradeFactory,
    RIASECAssessmentFactory,
)
from students.models import Subject

pytestmark = pytest.mark.django_db


def _auth(client, user):
    token = str(RefreshToken.for_user(user).access_token)
    client.cookies['access_token'] = token


@pytest.fixture
def school():
    return SchoolFactory()


@pytest.fixture
def counselor(school):
    return CounselorFactory(school=school)


@pytest.fixture
def assigned_student(counselor, school):
    profile = StudentProfileFactory(
        user=VerifiedUserFactory(role='student'),
        school=school, mode='school_linked', grade=9,
    )
    CounselorAssignmentFactory(
        counselor=counselor, student_profile=profile, school=school,
    )
    return profile


class TestCounselorStudentsView:
    def test_lists_assigned_students(self, client, counselor, assigned_student):
        _auth(client, counselor)
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 200
        data = r.json()['data']
        assert len(data) == 1
        assert data[0]['first_name'] == assigned_student.user.first_name

    def test_does_not_list_unassigned_students(self, client, counselor, school):
        _auth(client, counselor)
        StudentProfileFactory(school=school, mode='school_linked')
        r = client.get(reverse('counselor-students'))
        assert r.json()['data'] == []

    def test_does_not_list_other_counselors_students(self, client, school):
        c1 = CounselorFactory(school=school)
        c2 = CounselorFactory(school=school)
        profile = StudentProfileFactory(
            user=VerifiedUserFactory(role='student'),
            school=school, mode='school_linked',
        )
        CounselorAssignmentFactory(counselor=c1, student_profile=profile, school=school)
        _auth(client, c2)
        r = client.get(reverse('counselor-students'))
        assert r.json()['data'] == []

    def test_student_with_assessment_shows_quiz_done(self, client, counselor, assigned_student):
        from riasec.models import RIASECAssessment, RIASECScore, Pathway, Recommendation
        assessment = RIASECAssessment.objects.create(student_profile=assigned_student)
        for dim, score in [('R', 18), ('I', 22), ('A', 14), ('S', 11), ('E', 16), ('C', 13)]:
            RIASECScore.objects.create(assessment=assessment, dimension=dim, raw_score=score)
        pathway = Pathway.objects.first()
        if pathway:
            Recommendation.objects.create(
                assessment=assessment, pathway=pathway, rank=1, fit_score=18.25, fit_pct=73,
            )
        _auth(client, counselor)
        r = client.get(reverse('counselor-students'))
        data = r.json()['data']
        assert data[0]['quiz_status'] == 'done'

    def test_requires_auth(self, client):
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 401

    def test_student_cannot_access(self, client):
        student = VerifiedUserFactory(role='student')
        _auth(client, student)
        r = client.get(reverse('counselor-students'))
        assert r.status_code == 403


class TestCounselorStudentDetailView:
    def test_returns_student_detail(self, client, counselor, assigned_student):
        _auth(client, counselor)
        r = client.get(reverse('counselor-student-detail', args=[assigned_student.user.id]))
        assert r.status_code == 200
        data = r.json()['data']
        assert data['student']['email'] == assigned_student.user.email
        assert data['riasec_result'] is None
        assert data['grades'] == []
        assert data['notes_count'] == 0

    def test_returns_404_for_unassigned_student(self, client, counselor):
        other_student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=other_student)
        _auth(client, counselor)
        r = client.get(reverse('counselor-student-detail', args=[other_student.id]))
        assert r.status_code == 404


class TestCounselorStatsView:
    def test_returns_real_stats(self, client, counselor, assigned_student):
        CounselorNoteFactory(counselor=counselor, student=assigned_student.user)
        _auth(client, counselor)
        r = client.get(reverse('counselor-stats'))
        data = r.json()['data']
        assert data['total_students'] == 1
        assert data['notes_written'] == 1
        assert data['students_needing_attention'] == 1
        assert data['assessments_done'] == 0


class TestCounselorNotesView:
    def test_list_notes(self, client, counselor, assigned_student):
        CounselorNoteFactory(counselor=counselor, student=assigned_student.user, body='Note 1')
        _auth(client, counselor)
        r = client.get(reverse('counselor-notes'))
        assert r.status_code == 200
        assert len(r.json()['data']) == 1

    def test_list_excludes_soft_deleted(self, client, counselor, assigned_student):
        from django.utils import timezone
        note = CounselorNoteFactory(counselor=counselor, student=assigned_student.user)
        note.deleted_at = timezone.now()
        note.save()
        _auth(client, counselor)
        r = client.get(reverse('counselor-notes'))
        assert r.json()['data'] == []

    def test_create_note_for_assigned_student(self, client, counselor, assigned_student):
        _auth(client, counselor)
        r = client.post(reverse('counselor-notes'), {
            'student_id': assigned_student.user.id,
            'body': 'Keep up the good work!',
        }, content_type='application/json')
        assert r.status_code == 201
        assert r.json()['data']['body'] == 'Keep up the good work!'

    def test_create_note_for_unassigned_student_returns_400(self, client, counselor):
        other = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=other)
        _auth(client, counselor)
        r = client.post(reverse('counselor-notes'), {
            'student_id': other.id,
            'body': 'Test',
        }, content_type='application/json')
        assert r.status_code == 400

    def test_create_note_body_over_2000_chars_returns_400(self, client, counselor, assigned_student):
        _auth(client, counselor)
        r = client.post(reverse('counselor-notes'), {
            'student_id': assigned_student.user.id,
            'body': 'x' * 2001,
        }, content_type='application/json')
        assert r.status_code == 400

    def test_update_note(self, client, counselor, assigned_student):
        note = CounselorNoteFactory(counselor=counselor, student=assigned_student.user, body='Old')
        _auth(client, counselor)
        r = client.patch(
            reverse('counselor-note-detail', args=[note.id]),
            {'body': 'Updated note.'},
            content_type='application/json',
        )
        assert r.status_code == 200
        assert r.json()['data']['body'] == 'Updated note.'

    def test_cannot_update_other_counselors_note(self, client, school, assigned_student):
        c1 = CounselorFactory(school=school)
        c2 = CounselorFactory(school=school)
        note = CounselorNoteFactory(counselor=c1, student=assigned_student.user)
        _auth(client, c2)
        r = client.patch(
            reverse('counselor-note-detail', args=[note.id]),
            {'body': 'Hijack'},
            content_type='application/json',
        )
        assert r.status_code == 404

    def test_delete_note_soft_deletes(self, client, counselor, assigned_student):
        from counselors.models import CounselorNote
        note = CounselorNoteFactory(counselor=counselor, student=assigned_student.user)
        _auth(client, counselor)
        r = client.delete(reverse('counselor-note-detail', args=[note.id]))
        assert r.status_code == 200
        note.refresh_from_db()
        assert note.deleted_at is not None

    def test_requires_counselor_role(self, client, assigned_student):
        _auth(client, assigned_student.user)
        r = client.get(reverse('counselor-notes'))
        assert r.status_code == 403
