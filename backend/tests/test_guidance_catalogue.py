from datetime import date
from importlib import import_module

import pytest
from django.apps import apps as django_apps

from accounts.models import COUNTY_CHOICES, School
from guidance.models import (
    FrameworkVersion,
    PathwayTrack,
    SchoolOffering,
    SubjectCombination,
)


pytestmark = pytest.mark.django_db

PILOT_FRAMEWORK_CODE = 'CBC-SS-PILOT-2026'
PILOT_SCHOOL_CODE_PREFIX = 'PILOT-'

EXPECTED_TRACKS = {
    'STEM': {'PURE-SCIENCES', 'APPLIED-SCIENCES', 'TECHNICAL-STUDIES'},
    'Social Sciences': {'LANGUAGES-LITERATURE', 'HUMANITIES-BUSINESS'},
    'Arts & Sports Science': {'ARTS', 'SPORTS-RECREATION'},
}

EXPECTED_COMBINATIONS = {
    'ST1042': ('AGR10', 'BIO10', 'CHE10'),
    'ST2007': ('BST10', 'CPS10', 'PHY10'),
    'ST2067': ('AGR10', 'CPS10', 'PHY10'),
    'ST3074': ('CPS10', 'GSC10', 'MDT10'),
    'SS1006': ('ARA10', 'CPS10', 'FRN10'),
    'SS2019': ('CHR10', 'GEO10', 'HCT10'),
    'SS2033': ('CPS10', 'GEO10', 'IRE10'),
    'AS1021': ('CPS10', 'FAR10', 'MDA10'),
    'AS1049': ('LIE10', 'MDA10', 'TFM10'),
    'AS2009': ('BIO10', 'GEO10', 'SRE10'),
}


class TestPilotFrameworkSeed:
    def test_current_framework_is_source_dated_and_scoped_as_curated(self):
        framework = FrameworkVersion.objects.current()

        assert framework is not None
        assert framework.code == PILOT_FRAMEWORK_CODE
        assert framework.effective_date == date(2026, 1, 1)
        assert framework.source_url.startswith(
            'https://selection.education.go.ke/'
        )
        assert 'not the complete national catalogue' in framework.description.casefold()

    def test_current_framework_has_expected_tracks_for_all_three_pathways(self):
        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)

        actual = {
            pathway_name: set(
                PathwayTrack.objects.filter(
                    framework_version=framework,
                    pathway__name=pathway_name,
                ).values_list('code', flat=True)
            )
            for pathway_name in EXPECTED_TRACKS
        }

        assert actual == EXPECTED_TRACKS

    def test_curated_combinations_match_official_codes_and_subjects(self):
        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)
        combinations = SubjectCombination.objects.filter(
            framework_version=framework
        ).select_related('subject_one', 'subject_two', 'subject_three')

        actual = {
            combination.code: tuple(
                sorted(subject.code for subject in combination.subjects)
            )
            for combination in combinations
        }

        assert actual == EXPECTED_COMBINATIONS

    def test_combinations_cover_recommended_pathway_distribution(self):
        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)
        counts = {
            pathway_name: SubjectCombination.objects.filter(
                framework_version=framework,
                track__pathway__name=pathway_name,
            ).count()
            for pathway_name in EXPECTED_TRACKS
        }

        assert counts == {
            'STEM': 4,
            'Social Sciences': 3,
            'Arts & Sports Science': 3,
        }

    def test_every_seeded_combination_is_verified_and_resolves_three_subjects(self):
        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)

        for combination in SubjectCombination.objects.filter(
            framework_version=framework
        ).select_related('subject_one', 'subject_two', 'subject_three', 'track'):
            combination.full_clean()
            assert len({subject.pk for subject in combination.subjects}) == 3
            assert combination.verification_status == 'verified'
            assert combination.source_checked_at == date(2026, 7, 31)
            assert combination.source_url.startswith(
                'https://selection.education.go.ke/'
            )


class TestPilotSchoolOfferingsSeed:
    def test_one_demonstration_school_is_seeded_per_pilot_county(self):
        schools = School.objects.filter(school_code__startswith=PILOT_SCHOOL_CODE_PREFIX)
        pilot_counties = {code for code, _name in COUNTY_CHOICES}

        assert schools.count() == 5
        assert set(schools.values_list('county', flat=True)) == pilot_counties
        assert all('Pilot' in school.name for school in schools)
        assert set(schools.values_list('verification_status', flat=True)) == {
            'demonstration'
        }

    def test_every_demonstration_school_has_representative_offerings(self):
        schools = list(
            School.objects.filter(school_code__startswith=PILOT_SCHOOL_CODE_PREFIX)
        )

        assert len(schools) == 5
        assert all(
            school.guidance_offerings.filter(is_active=True).count() >= 4
            for school in schools
        )
        assert not SchoolOffering.objects.filter(
            school__in=schools,
        ).exclude(verification_status='demonstration').exists()

    def test_offerings_cover_every_curated_combination(self):
        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)
        offered_codes = set(
            SchoolOffering.objects.filter(
                school__school_code__startswith=PILOT_SCHOOL_CODE_PREFIX,
                is_active=True,
            ).values_list('combination__code', flat=True)
        )
        curated_codes = set(
            framework.combinations.filter(is_active=True).values_list('code', flat=True)
        )

        assert offered_codes == curated_codes


class TestPilotCatalogueMigration:
    def test_forward_seed_is_idempotent(self):
        migration = import_module('guidance.migrations.0002_seed_pilot_catalogue')

        migration.seed_pilot_catalogue(django_apps, None)
        migration.seed_pilot_catalogue(django_apps, None)

        framework = FrameworkVersion.objects.get(code=PILOT_FRAMEWORK_CODE)
        assert framework.tracks.count() == 7
        assert framework.combinations.count() == 10
        assert School.objects.filter(
            school_code__startswith=PILOT_SCHOOL_CODE_PREFIX
        ).count() == 5
        assert SchoolOffering.objects.filter(
            school__school_code__startswith=PILOT_SCHOOL_CODE_PREFIX
        ).count() == 20

    def test_reverse_removes_only_pilot_seed_and_can_be_reapplied(self):
        migration = import_module('guidance.migrations.0002_seed_pilot_catalogue')
        unrelated_school = School.objects.create(
            name='Unrelated School',
            county='kiambu',
            school_code='UNRELATED-001',
        )

        migration.unseed_pilot_catalogue(django_apps, None)

        assert not FrameworkVersion.objects.filter(code=PILOT_FRAMEWORK_CODE).exists()
        assert not School.objects.filter(
            school_code__startswith=PILOT_SCHOOL_CODE_PREFIX
        ).exists()
        assert School.objects.filter(pk=unrelated_school.pk).exists()

        migration.seed_pilot_catalogue(django_apps, None)

        assert FrameworkVersion.objects.filter(code=PILOT_FRAMEWORK_CODE).exists()
        assert School.objects.filter(
            school_code__startswith=PILOT_SCHOOL_CODE_PREFIX
        ).count() == 5
