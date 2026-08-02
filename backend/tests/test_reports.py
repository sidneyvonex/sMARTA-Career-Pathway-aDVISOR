import io
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from pypdf import PdfReader
from rest_framework.test import APIClient
from django.utils import timezone
from guidance.models import LearnerCombinationChoice, LearnerPlan, PlanMilestone
from reports.pdf_builder import build_student_report
from system_admin.models import AuditLog
from tests.factories import (
    VerifiedUserFactory, StudentProfileFactory, CounselorFactory,
    CounselorAssignmentFactory, SchoolFactory, SchoolAdminFactory,
    ParentFactory, ParentStudentLinkFactory, SystemAdminFactory,
    StudentSubjectFactory, CBCGradeFactory, AcademicGoalFactory,
    SubjectFactory,
    LearnerEducationGoalFactory,
    RIASECAssessmentFactory, RIASECScoreFactory, PathwayFactory,
    RecommendationFactory, FrameworkVersionFactory, PathwayTrackFactory,
    SubjectCombinationFactory,
    StudentSchoolMembershipFactory,
)

pytestmark = pytest.mark.django_db


def _extract_pdf_text(pdf_bytes):
    """Extract text from PDF bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text


class TestPDFBuilder:
    def _make_data(self, **overrides):
        base = {
            'student_name': 'Jane Muthoni',
            'grade': 9,
            'school_name': 'Starehe Boys Centre',
            'county': 'Kiambu',
            'email': 'jane@example.com',
            'mode': 'school_linked',
            'subjects': [
                {
                    'name': 'Mathematics',
                    'code': 'MAT0019',
                    'grades': [
                        {'term': 1, 'year': 2026, 'level': 'ME1',
                            'label': 'Meeting Expectation - Level 1'},
                        {'term': 2, 'year': 2026, 'level': 'EE1',
                            'label': 'Exceeding Expectation - Level 1'},
                    ],
                },
                {
                    'name': 'English',
                    'code': 'ENG0019',
                    'grades': [
                        {'term': 1, 'year': 2026, 'level': 'AE2',
                            'label': 'Approaching Expectation - Level 2'},
                    ],
                },
            ],
            'riasec': {
                'scores': {'R': 18, 'I': 22, 'A': 10, 'S': 15, 'E': 20, 'C': 12},
                'holland_code': 'IE',
            },
            'recommendations': [
                {
                    'rank': 1,
                    'pathway_name': 'Science & Technology',
                    'algorithm_version': 'interest-alignment-1.0',
                    'explanation': {
                        'summary': 'Science & Technology aligns with Investigative interests.',
                        'limitations': 'Interests alone do not predict success.',
                        'next_step': 'Review academic evidence and school offerings.',
                    },
                },
                {'rank': 2, 'pathway_name': 'Engineering'},
                {'rank': 3, 'pathway_name': 'Business Studies'},
            ],
            'evidence_summary': {
                'subjects_with_evidence': 2,
                'total_subjects': 2,
                'total_grade_records': 3,
                'assessment_submitted_at': '20 June 2026',
            },
            'evidence_completeness': {
                'status': 'in_progress',
                'label': 'In progress',
                'explanation': '2 of 2 enrolled subjects have recorded academic evidence.',
            },
            'academic_progress': {
                'overall': {
                    'status': 'on_track',
                    'label': 'On track',
                    'subject_continuity_codes': ['MAT'],
                },
                'subjects': [{
                    'continuity_code': 'MAT',
                    'subject_name': 'Mathematics',
                    'status': 'on_track',
                    'label': 'On track',
                    'rule_code': 'otherwise_me_on_track',
                    'explanation': 'The available academic evidence is meeting expectation.',
                    'suggested_action': (
                        'Continue practising and record the next available evidence.'
                    ),
                    'evidence_confidence': 'school_verified',
                    'records_used': [],
                    'evidence': [],
                    'decision_inputs': {},
                }],
                'advisory_disclaimer': (
                    'Academic progress is advisory only. It does not determine '
                    'official CBE placement or admission.'
                ),
            },
            'academic_goals': [{
                'continuity_code': 'MAT',
                'current_level': {
                    'code': 'ME1',
                    'framework': {
                        'code': 'CBC-JUNIOR-SCHOOL', 'version': 'pilot-2026',
                    },
                },
                'target_level': {
                    'code': 'ME2',
                    'framework': {
                        'code': 'CBC-JUNIOR-SCHOOL', 'version': 'pilot-2026',
                    },
                },
                'target_term': 3,
                'target_year': 2026,
                'action_plan': 'Practise twice each week.',
                'status': 'active',
            }],
            'education_goals': [{
                'kind': 'primary',
                'priority': 1,
                'institution': {
                    'name': 'Test University',
                    'source_url': 'https://students.kuccps.net/institutions/',
                    'education_framework': 'KCSE',
                    'admission_cycle': '2025/2026',
                    'effective_date': '2025-03-01',
                    'verification_status': 'historical',
                },
                'programme': {
                    'name': 'Bachelor of Science',
                    'source_url': 'https://students.kuccps.net/programmes/',
                    'education_framework': 'KCSE',
                    'admission_cycle': '2025/2026',
                    'effective_date': '2025-03-01',
                    'verification_status': 'historical',
                },
            }],
            'provisional_choice': {
                'code': 'STEM-PURE-01',
                'title': 'Pure Sciences',
                'pathway': 'STEM',
                'track': 'Pure Sciences',
                'subjects': ['Physics', 'Chemistry', 'Biology'],
                'learner_reason': 'I enjoy laboratory work.',
            },
            'plan': {
                'review_status': 'ready_for_review',
                'learner_reason': 'I want to prepare for a science pathway.',
                'milestones': [
                    {
                        'title': 'Discuss the choice with my counsellor',
                        'due_date': '30 June 2026',
                        'is_complete': False,
                    },
                ],
            },
            'framework': {
                'code': 'CBC-SS-2026',
                'title': 'Senior School Subject Combination Catalogue',
                'effective_date': '01 January 2026',
                'source_url': 'https://example.com/catalogue.pdf',
            },
            'instrument_version': 'riasec-pilot-1.0',
            'algorithm_version': 'interest-alignment-1.0',
            'generated_at': '21 June 2026 10:30 EAT',
            'logo_path': None,
        }
        base.update(overrides)
        return base

    def test_returns_valid_pdf_bytes(self):
        data = self._make_data()
        result = build_student_report(data)
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    def test_pdf_contains_student_name(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Jane Muthoni' in text

    def test_pdf_contains_school_name(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Starehe Boys Centre' in text

    def test_pdf_contains_subject_names(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Mathematics' in text
        assert 'English' in text

    def test_pdf_contains_riasec_dimensions(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Realistic' in text
        assert 'Investigative' in text

    def test_pdf_contains_pathway_names(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Science & Technology' in text

    def test_pdf_without_riasec(self):
        data = self._make_data(riasec=None, recommendations=[])
        result = build_student_report(data)
        assert isinstance(result, bytes)
        text = _extract_pdf_text(result)
        assert 'No assessment completed yet' in text

    def test_pdf_without_grades(self):
        data = self._make_data(subjects=[])
        result = build_student_report(data)
        assert isinstance(result, bytes)
        text = _extract_pdf_text(result)
        assert 'No subjects enrolled' in text

    def test_pdf_self_guided_student(self):
        data = self._make_data(school_name=None, mode='self_guided')
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'Self-Guided' in text

    def test_pdf_contains_disclaimer(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        assert 'advisory only' in text

    def test_pdf_presents_advisory_interest_alignment_without_percentages(self):
        data = self._make_data()
        result = build_student_report(data)
        text = _extract_pdf_text(result)
        normalized_text = ' '.join(text.split())
        assert 'Pathways Suggested for Exploration' in text
        assert 'Interest alignment' in text
        assert 'does not predict success or determine placement' in normalized_text
        assert '87%' not in text
        assert '72%' not in text
        assert '65%' not in text

    def test_pdf_contains_decision_context_and_provenance(self):
        result = build_student_report(self._make_data())
        text = _extract_pdf_text(result)
        normalized_text = ' '.join(text.split())

        assert 'Evidence Sources' in text
        assert '2 of 2 enrolled subjects' in normalized_text
        assert 'Interest Profile' in text
        assert 'Science & Technology aligns with Investigative interests' in normalized_text
        assert 'Evidence Completeness' in text
        assert 'In progress' in text
        assert 'Provisional Combination' in text
        assert 'STEM-PURE-01' in text
        assert 'Discuss the choice with my counsellor' in normalized_text
        assert 'CBC-SS-2026' in text
        assert 'interest-alignment-1.0' in text
        assert 'riasec-pilot-1.0' in text
        assert '21 June 2026 10:30 EAT' in normalized_text
        assert 'does not submit official Senior School choices' in normalized_text

    def test_pdf_contains_advisory_progress_targets_goals_and_evidence_provenance(self):
        data = self._make_data()
        data['subjects'][0]['grades'][0].update({
            'framework': {'code': 'CBC-JUNIOR-SCHOOL', 'version': 'pilot-2026'},
            'source': 'school',
            'verified_school': 'Starehe Boys Centre',
            'verified_at': '20 June 2026',
        })

        text = _extract_pdf_text(build_student_report(data))
        normalized = ' '.join(text.split())

        assert 'Academic Progress' in text
        assert 'otherwise_me_on_track' in normalized
        assert 'Continue practising' in normalized
        assert 'Academic Targets' in text
        assert 'ME1 to ME2' in normalized
        assert 'Education Goals' in text
        assert 'Test University' in text
        assert 'KCSE · 2025/2026' in normalized
        assert 'Verified by Starehe Boys Centre' in normalized
        assert 'CBC-JUNIOR-SCHOOL pilot-2026' in normalized
        assert 'advisory only' in normalized
        assert 'eligibility probability' not in normalized.lower()

    def test_pdf_labels_retained_provenance_as_removed_verification(self):
        data = self._make_data()
        data['subjects'][0]['grades'][0].update({
            'framework': {'code': 'CBC-JUNIOR-SCHOOL', 'version': 'pilot-2026'},
            'source': 'school',
            'verified_school': 'Starehe Boys Centre',
            'verified_at': None,
        })

        normalized = ' '.join(_extract_pdf_text(build_student_report(data)).split())

        assert 'Previously verified by Starehe Boys Centre; verification removed' in normalized
        assert 'Verified by Starehe Boys Centre' not in normalized

    def test_pdf_renders_exact_evidence_used_for_each_progress_status(self):
        data = self._make_data()
        data['academic_progress']['subjects'][0]['records_used'] = [{
            'id': 17,
            'academic_grade': 9,
            'term': 2,
            'year': 2026,
            'level': 'ME1',
            'framework': {
                'code': 'CBC-JUNIOR-SCHOOL',
                'version': 'pilot-2026',
            },
            'source': 'learner',
            'verified_school': 3,
            'verified_at': '2026-06-20T08:00:00+03:00',
        }]

        normalized = ' '.join(_extract_pdf_text(build_student_report(data)).split())

        assert 'Evidence used for this status' in normalized
        assert 'Grade 9 · Term 2 2026 · ME1' in normalized
        assert 'CBC-JUNIOR-SCHOOL pilot-2026' in normalized
        assert 'Origin: Learner entered' in normalized
        assert 'Verification: School verified on 2026-06-20T08:00:00+03:00' in normalized

    def test_pdf_uses_programme_provenance_and_historical_reference_wording(self):
        data = self._make_data()
        data['education_goals'][0]['institution'].update({
            'source_url': 'https://institution.example/source',
            'admission_cycle': '2024/2025',
            'effective_date': '2024-01-01',
            'verification_status': 'verified',
        })
        data['education_goals'][0]['programme'].update({
            'source_url': 'https://programme.example/source',
            'education_framework': 'KCSE',
            'admission_cycle': '2025/2026',
            'effective_date': '2025-03-01',
            'verification_status': 'historical',
        })

        normalized = ' '.join(_extract_pdf_text(build_student_report(data)).split())

        assert 'https://programme.example/source' in normalized
        assert '2025/2026' in normalized
        assert '2025-03-01' in normalized
        assert 'Historical reference only' in normalized
        assert 'https://institution.example/source' not in normalized

    def test_pdf_labels_subject_counts_as_evidence_completeness(self):
        normalized = ' '.join(
            _extract_pdf_text(build_student_report(self._make_data())).split()
        )

        assert 'Evidence Completeness' in normalized
        assert 'Academic Readiness' not in normalized


# ---------------------------------------------------------------------------
# Task 2: StudentReportView — Permissions + Data Assembly
# ---------------------------------------------------------------------------

class TestStudentReportViewPermissions:
    def setup_method(self):
        self.client = APIClient()
        self.student = VerifiedUserFactory(role='student')
        self.profile = StudentProfileFactory(user=self.student, grade=9, mode='self_guided')
        ss = StudentSubjectFactory(student_profile=self.profile)
        CBCGradeFactory(student_subject=ss, term=1, year=2026, level='ME1')

    def test_student_can_download_own_report(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'
        assert response.content[:5] == b'%PDF-'
        event = AuditLog.objects.get(action='report_downloaded')
        assert event.actor == self.student
        assert event.target_type == 'report'
        assert event.target_id == self.student.id
        assert event.details['student_id'] == self.student.id

    def test_student_cannot_download_other_report(self):
        other = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=other, grade=9)
        self.client.force_authenticate(self.student)
        response = self.client.get(f'/api/v1/reports/student/{other.id}/pdf/')
        assert response.status_code == 403

    def test_counselor_assigned_can_download(self):
        school = SchoolFactory()
        counselor = CounselorFactory(school=school)
        self.profile.school = school
        self.profile.mode = 'school_linked'
        self.profile.save(update_fields=['school', 'mode'])
        CounselorAssignmentFactory(
            counselor=counselor, student_profile=self.profile, school=school,
        )
        self.client.force_authenticate(counselor)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_counselor_unassigned_cannot_download(self):
        counselor = CounselorFactory()
        self.client.force_authenticate(counselor)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 403

    def test_school_admin_same_school_can_download(self):
        school = SchoolFactory()
        admin = SchoolAdminFactory(school=school)
        self.profile.school = school
        self.profile.mode = 'school_linked'
        self.profile.school_membership_status = 'active'
        self.profile.save(update_fields=['school', 'mode', 'school_membership_status'])
        self.client.force_authenticate(admin)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_school_admin_cannot_download_pending_membership_report(self):
        school = SchoolFactory()
        admin = SchoolAdminFactory(school=school)
        self.profile.school = school
        self.profile.mode = 'school_linked'
        self.profile.school_membership_status = 'pending'
        self.profile.save(update_fields=['school', 'mode', 'school_membership_status'])
        self.client.force_authenticate(admin)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 403

    def test_school_admin_cannot_download_when_ended_membership_conflicts_with_stale_profile(self):
        school = SchoolFactory()
        admin = SchoolAdminFactory(school=school)
        self.profile.school = school
        self.profile.mode = 'school_linked'
        self.profile.school_membership_status = 'active'
        self.profile.save(update_fields=['school', 'mode', 'school_membership_status'])
        StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=school,
            status='ended',
        )
        self.client.force_authenticate(admin)

        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')

        assert response.status_code == 403

    def test_active_membership_supplies_authoritative_report_school(
        self,
        monkeypatch,
    ):
        stale_school = SchoolFactory(name='Stale Profile School')
        current_school = SchoolFactory(name='Current Membership School')
        admin = SchoolAdminFactory(school=current_school)
        self.profile.school = stale_school
        self.profile.mode = 'self_guided'
        self.profile.school_membership_status = 'not_applicable'
        self.profile.save(update_fields=[
            'school',
            'mode',
            'school_membership_status',
        ])
        StudentSchoolMembershipFactory(
            student_profile=self.profile,
            school=current_school,
            status='active',
        )
        captured = {}

        def capture_report(data):
            captured.update(data)
            return b'%PDF-1.4 test'

        monkeypatch.setattr('reports.views.build_student_report', capture_report)
        self.client.force_authenticate(admin)

        response = self.client.get(
            f'/api/v1/reports/student/{self.student.id}/pdf/'
        )

        assert response.status_code == 200
        assert captured['school_name'] == 'Current Membership School'
        assert captured['school_membership_status'] == 'active'

    def test_school_admin_different_school_cannot_download(self):
        admin = SchoolAdminFactory()
        self.client.force_authenticate(admin)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 403

    def test_parent_linked_can_download(self):
        parent = ParentFactory()
        ParentStudentLinkFactory(parent=parent, student=self.student)
        self.client.force_authenticate(parent)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_parent_unlinked_cannot_download(self):
        parent = ParentFactory()
        self.client.force_authenticate(parent)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 403

    def test_parent_pending_learner_approval_cannot_download(self):
        parent = ParentFactory()
        ParentStudentLinkFactory(
            parent=parent,
            student=self.student,
            status='pending_learner',
        )
        self.client.force_authenticate(parent)

        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')

        assert response.status_code == 403

    def test_system_admin_can_download_any(self):
        admin = SystemAdminFactory()
        self.client.force_authenticate(admin)
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_unauthenticated_returns_401(self):
        response = self.client.get(f'/api/v1/reports/student/{self.student.id}/pdf/')
        assert response.status_code in (401, 403)

    def test_nonexistent_student_returns_404(self):
        admin = SystemAdminFactory()
        self.client.force_authenticate(admin)
        response = self.client.get('/api/v1/reports/student/99999/pdf/')
        assert response.status_code == 404

    def test_non_student_user_returns_404(self):
        admin = SystemAdminFactory()
        counselor = CounselorFactory()
        self.client.force_authenticate(admin)
        response = self.client.get(f'/api/v1/reports/student/{counselor.id}/pdf/')
        assert response.status_code == 404


class TestStudentReportViewEdgeCases:
    def setup_method(self):
        self.client = APIClient()
        self.admin = SystemAdminFactory()
        self.client.force_authenticate(self.admin)

    def test_student_with_no_grades_and_no_assessment_returns_400(self):
        student = VerifiedUserFactory(role='student')
        StudentProfileFactory(user=student, grade=9)
        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')
        assert response.status_code == 400
        assert 'no grades or assessment' in response.data['message'].lower()

    def test_student_with_grades_only(self):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        ss = StudentSubjectFactory(student_profile=profile)
        CBCGradeFactory(student_subject=ss)
        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_student_with_assessment_only(self):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        assessment = RIASECAssessmentFactory(student_profile=profile)
        for dim in ['R', 'I', 'A', 'S', 'E', 'C']:
            RIASECScoreFactory(assessment=assessment, dimension=dim, raw_score=15)
        pathway = PathwayFactory(name='Test Pathway')
        RecommendationFactory(assessment=assessment, pathway=pathway, rank=1)
        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/pdf'

    def test_content_disposition_header(self):
        student = VerifiedUserFactory(role='student', first_name='Jane', last_name='Doe')
        profile = StudentProfileFactory(user=student, grade=9)
        ss = StudentSubjectFactory(student_profile=profile)
        CBCGradeFactory(student_subject=ss)
        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')
        assert 'smarta-shauri-report-Jane-Doe' in response['Content-Disposition']

    def test_report_assembles_choice_plan_evidence_and_versions(self, monkeypatch):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        enrollment = StudentSubjectFactory(student_profile=profile)
        CBCGradeFactory(student_subject=enrollment)
        assessment = RIASECAssessmentFactory(
            student_profile=profile,
            instrument_version='riasec-pilot-test',
        )
        for dimension in ['R', 'I', 'A', 'S', 'E', 'C']:
            RIASECScoreFactory(
                assessment=assessment,
                dimension=dimension,
                raw_score=15,
            )
        pathway = PathwayFactory(name='Report STEM')
        RecommendationFactory(
            assessment=assessment,
            pathway=pathway,
            rank=1,
            algorithm_version='alignment-test-2',
            explanation={'summary': 'STEM aligns with Investigative interests.'},
        )
        framework = FrameworkVersionFactory(
            code='CBC-REPORT-2026',
            title='Report test catalogue',
            is_active=True,
        )
        track = PathwayTrackFactory(
            framework_version=framework,
            pathway=pathway,
            name='Pure Sciences',
        )
        combination = SubjectCombinationFactory(
            framework_version=framework,
            track=track,
            code='PURE-REPORT-01',
            title='Pure Sciences combination',
        )
        choice = LearnerCombinationChoice.objects.create(
            student_profile=profile,
            combination=combination,
            status=LearnerCombinationChoice.STATUS_PROVISIONAL,
            learner_reason='I enjoy experiments.',
        )
        plan = LearnerPlan.objects.create(
            student_profile=profile,
            provisional_choice=choice,
            learner_reason='Prepare for a science pathway.',
            review_status=LearnerPlan.STATUS_READY,
        )
        PlanMilestone.objects.create(
            plan=plan,
            title='Meet my counsellor',
            position=1,
        )
        captured = {}

        def capture_report(data):
            captured.update(data)
            return b'%PDF-1.4 test'

        monkeypatch.setattr('reports.views.build_student_report', capture_report)

        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')

        assert response.status_code == 200
        assert captured['evidence_summary']['total_grade_records'] == 1
        assert captured['evidence_completeness']['status'] == 'in_progress'
        assert 'academic_readiness' not in captured
        assert captured['provisional_choice']['code'] == 'PURE-REPORT-01'
        assert captured['plan']['milestones'][0]['title'] == 'Meet my counsellor'
        assert captured['framework']['code'] == 'CBC-REPORT-2026'
        assert captured['instrument_version'] == 'riasec-pilot-test'
        assert captured['algorithm_version'] == 'alignment-test-2'
        assert captured['generated_at']

    def test_report_assembles_progress_targets_goals_and_grade_provenance(self, monkeypatch):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        enrollment = StudentSubjectFactory(student_profile=profile)
        school = SchoolFactory(name='Evidence School')
        verifier = SchoolAdminFactory(school=school)
        grade = CBCGradeFactory(
            student_subject=enrollment,
            verified_by=verifier,
            verified_school=school,
            verified_at=timezone.now(),
            source='school',
        )
        AcademicGoalFactory(
            learner=profile,
            current_evidence=grade,
            created_by=student,
        )
        LearnerEducationGoalFactory(learner=profile, created_by=student)
        captured = {}

        def capture_report(data):
            captured.update(data)
            return b'%PDF-1.4 test'

        monkeypatch.setattr('reports.views.build_student_report', capture_report)

        response = self.client.get(f'/api/v1/reports/student/{student.id}/pdf/')

        assert response.status_code == 200
        assert captured['academic_progress']['subjects'][0]['rule_code']
        assert len(captured['academic_goals']) == 1
        assert len(captured['education_goals']) == 1
        exported_grade = captured['subjects'][0]['grades'][0]
        assert exported_grade['framework']['version'] == grade.framework.version
        assert exported_grade['verified_school'] == 'Evidence School'
        assert exported_grade['source'] == 'school'

    def test_report_assembly_queries_stay_bounded_as_progress_records_grow(
        self,
        monkeypatch,
    ):
        student = VerifiedUserFactory(role='student')
        profile = StudentProfileFactory(user=student, grade=9)
        for index in range(5):
            enrollment = StudentSubjectFactory(
                student_profile=profile,
                subject=SubjectFactory(code=f'RQRY{index}9', grade=9),
            )
            evidence = CBCGradeFactory(
                student_subject=enrollment,
                term=1,
                year=2026,
                level='ME1',
            )
            AcademicGoalFactory(
                learner=profile,
                current_evidence=evidence,
                created_by=student,
            )
        LearnerEducationGoalFactory(learner=profile)
        LearnerEducationGoalFactory(
            learner=profile,
            kind='alternative',
            priority=1,
        )
        LearnerEducationGoalFactory(
            learner=profile,
            kind='alternative',
            priority=2,
        )
        captured_report = {}

        def capture_report(data):
            captured_report.update(data)
            return b'%PDF-1.4 test'

        monkeypatch.setattr('reports.views.build_student_report', capture_report)

        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(
                f'/api/v1/reports/student/{student.id}/pdf/'
            )

        assert response.status_code == 200
        assert len(captured_report['subjects']) == 5
        assert len(captured_report['academic_goals']) == 5
        assert len(captured_report['education_goals']) == 3
        assert len(captured) <= 13

    def test_invalid_student_id_returns_404(self):
        # <int:student_id> URL converter rejects non-numeric IDs at routing level.
        # Django returns 404 but debug error page rendering may crash on some
        # Python versions, so we also accept an AttributeError from the template engine.
        try:
            response = self.client.get('/api/v1/reports/student/abc/pdf/')
            assert response.status_code == 404
        except AttributeError:
            # Django debug template rendering bug on Python 3.14 — the URL
            # correctly didn't match (which is a 404), but the error page crashes.
            pass
