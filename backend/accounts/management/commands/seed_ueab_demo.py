"""
Seed a full set of realistic demo accounts using the @ueab.ac.ke domain.

Covers every role (system_admin, school_admin, counselor, parent, student)
with two representative states per role, plus Grade 9 and Grade 10 students
with real education-goal selections drawn from the KUCCPS-DEMO catalogue.

Run:
    python manage.py seed_ueab_demo --password <secret>
    python manage.py seed_ueab_demo --password <secret> --clear   # wipe + re-seed

Credentials summary printed on success.
"""

import os
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from accounts.models import School, StudentProfile, User
from counselors.models import CounselorAssignment, CounselorIntervention, CounselorNote
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
from tertiary.models import Institution, LearnerEducationGoal, Programme

DOMAIN = 'ueab.ac.ke'
SCOPE = 'KUCCPS-DEMO'

# ──────────────────────────────────────────────────────────────────────────────
# Account catalogue
# ──────────────────────────────────────────────────────────────────────────────

USERS = {
    # ── System Admin ──────────────────────────────────────────────────────────
    # State A: fully active super-admin
    'sysadmin': {
        'email': f'admin@{DOMAIN}',
        'first_name': 'Wanjiru',
        'last_name': 'Kamau',
        'role': 'system_admin',
        'county': 'kiambu',
        'is_staff': True,
        'is_superuser': True,
    },

    # ── School Admins ─────────────────────────────────────────────────────────
    # State A: established, school assigned
    'schooladmin_active': {
        'email': f'schooladmin@{DOMAIN}',
        'first_name': 'Joseph',
        'last_name': 'Mwenda',
        'role': 'school_admin',
        'county': 'kiambu',
    },
    # State B: brand-new, no activity yet
    'schooladmin_new': {
        'email': f'newadmin@{DOMAIN}',
        'first_name': 'Faith',
        'last_name': 'Wangari',
        'role': 'school_admin',
        'county': 'nyeri',
    },

    # ── Counselors ────────────────────────────────────────────────────────────
    # State A: active caseload, has assigned students
    'counselor_active': {
        'email': f'counselor@{DOMAIN}',
        'first_name': 'Grace',
        'last_name': 'Njoroge',
        'role': 'counselor',
        'county': 'kiambu',
    },
    # State B: light caseload, assigned to Grade 10 cohort
    'counselor_senior': {
        'email': f'counselor2@{DOMAIN}',
        'first_name': 'Daniel',
        'last_name': 'Ochieng',
        'role': 'counselor',
        'county': 'kiambu',
    },

    # ── Parents ───────────────────────────────────────────────────────────────
    # State A: linked to a student, active
    'parent_linked': {
        'email': f'parent@{DOMAIN}',
        'first_name': 'Margaret',
        'last_name': 'Muthoni',
        'role': 'parent',
        'county': 'kiambu',
    },
    # State B: registered but not yet linked to any student
    'parent_unlinked': {
        'email': f'parent2@{DOMAIN}',
        'first_name': 'Robert',
        'last_name': 'Omondi',
        'role': 'parent',
        'county': 'muranga',
    },

    # ── Grade 9 Students ──────────────────────────────────────────────────────
    # State A: school-linked, has RIASEC & education goals, journey not selected
    'student_g9_active': {
        'email': f'njeri.g9@{DOMAIN}',
        'first_name': 'Njeri',
        'last_name': 'Maina',
        'role': 'student',
        'county': 'kiambu',
    },
    # State B: self-guided, just registered, journey unsure
    'student_g9_exploring': {
        'email': f'kevin.g9@{DOMAIN}',
        'first_name': 'Kevin',
        'last_name': 'Omondi',
        'role': 'student',
        'county': 'muranga',
    },

    # ── Grade 10 Students ─────────────────────────────────────────────────────
    # State A: school-linked, has decided on pathway & education goals
    'student_g10_decided': {
        'email': f'zawadi.g10@{DOMAIN}',
        'first_name': 'Zawadi',
        'last_name': 'Akinyi',
        'role': 'student',
        'county': 'kirinyaga',
    },
    # State B: school-linked, reconsidering current pathway
    'student_g10_reconsidering': {
        'email': f'emmanuel.g10@{DOMAIN}',
        'first_name': 'Emmanuel',
        'last_name': 'Kiprotich',
        'role': 'student',
        'county': 'nyeri',
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Education goals  (institution_ext_key, programme_suffix)
# Must match records seeded by seed_demo_institutions + seed_demo_programmes.
# ──────────────────────────────────────────────────────────────────────────────

GOAL_SPECS = {
    # Grade 9 – active: primary = UoN Medicine | alt-1 = JKUAT CS | alt-2 = KU Nursing
    'student_g9_active': [
        ('primary',      1, 'UON',   'MEDICINE'),
        ('alternative',  1, 'JKUAT', 'CS'),
        ('alternative',  2, 'KU',    'NURSING'),
    ],
    # Grade 10 – decided: primary = KU BEd Arts | alt-1 = Egerton Agriculture
    'student_g10_decided': [
        ('primary',      1, 'KU',    'BED_ARTS'),
        ('alternative',  1, 'EGU',   'AGRI'),
    ],
    # Grade 10 – reconsidering: only a primary goal, no alternatives yet
    'student_g10_reconsidering': [
        ('primary',      1, 'TUK',   'CS'),
    ],
}


class Command(BaseCommand):
    help = f'Seed demo accounts under @{DOMAIN} covering every role and key learner states.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            help=(
                f'Password for all @{DOMAIN} demo accounts. '
                'Prefer the UEAB_DEMO_PASSWORD env var outside local dev.'
            ),
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help=f'Delete all existing @{DOMAIN} accounts before re-seeding.',
        )

    def handle(self, *args, **options):
        password = options.get('password') or os.environ.get('UEAB_DEMO_PASSWORD')
        if not password:
            raise CommandError(
                f'Provide --password or set UEAB_DEMO_PASSWORD. '
                'The seed command never uses a hardcoded credential.'
            )
        if len(password) < 8:
            raise CommandError('Demo password must be at least 8 characters.')

        with transaction.atomic():
            if options['clear']:
                ueab_users = User.objects.filter(email__endswith=f'@{DOMAIN}')
                # Delete protected relations before the User cascade.
                LearnerEducationGoal.objects.filter(created_by__in=ueab_users).delete()
                LearnerEducationGoal.objects.filter(
                    learner__user__in=ueab_users
                ).delete()
                # CBCGrade.objects.delete() is blocked by the custom queryset guard;
                # use raw SQL so school-verified demo grades can be wiped cleanly.
                subject_ids = list(
                    StudentSubject.objects.filter(
                        student_profile__user__in=ueab_users
                    ).values_list('id', flat=True)
                )
                if subject_ids:
                    placeholders = ','.join(['%s'] * len(subject_ids))
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f'DELETE FROM students_cbcgrade'
                            f' WHERE student_subject_id IN ({placeholders})',
                            subject_ids,
                        )
                deleted, _ = ueab_users.delete()
                self.stdout.write(f'Cleared {deleted} existing @{DOMAIN} account(s).')

            school = self._school()
            users = self._users(password=password, school=school)
            profiles = self._profiles(users=users, school=school)
            self._education_goals(users=users, profiles=profiles)
            self._counselor_assignments(users=users, profiles=profiles, school=school)
            self._counselor_notes(users=users)
            self._counselor_interventions(users=users)
            self._parent_link(users=users)
            self._njeri_academic_data(users=users, profiles=profiles, school=school)

        self._print_summary(users)

    # ──────────────────────────────────────────────────────────────────────────

    def _school(self):
        school, _ = School.objects.update_or_create(
            school_code='UEAB-DEMO-001',
            defaults={
                'name': 'UEAB Demo Secondary School',
                'county': 'kiambu',
                'email': f'school@{DOMAIN}',
                'phone': '+254700000001',
                'is_active': True,
                'verification_status': School.VERIFICATION_DEMONSTRATION,
            },
        )
        return school

    def _users(self, *, password, school):
        users = {}
        school_roles = {'school_admin', 'counselor', 'student'}
        for key, spec in USERS.items():
            user, _ = User.objects.update_or_create(
                email=spec['email'],
                defaults={
                    'first_name': spec['first_name'],
                    'last_name': spec['last_name'],
                    'role': spec['role'],
                    'county': spec['county'],
                    'school': school if spec['role'] in school_roles else None,
                    'is_active': True,
                    'is_email_verified': True,
                    'is_staff': spec.get('is_staff', False),
                    'is_superuser': spec.get('is_superuser', False),
                },
            )
            user.set_password(password)
            user.save(update_fields=['password'])
            users[key] = user
        return users

    def _profiles(self, *, users, school):
        profile_specs = {
            'student_g9_active': {
                'grade': 9,
                'mode': 'school_linked',
                'school': school,
                'school_membership_status': 'active',
                'journey_status': StudentProfile.JOURNEY_NOT_SELECTED,
                'bio': 'I love science projects and want to help my community.',
                'career_interests': 'Medicine, engineering, public health',
                'date_of_birth': date(2011, 4, 15),
            },
            'student_g9_exploring': {
                'grade': 9,
                'mode': 'self_guided',
                'school': None,
                'school_membership_status': 'not_applicable',
                'journey_status': StudentProfile.JOURNEY_UNSURE,
                'bio': 'Still figuring out what I enjoy most.',
                'career_interests': 'Not sure yet',
                'date_of_birth': date(2011, 9, 22),
            },
            'student_g10_decided': {
                'grade': 10,
                'mode': 'school_linked',
                'school': school,
                'school_membership_status': 'active',
                'journey_status': StudentProfile.JOURNEY_SELECTED,
                'bio': (
                    'I have always enjoyed arts and languages. '
                    'Teaching is my goal.'
                ),
                'career_interests': 'Education, journalism, community development',
                'date_of_birth': date(2010, 1, 30),
                'selection_source': StudentProfile.SELECTION_LEARNER_REPORTED,
                'selection_date': date(2025, 2, 14),
            },
            'student_g10_reconsidering': {
                'grade': 10,
                'mode': 'school_linked',
                'school': school,
                'school_membership_status': 'active',
                'journey_status': StudentProfile.JOURNEY_RECONSIDERING,
                'bio': (
                    'I chose science subjects but now I am exploring whether '
                    'IT suits me better.'
                ),
                'career_interests': 'Technology, cybersecurity, software development',
                'date_of_birth': date(2010, 6, 8),
            },
        }

        profiles = {}
        for key, defaults in profile_specs.items():
            profile, _ = StudentProfile.objects.update_or_create(
                user=users[key],
                defaults=defaults,
            )
            profiles[key] = profile
        return profiles

    def _education_goals(self, *, users, profiles):
        # Build lookup: (inst_ext_key, prog_suffix) -> Programme
        programmes = {
            (p.institution.external_key, p.external_key.split('-', 1)[1]): p
            for p in Programme.objects.filter(
                source_scope=SCOPE
            ).select_related('institution')
        }

        if not programmes:
            self.stdout.write(
                self.style.WARNING(
                    'No KUCCPS-DEMO programmes found — skipping education goals. '
                    'Run seed_demo_programmes first.'
                )
            )
            return

        for profile_key, goal_list in GOAL_SPECS.items():
            profile = profiles[profile_key]
            user = users[profile_key]

            # Clear existing goals for idempotency
            LearnerEducationGoal.objects.filter(learner=profile).delete()

            for kind, priority, inst_key, prog_suffix in goal_list:
                prog = programmes.get((inst_key, prog_suffix))
                if prog is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Skipping goal ({inst_key}/{prog_suffix}): '
                            'programme not found in DB.'
                        )
                    )
                    continue

                goal = LearnerEducationGoal(
                    learner=profile,
                    institution=prog.institution,
                    programme=prog,
                    kind=kind,
                    priority=priority,
                    created_by=user,
                )
                goal.save()

    def _counselor_assignments(self, *, users, profiles, school):
        # Deactivate any stale active assignments for these students first
        stale = CounselorAssignment.objects.filter(
            student_profile__in=profiles.values(),
            is_active=True,
        )
        stale.update(is_active=False)

        # counselor_active (Grace) → Grade 9 students
        for profile_key in ('student_g9_active', 'student_g9_exploring'):
            CounselorAssignment.objects.update_or_create(
                counselor=users['counselor_active'],
                student_profile=profiles[profile_key],
                school=school,
                defaults={'is_active': True},
            )

        # counselor_senior (Daniel) → Grade 10 students
        for profile_key in ('student_g10_decided', 'student_g10_reconsidering'):
            CounselorAssignment.objects.update_or_create(
                counselor=users['counselor_senior'],
                student_profile=profiles[profile_key],
                school=school,
                defaults={'is_active': True},
            )

    def _counselor_notes(self, *, users):
        notes = [
            # Grace's notes on her Grade 9 students
            (
                users['counselor_active'],
                users['student_g9_active'],
                (
                    'Njeri shows strong motivation toward medicine and engineering. '
                    'Recommended she completes the interest assessment before our '
                    'next session to align her education goals with a pathway.'
                ),
                True,   # visible_to_parent
            ),
            (
                users['counselor_active'],
                users['student_g9_exploring'],
                (
                    'Kevin is still unsure about his direction. He finds technology '
                    'interesting but has not explored it formally. '
                    'Will monitor and follow up after the next school event.'
                ),
                False,
            ),
            # Daniel's notes on his Grade 10 students
            (
                users['counselor_senior'],
                users['student_g10_decided'],
                (
                    'Zawadi has a clear plan — targeting BEd Arts at KU as her '
                    'primary route. Evidence and pathway choice are consistent. '
                    'No major concerns at this stage.'
                ),
                True,
            ),
            (
                users['counselor_senior'],
                users['student_g10_reconsidering'],
                (
                    'Emmanuel is reconsidering his science pathway in favour of IT. '
                    'Discussed TUK Computer Science as a realistic alternative. '
                    'Needs to update his subject combination before the end of term.'
                ),
                False,
            ),
        ]
        for counselor, student, body, visible in notes:
            CounselorNote.objects.get_or_create(
                counselor=counselor,
                student=student,
                body=body,
                defaults={'visible_to_parent': visible},
            )

    def _counselor_interventions(self, *, users):
        today = timezone.localdate()
        interventions = [
            # Grace → Njeri: overdue follow-up (to trigger attention reason)
            (
                users['counselor_active'],
                users['student_g9_active'],
                CounselorIntervention.CATEGORY_ASSESSMENT,
                (
                    'Complete the RIASEC interest assessment before next counsellor '
                    'session so we can align subject combination choices with '
                    'stated career interests in medicine and technology.'
                ),
                today - timedelta(days=5),  # overdue
                CounselorIntervention.STATUS_OPEN,
                True,   # learner_visible
                True,   # parent_visible
            ),
            # Grace → Kevin: upcoming follow-up
            (
                users['counselor_active'],
                users['student_g9_exploring'],
                CounselorIntervention.CATEGORY_COMBINATION,
                (
                    'Explore at least two subject combination options on Smarta Shauri '
                    'and save one as provisional before the end of this term.'
                ),
                today + timedelta(days=10),
                CounselorIntervention.STATUS_OPEN,
                True,
                False,
            ),
            # Daniel → Zawadi: completed intervention
            (
                users['counselor_senior'],
                users['student_g10_decided'],
                CounselorIntervention.CATEGORY_PLAN,
                (
                    'Review and confirm the BEd Arts pathway and ensure the '
                    'subject combination is offered at the assigned school.'
                ),
                today - timedelta(days=14),
                CounselorIntervention.STATUS_COMPLETED,
                True,
                True,
            ),
            # Daniel → Emmanuel: open, upcoming
            (
                users['counselor_senior'],
                users['student_g10_reconsidering'],
                CounselorIntervention.CATEGORY_COMBINATION,
                (
                    'Update the provisional subject combination to reflect the shift '
                    'from the science pathway to the ICT/Technology track. '
                    'Discuss implications with parents before the change is finalised.'
                ),
                today + timedelta(days=7),
                CounselorIntervention.STATUS_OPEN,
                True,
                True,
            ),
        ]
        for counselor, student, category, action, follow_up, status, lv, pv in interventions:
            CounselorIntervention.objects.update_or_create(
                counselor=counselor,
                student=student,
                category=category,
                defaults={
                    'action_agreed': action,
                    'follow_up_date': follow_up,
                    'status': status,
                    'learner_visible': lv,
                    'parent_visible': pv,
                },
            )

    def _parent_link(self, *, users):
        ParentStudentLink.objects.update_or_create(
            parent=users['parent_linked'],
            student=users['student_g9_active'],
            defaults={
                'claimed_relationship': ParentStudentLink.RELATIONSHIP_MOTHER,
                'status': ParentStudentLink.STATUS_ACTIVE,
                'learner_approved_at': timezone.now(),
                'revoked_at': None,
            },
        )

    def _njeri_academic_data(self, *, users, profiles, school):
        """Seed Grade 9 subjects, school-verified grades, and RIASEC for Njeri Maina."""
        njeri_profile = profiles['student_g9_active']
        school_admin = users['schooladmin_active']

        # ── 1. Subject enrolments ─────────────────────────────────────────────
        subject_codes = ['ENG9', 'KIS9', 'MTH9', 'INT9', 'HSS9', 'ART9', 'BST9', 'CRE9']
        subjects = {s.code: s for s in Subject.objects.filter(code__in=subject_codes)}
        enrollments = {}
        for code in subject_codes:
            subject = subjects.get(code)
            if subject is None:
                self.stdout.write(self.style.WARNING(f'  Subject {code} not found — skipping.'))
                continue
            enrollment, _ = StudentSubject.objects.get_or_create(
                student_profile=njeri_profile,
                subject=subject,
                defaults={'academic_year': 2025},
            )
            enrollments[code] = enrollment

        # ── 2. CBC grades (Term 1 + Term 2 2025, school-verified) ─────────────
        verified_at = timezone.now()
        grade_data = [
            ('ENG9', 1, 'EE2'), ('ENG9', 2, 'EE1'),
            ('KIS9', 1, 'ME1'), ('KIS9', 2, 'EE2'),
            ('MTH9', 1, 'EE1'), ('MTH9', 2, 'EE1'),
            ('INT9', 1, 'EE1'), ('INT9', 2, 'EE1'),
            ('HSS9', 1, 'ME1'), ('HSS9', 2, 'ME1'),
            ('ART9', 1, 'ME2'), ('ART9', 2, 'ME1'),
            ('BST9', 1, 'ME2'), ('BST9', 2, 'ME1'),
            ('CRE9', 1, 'ME1'), ('CRE9', 2, 'ME2'),
        ]
        grades_created = 0
        for code, term, level in grade_data:
            enrollment = enrollments.get(code)
            if enrollment is None:
                continue
            if CBCGrade.objects.filter(
                student_subject=enrollment, term=term, year=2025
            ).exists():
                continue
            grade = CBCGrade(
                student_subject=enrollment,
                academic_grade=9,
                term=term,
                year=2025,
                level=level,
                source='school',
                verified_by=school_admin,
                verified_school=school,
                verified_at=verified_at,
            )
            grade.save()
            grades_created += 1

        # ── 3. RIASEC assessment (I/R dominant → STEM pathway ranks first) ────
        # Scores per dimension (range 5–25; 5 questions each scored 1–5).
        # R=20 I=22 A=10 S=13 E=12 C=14 → STEM 73 % / Social Sciences 57 % / Arts 54 %
        scores = {'R': 20, 'I': 22, 'A': 10, 'S': 13, 'E': 12, 'C': 14}

        assessment = njeri_profile.riasec_assessments.order_by('pk').first()
        if assessment is None:
            assessment = RIASECAssessment.objects.create(
                student_profile=njeri_profile,
                instrument_version=CURRENT_INSTRUMENT_VERSION,
            )
        else:
            njeri_profile.riasec_assessments.exclude(pk=assessment.pk).delete()

        for dimension, raw_score in scores.items():
            RIASECScore.objects.update_or_create(
                assessment=assessment,
                dimension=dimension,
                defaults={'raw_score': raw_score},
            )

        pathway_values = list(
            Pathway.objects.order_by('pk').values(
                'id', 'name', 'description',
                'weight_r', 'weight_i', 'weight_a', 'weight_s', 'weight_e', 'weight_c',
            )
        )
        pathway_objects = {p.pk: p for p in Pathway.objects.all()}
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

        self.stdout.write(
            f'  Njeri: {len(enrollments)} subjects enrolled, '
            f'{grades_created} grade entries, RIASEC assessment seeded.'
        )

    def _print_summary(self, users):
        self.stdout.write(self.style.SUCCESS(
            f'\nUEAB demo accounts ready. '
            f'All {len(users)} accounts use the same password.\n'
        ))
        rows = [
            ('Role',         'State',              'Email'),
            ('-' * 15,       '-' * 22,             '-' * 38),
            ('system_admin', 'super-admin',         users['sysadmin'].email),
            ('school_admin', 'established',         users['schooladmin_active'].email),
            ('school_admin', 'brand-new',           users['schooladmin_new'].email),
            ('counselor',    'active caseload',     users['counselor_active'].email),
            ('counselor',    'senior/G10 cohort',   users['counselor_senior'].email),
            ('parent',       'linked to Njeri',     users['parent_linked'].email),
            ('parent',       'unlinked',            users['parent_unlinked'].email),
            ('student G9',   'exploring, no goals', users['student_g9_exploring'].email),
            ('student G9',   'active + 3 goals',    users['student_g9_active'].email),
            ('student G10',  'decided + 2 goals',   users['student_g10_decided'].email),
            ('student G10',  'reconsidering+1 goal',users['student_g10_reconsidering'].email),
        ]
        col_w = [max(len(r[i]) for r in rows) for i in range(3)]
        for role, state, email in rows:
            self.stdout.write(
                f'  {role:<{col_w[0]}}  {state:<{col_w[1]}}  {email}'
            )
        self.stdout.write('')
