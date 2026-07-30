from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from guidance.models import FrameworkVersion
from tests.factories import (
    FrameworkVersionFactory,
    PathwayTrackFactory,
    SchoolFactory,
    SchoolOfferingFactory,
    SubjectCombinationFactory,
    SubjectFactory,
)


pytestmark = pytest.mark.django_db


class TestFrameworkVersion:
    def test_new_active_version_deactivates_previous_version(self):
        previous = FrameworkVersionFactory(is_active=True)

        current = FrameworkVersionFactory(is_active=True)

        previous.refresh_from_db()
        assert previous.is_active is False
        assert FrameworkVersion.objects.current() == current

    def test_current_returns_none_without_active_version(self):
        FrameworkVersionFactory(is_active=False)

        assert FrameworkVersion.objects.current() is None

    def test_framework_records_source_and_effective_date(self):
        framework = FrameworkVersionFactory(
            source_url='https://kicd.ac.ke/curriculum-reform/',
            effective_date=date(2026, 1, 1),
        )

        assert framework.source_url == 'https://kicd.ac.ke/curriculum-reform/'
        assert framework.effective_date == date(2026, 1, 1)


class TestPathwayTrack:
    def test_code_is_unique_within_framework_version(self):
        track = PathwayTrackFactory(code='PURE-SCIENCES')

        with pytest.raises(IntegrityError), transaction.atomic():
            PathwayTrackFactory(
                framework_version=track.framework_version,
                code=track.code,
            )

    def test_code_can_repeat_in_another_framework_version(self):
        PathwayTrackFactory(code='PURE-SCIENCES')

        repeated = PathwayTrackFactory(code='PURE-SCIENCES')

        assert repeated.pk is not None


class TestSubjectCombination:
    def test_combination_has_exactly_three_distinct_elective_subjects(self):
        combination = SubjectCombinationFactory()

        subjects = combination.subjects
        assert len(subjects) == 3
        assert len({subject.pk for subject in subjects}) == 3
        assert all(subject.grade == 10 for subject in subjects)
        assert all(subject.category == 'Elective' for subject in subjects)

    def test_duplicate_subjects_violate_database_constraint(self):
        combination = SubjectCombinationFactory()
        combination.subject_two = combination.subject_one

        with pytest.raises(IntegrityError), transaction.atomic():
            combination.save()

    @pytest.mark.parametrize(
        ('subject_overrides', 'expected_message'),
        [
            ({'grade': 9, 'category': 'Elective'}, 'Grade 10'),
            ({'grade': 10, 'category': 'Core'}, 'elective'),
            ({'grade': 10, 'category': 'Elective', 'is_active': False}, 'active'),
        ],
    )
    def test_subjects_must_be_active_grade_10_electives(
        self,
        subject_overrides,
        expected_message,
    ):
        combination = SubjectCombinationFactory()
        combination.subject_one = SubjectFactory(**subject_overrides)

        with pytest.raises(ValidationError, match=expected_message):
            combination.full_clean()

    def test_track_must_belong_to_same_framework_version(self):
        combination = SubjectCombinationFactory()
        combination.framework_version = FrameworkVersionFactory()

        with pytest.raises(ValidationError, match='framework version'):
            combination.full_clean()

    def test_code_is_unique_within_framework_version(self):
        combination = SubjectCombinationFactory(code='STEM-PURE-01')

        with pytest.raises(IntegrityError), transaction.atomic():
            SubjectCombinationFactory(
                framework_version=combination.framework_version,
                track=combination.track,
                code=combination.code,
            )

    def test_code_can_repeat_in_another_framework_version(self):
        SubjectCombinationFactory(code='STEM-PURE-01')

        repeated = SubjectCombinationFactory(code='STEM-PURE-01')

        assert repeated.pk is not None


class TestSchoolOffering:
    def test_school_and_combination_pair_is_unique(self):
        offering = SchoolOfferingFactory()

        with pytest.raises(IntegrityError), transaction.atomic():
            SchoolOfferingFactory(
                school=offering.school,
                combination=offering.combination,
            )

    def test_school_can_offer_multiple_combinations(self):
        school = SchoolFactory()

        first = SchoolOfferingFactory(school=school)
        second = SchoolOfferingFactory(school=school)

        assert first.combination_id != second.combination_id
