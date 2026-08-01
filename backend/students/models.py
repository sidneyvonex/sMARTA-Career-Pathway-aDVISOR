from decimal import Decimal
import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from accounts.models import StudentProfile

GRADE_LEVEL_CHOICES = [
    ('EE1', 'Exceeding Expectation - Level 1'),
    ('EE2', 'Exceeding Expectation - Level 2'),
    ('ME1', 'Meeting Expectation - Level 1'),
    ('ME2', 'Meeting Expectation - Level 2'),
    ('AE1', 'Approaching Expectation - Level 1'),
    ('AE2', 'Approaching Expectation - Level 2'),
    ('BE1', 'Below Expectation - Level 1'),
    ('BE2', 'Below Expectation - Level 2'),
]

GRADE_LEVEL_POINTS = {
    'EE1': 8,
    'EE2': 7,
    'ME1': 6,
    'ME2': 5,
    'AE1': 4,
    'AE2': 3,
    'BE1': 2,
    'BE2': 1,
}


GRADE_SUFFIX = re.compile(r'(?:9|10|11|12)$')


class AssessmentFramework(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_RETIRED = 'retired'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_RETIRED, 'Retired'),
    ]

    code = models.CharField(max_length=80)
    version = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    scope = models.CharField(max_length=40)
    source_url = models.URLField(max_length=500)
    effective_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scope', '-effective_date', 'code', 'version']
        constraints = [
            models.UniqueConstraint(
                fields=['code', 'version'],
                name='students_framework_code_version_uniq',
            ),
            models.UniqueConstraint(
                fields=['scope'],
                condition=models.Q(status='active'),
                name='students_active_framework_scope_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.code} {self.version} — {self.title}'


class PerformanceLevelDefinition(models.Model):
    framework = models.ForeignKey(
        AssessmentFramework,
        on_delete=models.CASCADE,
        related_name='level_definitions',
    )
    code = models.CharField(max_length=10)
    label = models.CharField(max_length=120)
    description = models.TextField()
    rank = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    official_min_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    official_max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    official_points = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-rank', 'code']
        constraints = [
            models.UniqueConstraint(
                fields=['framework', 'code'],
                name='students_level_framework_code_uniq',
            ),
            models.UniqueConstraint(
                fields=['framework', 'rank'],
                name='students_level_framework_rank_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.framework.code} {self.framework.version} — {self.code}'


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    continuity_code = models.CharField(max_length=80)
    grade = models.IntegerField(
        choices=[
            (9, 'Grade 9'),
            (10, 'Grade 10'),
            (11, 'Grade 11'),
            (12, 'Grade 12'),
        ],
        validators=[MinValueValidator(9), MaxValueValidator(12)],
    )
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_selectable_in_combination = models.BooleanField(default=False)

    class Meta:
        ordering = ['grade', 'category', 'name']

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.continuity_code:
            self.continuity_code = GRADE_SUFFIX.sub('', self.code)
        return super().save(*args, **kwargs)


class StudentSubject(models.Model):
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='enrolled_subjects'
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='enrollments')
    continuity_code = models.CharField(max_length=80)
    academic_grade = models.IntegerField(
        choices=[
            (9, 'Grade 9'),
            (10, 'Grade 10'),
            (11, 'Grade 11'),
            (12, 'Grade 12'),
        ],
        validators=[MinValueValidator(9), MaxValueValidator(12)],
    )
    academic_year = models.PositiveSmallIntegerField()
    active_identity = models.CharField(
        max_length=96,
        null=True,
        blank=True,
        editable=False,
    )
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'student_profile',
                    'active_identity',
                ],
                name='students_active_identity_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(is_active=True, ended_at__isnull=True)
                    | models.Q(is_active=False, ended_at__isnull=False)
                ),
                name='students_enrollment_state_ck',
            ),
        ]

    def __str__(self):
        return f"{self.student_profile} — {self.subject.code}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.continuity_code = self.subject.continuity_code
            self.academic_grade = self.subject.grade
            if self.academic_year is None:
                self.academic_year = timezone.now().year
        else:
            original = (
                type(self).objects.filter(pk=self.pk)
                .values_list(
                    'subject_id',
                    'continuity_code',
                    'academic_grade',
                )
                .first()
            )
            if original is not None and original != (
                self.subject_id,
                self.continuity_code,
                self.academic_grade,
            ):
                raise ValidationError(
                    'Enrollment subject identity snapshots are immutable.'
                )
        self.active_identity = (
            f'{self.continuity_code}:{self.academic_grade}'
            if self.is_active
            else None
        )
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {
                'active_identity'
            }
        return super().save(*args, **kwargs)

    def archive(self):
        if not self.is_active:
            return
        self.is_active = False
        self.ended_at = timezone.now()
        self.save(update_fields=['is_active', 'ended_at', 'active_identity'])

    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        self.ended_at = None
        self.save(update_fields=['is_active', 'ended_at', 'active_identity'])


