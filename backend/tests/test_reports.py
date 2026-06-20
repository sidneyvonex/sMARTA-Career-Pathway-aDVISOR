import io
import pytest
from pypdf import PdfReader
from reports.pdf_builder import build_student_report

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
                        {'term': 1, 'year': 2026, 'level': 'ME1', 'label': 'Meeting Expectation (lower)'},
                        {'term': 2, 'year': 2026, 'level': 'EE1', 'label': 'Exceeding Expectation (lower)'},
                    ],
                },
                {
                    'name': 'English',
                    'code': 'ENG0019',
                    'grades': [
                        {'term': 1, 'year': 2026, 'level': 'AE2', 'label': 'Approaching Expectation (upper)'},
                    ],
                },
            ],
            'riasec': {
                'scores': {'R': 18, 'I': 22, 'A': 10, 'S': 15, 'E': 20, 'C': 12},
                'holland_code': 'IE',
            },
            'recommendations': [
                {'rank': 1, 'pathway_name': 'Science & Technology', 'fit_pct': 87},
                {'rank': 2, 'pathway_name': 'Engineering', 'fit_pct': 72},
                {'rank': 3, 'pathway_name': 'Business Studies', 'fit_pct': 65},
            ],
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
