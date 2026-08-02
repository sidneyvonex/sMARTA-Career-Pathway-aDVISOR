import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import School, StudentProfile, User
from counselors.models import (
    CounselorAssignment,
    CounselorIntervention,
    CounselorNote,
)
from guidance.models import (
    FrameworkVersion,
    LearnerCombinationChoice,
    LearnerPlan,
    PlanMilestone,
    SchoolOffering,
    SubjectCombination,
)
from notifications.models import Notification
from parents.models import ParentStudentLink
from riasec.models import (
    CURRENT_ALGORITHM_VERSION,
    CURRENT_INSTRUMENT_VERSION,
    Pathway,
    Recommendation,
    RIASECAssessment,
    RIASECScore,
)
from riasec.scoring import build_interest_explanation, compute_pathway_fits
from students.models import CBCGrade, StudentSubject, Subject
from system_admin.models import AuditLog


DEMO_DOMAIN = 'demo.smartashauri.test'
DEMO_SCHOOL_PREFIX = 'PILOT-'
PILOT_COUNTIES = (
    ('kiambu', 'Kiambu', 'KIA'),
    ('muranga', "Murang'a", 'MUR'),
    ('nyeri', 'Nyeri', 'NYE'),
    ('kirinyaga', 'Kirinyaga', 'KIR'),
    ('nyandarua', 'Nyandarua', 'NYA'),
)
PILOT_OFFERING_CODES = {
    'kiambu': ('ST1042', 'ST2007', 'SS2019', 'AS2009'),
    'muranga': ('ST2067', 'ST3074', 'SS1006', 'AS1021'),
    'nyeri': ('ST1042', 'ST2067', 'SS2033', 'AS1049'),
    'kirinyaga': ('ST2007', 'ST3074', 'SS2019', 'AS2009'),
    'nyandarua': ('ST1042', 'ST2007', 'SS1006', 'AS1021'),
}

DEMO_USERS = {
    'system_admin': {
        'email': f'system.admin@{DEMO_DOMAIN}',
        'first_name': 'Amina',
        'last_name': 'Mwangi',
        'role': 'system_admin',
        'county': 'kiambu',
    },
    'school_admin': {
        'email': f'school.admin@{DEMO_DOMAIN}',
        'first_name': 'Peter',
        'last_name': 'Kamau',
        'role': 'school_admin',
        'county': 'kiambu',
    },
    'counselor_one': {
        'email': f'counsellor.one@{DEMO_DOMAIN}',
        'first_name': 'Grace',
        'last_name': 'Wanjiku',
        'role': 'counselor',
        'county': 'kiambu',
    },
    'counselor_two': {
        'email': f'counsellor.two@{DEMO_DOMAIN}',
        'first_name': 'Daniel',
        'last_name': 'Otieno',
        'role': 'counselor',
        'county': 'kiambu',
    },
    'learner_ready': {
        'email': f'learner.ready@{DEMO_DOMAIN}',
        'first_name': 'Njeri',
        'last_name': 'Maina',
        'role': 'student',
        'county': 'kiambu',
    },
    'learner_review': {
        'email': f'learner.review@{DEMO_DOMAIN}',
        'first_name': 'Brian',
        'last_name': 'Kariuki',
        'role': 'student',
        'county': 'kiambu',
    },
    'learner_starting': {
        'email': f'learner.starting@{DEMO_DOMAIN}',
        'first_name': 'Asha',
        'last_name': 'Hassan',
        'role': 'student',
        'county': 'kiambu',
    },
    'parent': {
        'email': f'parent@{DEMO_DOMAIN}',
        'first_name': 'Lucy',
        'last_name': 'Maina',
        'role': 'parent',
        'county': 'kiambu',
    },
}