class CBCGrade(models.Model):
    TERM_CHOICES = [(1, 'Term 1'), (2, 'Term 2'), (3, 'Term 3')]
    SOURCE_CHOICES = [('learner', 'Learner'), ('school', 'School')]

    student_subject = models.ForeignKey(
        StudentSubject, on_delete=models.PROTECT, related_name='grades'
    )
    framework = models.ForeignKey(
        AssessmentFramework,
        on_delete=models.PROTECT,
        related_name='grades',
    )
    academic_grade = models.IntegerField(
        choices=[
            (9, 'Grade 9'),
            (10, 'Grade 10'),
            (11, 'Grade 11'),
            (12, 'Grade 12'),
        ],
        validators=[MinValueValidator(9), MaxValueValidator(12)],
    )
    term = models.IntegerField(choices=TERM_CHOICES)
    year = models.IntegerField()
    level = models.CharField(max_length=10, choices=GRADE_LEVEL_CHOICES)
    raw_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
    )
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='learner',
    )
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_cbc_grades',
    )
    verified_school = models.ForeignKey(
        'accounts.School',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='verified_cbc_grades',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student_subject', 'term', 'year')
        ordering = ['year', 'term']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(verified_by__isnull=True, verified_at__isnull=True)
                    | models.Q(
                        verified_by__isnull=False,
                        verified_at__isnull=False,
                    )
                ),
                name='students_grade_verification_pair',
            ),
        ]

    def __str__(self):
        return f"{self.student_subject} — T{self.term} {self.year}: {self.level}"

    def clean(self):
        super().clean()
        if self.student_subject_id is None or self.academic_grade is None:
            return

        enrollment_grade = self.student_subject.academic_grade
        if self.academic_grade != enrollment_grade:
            raise ValidationError(
                {
                    'academic_grade': (
                        'Academic grade must match the enrollment subject grade.'
                    )
                }
            )

        framework_scope = (
            'junior_school' if self.academic_grade == 9 else 'senior_school'
        )
        if self.framework_id is not None and self.framework.scope != framework_scope:
            raise ValidationError(
                {
                    'framework': (
                        'Assessment framework scope must match the academic grade.'
                    )
                }
            )

        original = None
        if not self._state.adding:
            original = (
                type(self).objects.filter(pk=self.pk)
                .values_list(
                    'verified_by_id',
                    'verified_at',
                    'verified_school_id',
                )
                .first()
            )
            if (
                original is not None
                and original[2] is not None
                and original[2] != self.verified_school_id
            ):
                raise ValidationError(
                    {'verified_school': 'Verifying school provenance is immutable.'}
                )

            is_unchanged_legacy_verification = (
                original is not None
                and original[0] is not None
                and original[1] is not None
                and original[2] is None
                and self.verified_by_id == original[0]
                and self.verified_at == original[1]
                and self.verified_school_id is None
            )
            if is_unchanged_legacy_verification:
                return
        has_verifier = self.verified_by_id is not None
        has_verified_at = self.verified_at is not None
        has_verified_school = self.verified_school_id is not None
        if has_verifier != has_verified_at:
            raise ValidationError(
                {
                    'verified_by': (
                        'Verification actor and timestamp must be recorded together.'
                    )
                }
            )
        if has_verifier:
            if not has_verified_school:
                raise ValidationError(
                    {
                        'verified_school': (
                            'Verified evidence must record the verifying school.'
                        )
                    }
                )
            if self.verified_by.school_id != self.verified_school_id:
                raise ValidationError(
                    {
                        'verified_school': (
                            'Verifying school must match the verifier account.'
                        )
                    }
                )
        elif self._state.adding and has_verified_school:
            raise ValidationError(
                {
                    'verified_school': (
                        'Verifying school requires a verification actor and timestamp.'
                    )
                }
            )
    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.academic_grade is None:
                self.academic_grade = self.student_subject.academic_grade
            if self.framework_id is None:
                framework_scope = (
                    'junior_school'
                    if self.academic_grade == 9
                    else 'senior_school'
                )
                try:
                    self.framework = AssessmentFramework.objects.get(
                        scope=framework_scope,
                        status=AssessmentFramework.STATUS_ACTIVE,
                    )
                except AssessmentFramework.DoesNotExist as exc:
                    raise ValidationError(
                        {
                            'framework': (
                                f'No active {framework_scope.replace("_", " ").title()} '
                                'assessment framework is configured.'
                            )
                        }
                    ) from exc
                except AssessmentFramework.MultipleObjectsReturned as exc:
                    raise ValidationError(
                        {
                            'framework': (
                                f'Multiple active {framework_scope.replace("_", " ").title()} '
                                'assessment frameworks are configured.'
                            )
                        }
                    ) from exc
        self.clean()
        return super().save(*args, **kwargs)


class AcademicGoal(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_ACHIEVED = 'achieved'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ACHIEVED, 'Achieved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    learner = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='academic_goals',
    )
    continuity_code = models.CharField(max_length=80)
    active_identity = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        editable=False,
    )
    current_evidence = models.ForeignKey(
        CBCGrade,
        on_delete=models.PROTECT,
        related_name='goals_created_from_evidence',
    )
    current_level_definition = models.ForeignKey(
        PerformanceLevelDefinition,
        on_delete=models.PROTECT,
        related_name='goals_with_current_level',
    )
    target_level_definition = models.ForeignKey(
        PerformanceLevelDefinition,
        on_delete=models.PROTECT,
        related_name='goals_with_target_level',
    )
    current_level_code = models.CharField(max_length=10, editable=False)
    current_level_rank = models.PositiveSmallIntegerField(editable=False)
    current_framework_code = models.CharField(max_length=80, editable=False)
    current_framework_version = models.CharField(max_length=40, editable=False)
    target_level_code = models.CharField(max_length=10, editable=False)
    target_level_rank = models.PositiveSmallIntegerField(editable=False)
    target_framework_code = models.CharField(max_length=80, editable=False)
    target_framework_version = models.CharField(max_length=40, editable=False)
    target_term = models.PositiveSmallIntegerField(choices=CBCGrade.TERM_CHOICES)
    target_year = models.PositiveSmallIntegerField()
    target_academic_grade = models.PositiveSmallIntegerField(
        choices=[
            (9, 'Grade 9'),
            (10, 'Grade 10'),
            (11, 'Grade 11'),
            (12, 'Grade 12'),
        ],
        validators=[MinValueValidator(9), MaxValueValidator(12)],
    )
    action_plan = models.TextField(max_length=2000)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='academic_goals_created',
    )
    achieved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['learner', 'active_identity'],
                name='students_active_goal_identity_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(status='active', active_identity__isnull=False)
                    | models.Q(
                        status__in=['achieved', 'closed'],
                        active_identity__isnull=True,
                    )
                ),
                name='students_goal_status_identity_ck',
            ),
        ]

    @staticmethod
    def _evidence_order(evidence):
        return (
            evidence.academic_grade,
            evidence.year,
            evidence.term,
            evidence.created_at,
            evidence.pk,
        )

    def clean(self):
        super().clean()
        if not all((
            self.learner_id,
            self.current_evidence_id,
            self.current_level_definition_id,
            self.target_level_definition_id,
        )):
            return
        evidence = self.current_evidence
        if evidence.student_subject.student_profile_id != self.learner_id:
            raise ValidationError(
                {'current_evidence': 'Current evidence must belong to the learner.'}
            )
        if evidence.student_subject.continuity_code != self.continuity_code:
            raise ValidationError(
                {'continuity_code': 'Current evidence must match the goal subject.'}
            )
        current_level = self.current_level_definition
        target_level = self.target_level_definition
        if (
            current_level.framework_id != evidence.framework_id
            or current_level.code != evidence.level
        ):
            raise ValidationError(
                {'current_level_definition': 'Current level must match the evidence snapshot.'}
            )
        if target_level.framework_id != current_level.framework_id:
            raise ValidationError(
                {'target_level_definition': 'Target level must use the current assessment framework.'}
            )
        if target_level.rank < current_level.rank:
            raise ValidationError(
                {'target_level_definition': 'Target level cannot be lower than the current level.'}
            )
        target_period = (
            self.target_academic_grade,
            self.target_year,
            self.target_term,
        )
        current_period = (evidence.academic_grade, evidence.year, evidence.term)
        if target_period <= current_period:
            raise ValidationError(
                {'target_term': 'Target period must be later than the current evidence period.'}
            )
        if self.created_by_id != self.learner.user_id:
            raise ValidationError(
                {'created_by': 'Academic goals must be created by the learner.'}
            )

        if not self._state.adding:
            original = type(self).objects.filter(pk=self.pk).values(
                'learner_id',
                'continuity_code',
                'current_evidence_id',
                'current_level_definition_id',
                'current_level_code',
                'current_level_rank',
                'current_framework_code',
                'current_framework_version',
                'created_by_id',
            ).first()
            current_snapshot = {
                'learner_id': self.learner_id,
                'continuity_code': self.continuity_code,
                'current_evidence_id': self.current_evidence_id,
                'current_level_definition_id': self.current_level_definition_id,
                'current_level_code': self.current_level_code,
                'current_level_rank': self.current_level_rank,
                'current_framework_code': self.current_framework_code,
                'current_framework_version': self.current_framework_version,
                'created_by_id': self.created_by_id,
            }
            if original is not None and original != current_snapshot:
                raise ValidationError('Academic goal creation snapshots are immutable.')

    def save(self, *args, **kwargs):
        if self._state.adding:
            current = self.current_level_definition
            self.current_level_code = current.code
            self.current_level_rank = current.rank
            self.current_framework_code = current.framework.code
            self.current_framework_version = current.framework.version
        target = self.target_level_definition
        self.target_level_code = target.code
        self.target_level_rank = target.rank
        self.target_framework_code = target.framework.code
        self.target_framework_version = target.framework.version
        self.active_identity = (
            self.continuity_code if self.status == self.STATUS_ACTIVE else None
        )
        self.clean()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {
                'active_identity',
                'target_level_code',
                'target_level_rank',
                'target_framework_code',
                'target_framework_version',
            }
        return super().save(*args, **kwargs)

    def close(self):
        if self.status != self.STATUS_ACTIVE:
            return
        self.status = self.STATUS_CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])

    def mark_achieved(self):
        if self.status != self.STATUS_ACTIVE:
            return
        self.status = self.STATUS_ACHIEVED
        self.achieved_at = timezone.now()
        self.save(update_fields=['status', 'achieved_at'])

    def readiness_evidence(self):
        if self.status != self.STATUS_ACTIVE:
            return None
        current_order = self._evidence_order(self.current_evidence)
        later = [
            evidence
            for evidence in CBCGrade.objects.filter(
                student_subject__student_profile=self.learner,
                student_subject__continuity_code=self.continuity_code,
                framework=self.current_level_definition.framework,
            ).select_related('student_subject', 'framework').order_by(
                'academic_grade', 'year', 'term', 'created_at', 'pk'
            )
            if self._evidence_order(evidence) > current_order
        ]
        if not later:
            return None
        latest = later[-1]
        level = PerformanceLevelDefinition.objects.filter(
            framework=latest.framework,
            code=latest.level,
        ).first()
        if level is None or level.rank < self.target_level_rank:
            return None
        return latest

    def __str__(self):
        return f'{self.learner} — {self.continuity_code}: {self.status}'