class Command(BaseCommand):
    help = 'Seed a repeatable five-county dataset for the pilot presentation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            help=(
                'Password for all demo accounts. Prefer the '
                'PILOT_DEMO_PASSWORD environment variable outside local development.'
            ),
        )

    def handle(self, *args, **options):
        password = options.get('password') or os.environ.get('PILOT_DEMO_PASSWORD')
        if not password:
            raise CommandError(
                'Provide --password or set PILOT_DEMO_PASSWORD. '
                'The seed command never stores a default credential.'
            )
        if len(password) < 10:
            raise CommandError('The demo password must contain at least 10 characters.')

        with transaction.atomic():
            framework, combinations, grade_subjects = self._catalogue()
            schools = self._schools()
            users = self._users(password=password, primary_school=schools['kiambu'])
            profiles = self._profiles(users=users, school=schools['kiambu'])
            self._school_offerings(schools=schools, combinations=combinations)
            self._academic_evidence(
                profiles=profiles,
                subjects=grade_subjects,
                verifier=users['school_admin'],
            )
            self._assessments(profiles=profiles)
            choices, plans = self._choices_and_plans(
                profiles=profiles,
                combinations=combinations,
            )
            self._relationships(users=users, profiles=profiles, school=schools['kiambu'])
            self._notifications(users=users)
            self._audit_events(
                users=users,
                school=schools['kiambu'],
                choices=choices,
                plans=plans,
                framework=framework,
            )

        self.stdout.write(self.style.SUCCESS('Pilot demo data is ready.'))
        self.stdout.write(
            f'Created or refreshed 5 schools and {len(DEMO_USERS)} accounts.'
        )
        self.stdout.write('Demo account emails:')
        for spec in DEMO_USERS.values():
            self.stdout.write(f"  - {spec['email']}")
        self.stdout.write('Password source accepted; password was not printed.')

    def _catalogue(self):
        framework = FrameworkVersion.objects.current()
        if framework is None:
            raise CommandError(
                'No active guidance framework exists. Run migrations before seeding.'
            )

        combinations = list(
            SubjectCombination.objects.filter(
                framework_version=framework,
                is_active=True,
                track__is_active=True,
            )
            .select_related(
                'track__pathway',
                'subject_one',
                'subject_two',
                'subject_three',
            )
            .order_by('code')
        )
        pathways = Pathway.objects.count()
        if pathways < 3 or len(combinations) < 5:
            raise CommandError(
                'The pilot pathway and combination catalogue is incomplete. '
                'Run migrations before seeding.'
            )

        grade_subjects = list(
            Subject.objects.filter(grade=9, is_active=True).order_by('code')[:5]
        )
        if len(grade_subjects) < 5:
            raise CommandError(
                'The Grade 9 subject catalogue is incomplete. Run migrations before seeding.'
            )
        return framework, combinations, grade_subjects

    def _schools(self):
        schools = {}
        for county, county_label, code in PILOT_COUNTIES:
            school, _ = School.objects.update_or_create(
                school_code=f'{DEMO_SCHOOL_PREFIX}{code}-001',
                defaults={
                    'name': f'Smarta Shauri {county_label} Demo School',
                    'county': county,
                    'email': f'{county}@schools.{DEMO_DOMAIN}',
                    'phone': '+254700000000',
                    'is_active': True,
                },
            )
            schools[county] = school
        return schools

    def _users(self, *, password, primary_school):
        users = {}
        for key, spec in DEMO_USERS.items():
            school = primary_school if spec['role'] in {
                'school_admin',
                'counselor',
                'student',
            } else None
            user, _ = User.objects.update_or_create(
                email=spec['email'],
                defaults={
                    'first_name': spec['first_name'],
                    'last_name': spec['last_name'],
                    'role': spec['role'],
                    'county': spec['county'],
                    'school': school,
                    'is_active': True,
                    'is_email_verified': True,
                    'is_staff': spec['role'] == 'system_admin',
                    'is_superuser': spec['role'] == 'system_admin',
                },
            )
            user.set_password(password)
            user.save(update_fields=['password'])
            users[key] = user
        return users

    def _profiles(self, *, users, school):
        profile_specs = {
            'learner_ready': {
                'bio': 'I enjoy practical science projects and solving community problems.',
                'career_interests': 'Engineering, technology and environmental solutions',
                'date_of_birth': date(2011, 3, 12),
            },
            'learner_review': {
                'bio': 'I enjoy creative projects, teamwork and communicating ideas.',
                'career_interests': 'Design, media and community work',
                'date_of_birth': date(2011, 7, 24),
            },
            'learner_starting': {
                'bio': 'I am beginning to explore the senior school pathways.',
                'career_interests': 'Still exploring',
                'date_of_birth': date(2011, 11, 8),
            },
        }
        profiles = {}
        for key, details in profile_specs.items():
            profile, _ = StudentProfile.objects.update_or_create(
                user=users[key],
                defaults={
                    'mode': 'school_linked',
                    'school': school,
                    'school_membership_status': 'active',
                    'grade': 9,
                    **details,
                },
            )
            profiles[key] = profile
        return profiles

    def _school_offerings(self, *, schools, combinations):
        combinations_by_code = {
            combination.code: combination for combination in combinations
        }
        for county, school in schools.items():
            try:
                selected = [
                    combinations_by_code[code]
                    for code in PILOT_OFFERING_CODES[county]
                ]
            except KeyError as exc:
                raise CommandError(
                    f'The pilot catalogue is missing combination {exc.args[0]}. '
                    'Run migrations before seeding.'
                ) from exc
            SchoolOffering.objects.filter(
                school=school,
                combination__framework_version=combinations[0].framework_version,
            ).exclude(combination__in=selected).update(is_active=False)
            for combination in selected:
                SchoolOffering.objects.update_or_create(
                    school=school,
                    combination=combination,
                    defaults={'is_active': True},
                )

    def _academic_evidence(self, *, profiles, subjects, verifier):
        levels = {
            'learner_ready': ('EE2', 'ME1', 'EE1', 'ME2', 'EE2'),
            'learner_review': ('ME2', 'AE1', 'ME1', 'ME2', 'AE2'),
            'learner_starting': ('AE1', 'ME2', 'AE2', 'ME1', 'ME2'),
        }
        current_year = timezone.localdate().year
        verified_at = timezone.now()
        for profile_key, profile in profiles.items():
            for subject, level in zip(subjects, levels[profile_key]):
                enrollment, _ = StudentSubject.objects.get_or_create(
                    student_profile=profile,
                    subject=subject,
                )
                CBCGrade.objects.update_or_create(
                    student_subject=enrollment,
                    term=1,
                    year=current_year,
                    defaults={
                        'level': level,
                        'source': 'school',
                        'verified_by': verifier,
                        'verified_school': verifier.school,
                        'verified_at': verified_at,
                    },
                )

    def _assessments(self, *, profiles):
        score_sets = {
            'learner_ready': {'R': 21, 'I': 23, 'A': 14, 'S': 16, 'E': 18, 'C': 19},
            'learner_review': {'R': 13, 'I': 16, 'A': 23, 'S': 22, 'E': 18, 'C': 15},
        }
        pathway_values = list(
            Pathway.objects.order_by('pk').values(
                'id',
                'name',
                'description',
                'weight_r',
                'weight_i',
                'weight_a',
                'weight_s',
                'weight_e',
                'weight_c',
            )
        )
        pathway_objects = {pathway.pk: pathway for pathway in Pathway.objects.all()}

        for profile_key, scores in score_sets.items():
            profile = profiles[profile_key]
            assessment = profile.riasec_assessments.order_by('pk').first()
            if assessment is None:
                assessment = RIASECAssessment.objects.create(
                    student_profile=profile,
                    instrument_version=CURRENT_INSTRUMENT_VERSION,
                )
            else:
                assessment.instrument_version = CURRENT_INSTRUMENT_VERSION
                assessment.save(update_fields=['instrument_version'])
                profile.riasec_assessments.exclude(pk=assessment.pk).delete()

            for dimension, raw_score in scores.items():
                RIASECScore.objects.update_or_create(
                    assessment=assessment,
                    dimension=dimension,
                    defaults={'raw_score': raw_score},
                )

            assessment.recommendations.all().delete()
            for fit in compute_pathway_fits(scores, pathway_values):
                pathway_data = fit['pathway']
                Recommendation.objects.create(
                    assessment=assessment,
                    pathway=pathway_objects[pathway_data['id']],
                    rank=fit['rank'],
                    fit_score=fit['fit_score'],
                    fit_pct=fit['fit_pct'],
                    algorithm_version=CURRENT_ALGORITHM_VERSION,
                    explanation=build_interest_explanation(scores, pathway_data),
                )

    def _choices_and_plans(self, *, profiles, combinations):
        choices = {}
        plans = {}
        combinations_by_code = {
            combination.code: combination for combination in combinations
        }
        choice_specs = {
            'learner_ready': (
                combinations_by_code['ST1042'],
                combinations_by_code['ST2007'],
            ),
            'learner_review': (
                combinations_by_code['SS2019'],
                combinations_by_code['AS2009'],
            ),
        }
        for profile_key, (provisional_combination, saved_combination) in choice_specs.items():
            profile = profiles[profile_key]
            profile.combination_choices.update(
                status=LearnerCombinationChoice.STATUS_SAVED
            )
            provisional, _ = LearnerCombinationChoice.objects.update_or_create(
                student_profile=profile,
                combination=provisional_combination,
                defaults={
                    'status': LearnerCombinationChoice.STATUS_PROVISIONAL,
                    'learner_reason': (
                        'This option connects my interests with subjects I want to '
                        'explore further.'
                    ),
                },
            )
            LearnerCombinationChoice.objects.update_or_create(
                student_profile=profile,
                combination=saved_combination,
                defaults={
                    'status': LearnerCombinationChoice.STATUS_SAVED,
                    'learner_reason': 'I saved this as a useful alternative to compare.',
                },
            )
            choices[profile_key] = provisional

        now = timezone.now()
        ready_plan, _ = LearnerPlan.objects.update_or_create(
            student_profile=profiles['learner_ready'],
            defaults={
                'provisional_choice': choices['learner_ready'],
                'learner_reason': (
                    'My evidence and interests support discussing this combination '
                    'with my counsellor and parent.'
                ),
                'review_status': LearnerPlan.STATUS_REVIEWED,
                'reviewed_at': now,
            },
        )
        review_plan, _ = LearnerPlan.objects.update_or_create(
            student_profile=profiles['learner_review'],
            defaults={
                'provisional_choice': choices['learner_review'],
                'learner_reason': (
                    'I would like help comparing this option with the school offering.'
                ),
                'review_status': LearnerPlan.STATUS_READY,
                'reviewed_at': None,
            },
        )
        plans['learner_ready'] = ready_plan
        plans['learner_review'] = review_plan

        for profile_key, selected_combinations in choice_specs.items():
            profiles[profile_key].combination_choices.exclude(
                combination__in=selected_combinations
            ).delete()

        milestone_specs = {
            ready_plan: (
                ('Complete interest assessment', -7, True, 0),
                ('Discuss evidence with counsellor', -2, True, 1),
                ('Confirm next-term subjects', 14, False, 2),
            ),
            review_plan: (
                ('Compare two subject combinations', 3, False, 0),
                ('Meet assigned counsellor', 7, False, 1),
            ),
        }
        for plan, milestones in milestone_specs.items():
            for title, due_offset, complete, position in milestones:
                PlanMilestone.objects.update_or_create(
                    plan=plan,
                    title=title,
                    defaults={
                        'due_date': timezone.localdate() + timedelta(days=due_offset),
                        'is_complete': complete,
                        'completed_at': now if complete else None,
                        'position': position,
                    },
                )
        return choices, plans

    def _relationships(self, *, users, profiles, school):
        assignment_specs = {
            'learner_ready': 'counselor_one',
            'learner_review': 'counselor_one',
            'learner_starting': 'counselor_two',
        }
        CounselorAssignment.objects.filter(
            student_profile__in=profiles.values(),
            is_active=True,
        ).update(is_active=False)
        for profile_key, counselor_key in assignment_specs.items():
            CounselorAssignment.objects.update_or_create(
                counselor=users[counselor_key],
                student_profile=profiles[profile_key],
                school=school,
                defaults={'is_active': True},
            )

        ParentStudentLink.objects.update_or_create(
            parent=users['parent'],
            student=users['learner_ready'],
            defaults={
                'claimed_relationship': ParentStudentLink.RELATIONSHIP_GUARDIAN,
                'status': ParentStudentLink.STATUS_ACTIVE,
                'learner_approved_at': timezone.now(),
                'revoked_at': None,
            },
        )
        CounselorNote.objects.get_or_create(
            counselor=users['counselor_one'],
            student=users['learner_ready'],
            body=(
                'Reviewed the learner evidence and agreed to keep the current '
                'combination as the provisional direction.'
            ),
            defaults={'visible_to_parent': True},
        )
        CounselorIntervention.objects.update_or_create(
            counselor=users['counselor_one'],
            student=users['learner_review'],
            category=CounselorIntervention.CATEGORY_COMBINATION,
            defaults={
                'action_agreed': (
                    'Compare the provisional combination with the subjects offered '
                    'by the school before the review meeting.'
                ),
                'follow_up_date': timezone.localdate() + timedelta(days=7),
                'status': CounselorIntervention.STATUS_OPEN,
                'learner_visible': True,
                'parent_visible': False,
            },
        )

    def _notifications(self, *, users):
        notification_specs = (
            (
                users['learner_review'],
                'counselor_assigned',
                'Grace Wanjiku is available to review your provisional choice.',
                False,
            ),
            (
                users['counselor_one'],
                'assessment_submitted',
                'Brian Kariuki has requested a review of a provisional choice.',
                False,
            ),
            (
                users['parent'],
                'child_assessment_complete',
                'Njeri Maina has completed the interest assessment.',
                False,
            ),
            (
                users['learner_ready'],
                'counselor_note',
                'Your counsellor has added a shared review note.',
                True,
            ),
        )
        for user, notification_type, message, read in notification_specs:
            Notification.objects.update_or_create(
                user=user,
                type=notification_type,
                message=message,
                defaults={'read': read},
            )

    def _audit_events(self, *, users, school, choices, plans, framework):
        events = (
            (
                users['system_admin'],
                'school_created',
                'school',
                school.pk,
                {'source': 'pilot_demo_seed', 'county': school.county},
            ),
            (
                users['learner_ready'],
                'provisional_combination_changed',
                'choice',
                choices['learner_ready'].pk,
                {
                    'source': 'pilot_demo_seed',
                    'framework_code': framework.code,
                },
            ),
            (
                users['counselor_one'],
                'plan_review_status_changed',
                'plan',
                plans['learner_ready'].pk,
                {'source': 'pilot_demo_seed', 'status': LearnerPlan.STATUS_REVIEWED},
            ),
            (
                users['learner_review'],
                'plan_review_status_changed',
                'plan',
                plans['learner_review'].pk,
                {'source': 'pilot_demo_seed', 'status': LearnerPlan.STATUS_READY},
            ),
        )
        for actor, action, target_type, target_id, details in events:
            AuditLog.objects.update_or_create(
                actor=actor,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details__source='pilot_demo_seed',
                defaults={'details': details},
            )
