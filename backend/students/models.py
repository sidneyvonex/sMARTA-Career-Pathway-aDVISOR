from decimal import Decimal
import re

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
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
_ACADEMIC_GOAL_LIFECYCLE_TRANSITION = object()
_CBC_GRADE_VERIFICATION_TRANSITION = object()


class AcademicGoalHistoryDeletionError(ValidationError):
    """Raised when application code attempts to erase a goal audit row."""

    def __init__(self):
        super().__init__(
            'Academic goal history cannot be deleted; close an active goal instead.'
        )


def set_academic_goal_evidence_null(collector, field, sub_objs, using):
    """Preserve SET_NULL semantics without exposing a public queryset bypass."""
    collector.add_field_update(field, None, list(sub_objs))


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
        return f"{self.code} {self.version} — {self.title}"

    def validate_activation_readiness(self):
        expected = GRADE_LEVEL_POINTS
        actual = dict(self.level_definitions.values_list('code', 'rank'))
        if actual != expected:
            raise ValidationError(
                'Assessment framework activation requires the complete '
                'EE1–BE2 definition set with ranks 8–1.'
            )


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
        return f"{self.framework.code} {self.framework.version} — {self.code}"


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
    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name='enrollments'
    )
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
                type(self)
                .objects.filter(pk=self.pk)
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
            f"{self.continuity_code}:{self.academic_grade}" if self.is_active else None
        )
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'active_identity'}
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


class CBCGradeQuerySet(models.QuerySet):
    PROTECTED_EVIDENCE_FIELDS = frozenset({
        'student_subject',
        'student_subject_id',
        'framework',
        'framework_id',
        'academic_grade',
        'term',
        'year',
        'level',
        'level_definition_id_snapshot',
        'raw_score',
        'source',
        'verified_by',
        'verified_by_id',
        'verified_school',
        'verified_school_id',
        'verified_at',
    })

    @staticmethod
    def _bulk_persistence_error():
        return ValidationError(
            'CBC grade bulk persistence cannot modify evidence identity fields.'
        )

    def update(self, **kwargs):
        if set(kwargs) & self.PROTECTED_EVIDENCE_FIELDS:
            raise self._bulk_persistence_error()
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if set(fields) & self.PROTECTED_EVIDENCE_FIELDS:
            raise self._bulk_persistence_error()
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, **kwargs):
        raise self._bulk_persistence_error()

    def delete(self):
        if self.filter(
            models.Q(verified_by__isnull=False)
            | models.Q(verified_at__isnull=False)
            | models.Q(verified_school__isnull=False)
        ).exists():
            raise ValidationError('School-verified evidence cannot be deleted.')
        raise ValidationError(
            'CBC grade bulk deletion is disabled; delete individual unverified '
            'evidence through the guarded learner endpoint.'
        )


class CBCGradeManager(models.Manager.from_queryset(CBCGradeQuerySet)):
    pass


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
    level_definition_id_snapshot = models.PositiveBigIntegerField(
        null=True,
        editable=False,
    )
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

    objects = CBCGradeManager()

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
                type(self)
                .objects.filter(pk=self.pk)
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
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields = set(update_fields)
            kwargs['update_fields'] = update_fields

        original_persistence = None
        if not self._state.adding:
            original_persistence = type(self).objects.filter(pk=self.pk).values(
                'student_subject_id',
                'academic_grade',
                'framework_id',
                'term',
                'year',
                'level',
                'level_definition_id_snapshot',
                'raw_score',
                'source',
                'verified_by_id',
                'verified_at',
                'verified_school_id',
            ).first()

        if original_persistence is not None:
            verification_fields = {
                'verified_by_id': (
                    {'verified_by', 'verified_by_id'},
                    self.verified_by_id,
                ),
                'verified_at': ({'verified_at'}, self.verified_at),
                'verified_school_id': (
                    {'verified_school', 'verified_school_id'},
                    self.verified_school_id,
                ),
            }
            persisted_verification = {
                field: (
                    current
                    if update_fields is None or update_fields & aliases
                    else original_persistence[field]
                )
                for field, (aliases, current) in verification_fields.items()
            }
            verification_changed = any(
                original_persistence[field] != value
                for field, value in persisted_verification.items()
            )
            if verification_changed and getattr(
                self,
                '_verification_transition_token',
                None,
            ) is not _CBC_GRADE_VERIFICATION_TRANSITION:
                raise ValidationError(
                    'Grade verification changes must use the evidence transition service.'
                )

            has_verification_provenance = any(
                original_persistence[field] is not None
                for field in (
                    'verified_by_id',
                    'verified_at',
                    'verified_school_id',
                )
            )
            if has_verification_provenance:
                protected_fields = {
                    'student_subject_id': (
                        {'student_subject', 'student_subject_id'},
                        self.student_subject_id,
                    ),
                    'academic_grade': ({'academic_grade'}, self.academic_grade),
                    'framework_id': ({'framework', 'framework_id'}, self.framework_id),
                    'term': ({'term'}, self.term),
                    'year': ({'year'}, self.year),
                    'level': ({'level'}, self.level),
                    'level_definition_id_snapshot': (
                        {'level_definition_id_snapshot'},
                        self.level_definition_id_snapshot,
                    ),
                    'raw_score': ({'raw_score'}, self.raw_score),
                    'source': ({'source'}, self.source),
                }
                persisted_evidence = {
                    field: (
                        current
                        if update_fields is None or update_fields & aliases
                        else original_persistence[field]
                    )
                    for field, (aliases, current) in protected_fields.items()
                }
                if any(
                    original_persistence[field] != value
                    for field, value in persisted_evidence.items()
                ):
                    raise ValidationError(
                        'School-verified evidence cannot be edited.'
                    )

        if self._state.adding:
            if self.academic_grade is None:
                self.academic_grade = self.student_subject.academic_grade
            if self.framework_id is None:
                framework_scope = (
                    'junior_school' if self.academic_grade == 9 else 'senior_school'
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
                                f'No active {framework_scope.replace('_', ' ').title()} '
                                'assessment framework is configured.'
                            )
                        }
                    ) from exc
                except AssessmentFramework.MultipleObjectsReturned as exc:
                    raise ValidationError(
                        {
                            'framework': (
                                f'Multiple active {framework_scope.replace('_', ' ').title()} '
                                'assessment frameworks are configured.'
                            )
                        }
                    ) from exc

        persisted_update_fields = update_fields
        original_identity = None
        definition_identity_changed = self._state.adding
        definition_framework_id = self.framework_id
        definition_level = self.level
        if not self._state.adding:
            original_identity = original_persistence
            if original_identity is None:
                definition_identity_changed = True
            else:
                persisted_identity = {
                    'student_subject_id': self.student_subject_id,
                    'academic_grade': self.academic_grade,
                    'framework_id': self.framework_id,
                    'level': self.level,
                }
                if persisted_update_fields is not None:
                    field_aliases = {
                        'student_subject_id': {
                            'student_subject',
                            'student_subject_id',
                        },
                        'academic_grade': {'academic_grade'},
                        'framework_id': {'framework', 'framework_id'},
                        'level': {'level'},
                    }
                    persisted_identity = {
                        field: (
                            value
                            if persisted_update_fields & field_aliases[field]
                            else original_identity[field]
                        )
                        for field, value in persisted_identity.items()
                    }
                definition_identity_changed = any(
                    original_identity[field] != value
                    for field, value in persisted_identity.items()
                )
                definition_framework_id = persisted_identity['framework_id']
                definition_level = persisted_identity['level']
                original_snapshot = original_identity[
                    'level_definition_id_snapshot'
                ]
                if (
                    not definition_identity_changed
                    and original_snapshot is not None
                    and self.level_definition_id_snapshot != original_snapshot
                ):
                    raise ValidationError(
                        {
                            'level_definition_id_snapshot': (
                                'The grade definition snapshot is immutable while '
                                'the evidence identity is unchanged.'
                            )
                        }
                    )
                if original_snapshot is None:
                    definition_identity_changed = True

        if definition_identity_changed and definition_framework_id is not None:
            try:
                self.level_definition_id_snapshot = (
                    PerformanceLevelDefinition.objects.only('pk').get(
                        framework_id=definition_framework_id,
                        code=definition_level,
                    ).pk
                )
            except PerformanceLevelDefinition.DoesNotExist:
                raise ValidationError(
                    {
                        'level': (
                            'The selected framework has no matching performance '
                            'level definition.'
                        )
                    }
                )
        self.clean()
        if update_fields is not None and definition_identity_changed:
            update_fields.add('level_definition_id_snapshot')
        return super().save(*args, **kwargs)

    def _persist_verification_transition(self, *, update_fields):
        self._verification_transition_token = _CBC_GRADE_VERIFICATION_TRANSITION
        try:
            self.save(update_fields=update_fields)
        finally:
            del self._verification_transition_token

    def delete(self, *args, **kwargs):
        if any((self.verified_by_id, self.verified_at, self.verified_school_id)):
            raise ValidationError('School-verified evidence cannot be deleted.')
        return super().delete(*args, **kwargs)


class AcademicGoalQuerySet(models.QuerySet):
    SAFE_UPDATE_FIELDS = frozenset({'action_plan', 'updated_at'})

    @staticmethod
    def _bulk_persistence_error():
        return ValidationError(
            'Academic goal bulk persistence cannot modify protected fields.'
        )

    def update(self, **kwargs):
        if set(kwargs) - self.SAFE_UPDATE_FIELDS:
            raise self._bulk_persistence_error()
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        raise self._bulk_persistence_error()

    def bulk_create(self, objs, **kwargs):
        raise self._bulk_persistence_error()

    def delete(self):
        raise AcademicGoalHistoryDeletionError()


class AcademicGoalManager(models.Manager.from_queryset(AcademicGoalQuerySet)):
    pass


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
        on_delete=set_academic_goal_evidence_null,
        null=True,
        blank=True,
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
    target_framework_id_snapshot = models.PositiveBigIntegerField(editable=False)
    creation_evidence_snapshot = models.JSONField(default=dict, editable=False)
    achievement_evidence_snapshot = models.JSONField(
        null=True,
        blank=True,
        editable=False,
    )
    legacy_lifecycle_unverifiable = models.BooleanField(
        default=False,
        editable=False,
    )
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
    confirmed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name='academic_goals_confirmed',
    )
    achieved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AcademicGoalManager()

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['learner', 'active_identity'],
                name='students_active_goal_identity_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(
                        status='active',
                        legacy_lifecycle_unverifiable=False,
                        active_identity__isnull=False,
                        achieved_at__isnull=True,
                        closed_at__isnull=True,
                        confirmed_by__isnull=True,
                        achievement_evidence_snapshot__isnull=True,
                    )
                    | models.Q(
                        status='achieved',
                        legacy_lifecycle_unverifiable=False,
                        active_identity__isnull=True,
                        achieved_at__isnull=False,
                        closed_at__isnull=True,
                        confirmed_by__isnull=False,
                        confirmed_by=models.F('created_by'),
                        achievement_evidence_snapshot__isnull=False,
                    )
                    | models.Q(
                        status='closed',
                        legacy_lifecycle_unverifiable=False,
                        active_identity__isnull=True,
                        achieved_at__isnull=True,
                        closed_at__isnull=False,
                        confirmed_by__isnull=True,
                        achievement_evidence_snapshot__isnull=True,
                    )
                    | (
                        models.Q(
                            legacy_lifecycle_unverifiable=True,
                            confirmed_by__isnull=True,
                            achievement_evidence_snapshot__isnull=True,
                        )
                        & (
                            models.Q(
                                status='active',
                                active_identity__isnull=False,
                            )
                            | models.Q(
                                status__in=['achieved', 'closed'],
                                active_identity__isnull=True,
                            )
                        )
                    )
                ),
                name='students_goal_lifecycle_coherence_ck',
            ),
        ]

    @staticmethod
    def _evidence_order(evidence):
        return (
            evidence.academic_grade,
            evidence.year,
            evidence.term,
            evidence.created_at.isoformat(),
            evidence.pk,
        )

    @staticmethod
    def _snapshot_order(snapshot):
        period = snapshot['period']
        return (
            period['academic_grade'],
            period['year'],
            period['term'],
            snapshot['recorded_at'],
            snapshot['evidence_id'],
        )

    @staticmethod
    def _isoformat(value):
        return value.isoformat() if value is not None else None

    @classmethod
    def evidence_snapshot(
        cls,
        evidence,
        *,
        level_definitions=None,
        level_definition_id=None,
    ):
        if level_definitions is None:
            level_definitions = {
                str(definition_id): {'code': code, 'rank': rank}
                for definition_id, code, rank in (
                    PerformanceLevelDefinition.objects.filter(
                        framework_id=evidence.framework_id,
                    ).values_list('pk', 'code', 'rank')
                )
            }
        if level_definition_id is None:
            level_definition_id = evidence.level_definition_id_snapshot
            if level_definition_id is None:
                level_definition_id = next(
                    (
                        int(definition_id)
                        for definition_id, definition in level_definitions.items()
                        if definition['code'] == evidence.level
                    ),
                    None,
                )
        definition = level_definitions.get(str(level_definition_id))
        if definition is None:
            raise ValidationError(
                {'current_evidence': 'The assessment framework is incomplete.'}
            )
        level_ranks = {
            item['code']: item['rank'] for item in level_definitions.values()
        }
        return {
            'evidence_id': evidence.pk,
            'period': {
                'academic_grade': evidence.academic_grade,
                'year': evidence.year,
                'term': evidence.term,
            },
            'level': {
                'code': evidence.level,
                'rank': definition['rank'],
                'definition_id': level_definition_id,
            },
            'framework': {
                'id': evidence.framework_id,
                'code': evidence.framework.code,
                'version': evidence.framework.version,
                'level_ranks': level_ranks,
                'level_definitions': level_definitions,
            },
            'source': evidence.source,
            'verification': {
                'confidence': (
                    'school_verified'
                    if evidence.verified_at is not None
                    else 'learner_entered'
                ),
                'verified_by': evidence.verified_by_id,
                'verified_school': evidence.verified_school_id,
                'verified_at': cls._isoformat(evidence.verified_at),
            },
            'recorded_at': cls._isoformat(evidence.created_at),
        }

    def _validate_lifecycle_coherence(self):
        active = self.status == self.STATUS_ACTIVE
        achieved = self.status == self.STATUS_ACHIEVED
        closed = self.status == self.STATUS_CLOSED
        valid = (
            (
                active
                and not self.legacy_lifecycle_unverifiable
                and self.active_identity is not None
                and self.achieved_at is None
                and self.closed_at is None
                and self.confirmed_by_id is None
                and self.achievement_evidence_snapshot is None
            )
            or (
                achieved
                and not self.legacy_lifecycle_unverifiable
                and self.active_identity is None
                and self.achieved_at is not None
                and self.closed_at is None
                and self.confirmed_by_id is not None
                and self.confirmed_by_id == self.learner.user_id
                and self.achievement_evidence_snapshot is not None
            )
            or (
                closed
                and not self.legacy_lifecycle_unverifiable
                and self.active_identity is None
                and self.achieved_at is None
                and self.closed_at is not None
                and self.confirmed_by_id is None
                and self.achievement_evidence_snapshot is None
            )
            or (
                self.legacy_lifecycle_unverifiable
                and self.confirmed_by_id is None
                and self.achievement_evidence_snapshot is None
                and (
                    (active and self.active_identity is not None)
                    or ((achieved or closed) and self.active_identity is None)
                )
            )
        )
        if not valid:
            raise ValidationError('Academic goal lifecycle fields are incoherent.')

    def clean(self):
        super().clean()
        if self._state.adding and self.legacy_lifecycle_unverifiable:
            raise ValidationError('The legacy lifecycle exemption is migration-only.')
        self._validate_lifecycle_coherence()
        if not all(
            (
                self.learner_id,
                self.current_level_definition_id,
                self.target_level_definition_id,
                self.creation_evidence_snapshot,
            )
        ):
            return
        snapshot = self.creation_evidence_snapshot
        if self._state.adding:
            evidence = self.current_evidence
            if evidence is None:
                raise ValidationError(
                    {'current_evidence': 'Current evidence is required.'}
                )
            if evidence.student_subject.student_profile_id != self.learner_id:
                raise ValidationError(
                    {'current_evidence': 'Current evidence must belong to the learner.'}
                )
            if evidence.student_subject.continuity_code != self.continuity_code:
                raise ValidationError(
                    {'continuity_code': 'Current evidence must match the goal subject.'}
                )
            current_level = self.current_level_definition
            current_definition_matches = (
                current_level.framework_id == evidence.framework_id
                and (
                    current_level.pk == evidence.level_definition_id_snapshot
                    if evidence.level_definition_id_snapshot is not None
                    else current_level.code == evidence.level
                )
            )
            if not current_definition_matches:
                raise ValidationError(
                    {
                        'current_level_definition': 'Current level must match the evidence snapshot.'
                    }
                )

        target_level = self.target_level_definition
        target_framework = snapshot['framework']
        if target_level.framework_id != target_framework['id']:
            raise ValidationError(
                {
                    'target_level_definition': 'Target level must use the current assessment framework.'
                }
            )
        if self.target_level_rank < snapshot['level']['rank']:
            raise ValidationError(
                {
                    'target_level_definition': 'Target level cannot be lower than the current level.'
                }
            )
        target_period = (
            self.target_academic_grade,
            self.target_year,
            self.target_term,
        )
        current_period = (
            snapshot['period']['academic_grade'],
            snapshot['period']['year'],
            snapshot['period']['term'],
        )
        if target_period <= current_period:
            raise ValidationError(
                {
                    'target_term': 'Target period must be later than the current evidence period.'
                }
            )
        if self.created_by_id != self.learner.user_id:
            raise ValidationError(
                {'created_by': 'Academic goals must be created by the learner.'}
            )

        if not self._state.adding:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    'learner_id',
                    'continuity_code',
                    'current_evidence_id',
                    'current_level_definition_id',
                    'current_level_code',
                    'current_level_rank',
                    'current_framework_code',
                    'current_framework_version',
                    'creation_evidence_snapshot',
                    'legacy_lifecycle_unverifiable',
                    'created_by_id',
                )
                .first()
            )
            current_snapshot = {
                'learner_id': self.learner_id,
                'continuity_code': self.continuity_code,
                'current_evidence_id': self.current_evidence_id,
                'current_level_definition_id': self.current_level_definition_id,
                'current_level_code': self.current_level_code,
                'current_level_rank': self.current_level_rank,
                'current_framework_code': self.current_framework_code,
                'current_framework_version': self.current_framework_version,
                'creation_evidence_snapshot': self.creation_evidence_snapshot,
                'legacy_lifecycle_unverifiable': self.legacy_lifecycle_unverifiable,
                'created_by_id': self.created_by_id,
            }
            if original is not None and original != current_snapshot:
                raise ValidationError('Academic goal creation snapshots are immutable.')

    def save(self, *args, **kwargs):
        original = None
        if not self._state.adding:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    'status',
                    'target_level_definition_id',
                    'target_level_code',
                    'target_level_rank',
                    'target_framework_code',
                    'target_framework_version',
                    'target_framework_id_snapshot',
                    'achieved_at',
                    'closed_at',
                    'confirmed_by_id',
                    'achievement_evidence_snapshot',
                    'legacy_lifecycle_unverifiable',
                )
                .first()
            )
            if original is not None and original['status'] != self.status:
                transition_token = getattr(
                    self,
                    '_lifecycle_transition_token',
                    None,
                )
                if (
                    transition_token is not _ACADEMIC_GOAL_LIFECYCLE_TRANSITION
                    or original['status'] != self.STATUS_ACTIVE
                ):
                    raise ValidationError(
                        'Only an active academic goal can use this lifecycle transition.'
                    )
            if original is not None and original['status'] == self.status:
                lifecycle_record = {
                    'achieved_at': self.achieved_at,
                    'closed_at': self.closed_at,
                    'confirmed_by_id': self.confirmed_by_id,
                    'achievement_evidence_snapshot': self.achievement_evidence_snapshot,
                    'legacy_lifecycle_unverifiable': (
                        self.legacy_lifecycle_unverifiable
                    ),
                }
                if any(
                    original[field] != value
                    for field, value in lifecycle_record.items()
                ):
                    raise ValidationError(
                        'Academic goal lifecycle records are immutable.'
                    )
                if original[
                    'target_level_definition_id'
                ] == self.target_level_definition_id and any(
                    (
                        original['target_level_code'] != self.target_level_code,
                        original['target_level_rank'] != self.target_level_rank,
                        original['target_framework_code'] != self.target_framework_code,
                        original['target_framework_version']
                        != self.target_framework_version,
                        original['target_framework_id_snapshot']
                        != self.target_framework_id_snapshot,
                    )
                ):
                    raise ValidationError(
                        'Academic goal target snapshots are immutable.'
                    )
        if self._state.adding:
            current = self.current_level_definition
            self.current_level_code = self.current_evidence.level
            self.current_level_rank = current.rank
            self.current_framework_code = current.framework.code
            self.current_framework_version = current.framework.version
            self.creation_evidence_snapshot = self.evidence_snapshot(
                self.current_evidence
            )
        target_changed = (
            self._state.adding
            or original is None
            or original['target_level_definition_id'] != self.target_level_definition_id
        )
        if target_changed:
            target = self.target_level_definition
            self.target_level_code = target.code
            self.target_level_rank = target.rank
            self.target_framework_code = target.framework.code
            self.target_framework_version = target.framework.version
            self.target_framework_id_snapshot = target.framework_id
        self.active_identity = (
            self.continuity_code if self.status == self.STATUS_ACTIVE else None
        )
        self.clean()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {
                'active_identity',
            }
            if target_changed:
                kwargs['update_fields'] |= {
                    'target_level_code',
                    'target_level_rank',
                    'target_framework_code',
                    'target_framework_version',
                    'target_framework_id_snapshot',
                }
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AcademicGoalHistoryDeletionError()

    def _validate_actor(self, actor):
        if actor is None or actor.pk != self.learner.user_id:
            raise ValidationError('Only the learner can transition an academic goal.')

    def _close_locked(self, *, actor):
        self._validate_actor(actor)
        if self.status != self.STATUS_ACTIVE:
            raise ValidationError('Only an active academic goal can be closed.')
        self._lifecycle_transition_token = _ACADEMIC_GOAL_LIFECYCLE_TRANSITION
        self.status = self.STATUS_CLOSED
        self.achieved_at = None
        self.closed_at = timezone.now()
        self.confirmed_by = None
        self.achievement_evidence_snapshot = None
        self.save(
            update_fields=[
                'status',
                'achieved_at',
                'closed_at',
                'confirmed_by',
                'achievement_evidence_snapshot',
            ]
        )
        return self

    @classmethod
    def close_goal(cls, *, goal_id, actor):
        """Close after reloading the goal under its transaction-owned row lock."""
        with transaction.atomic():
            goal = (
                cls.objects.select_for_update()
                .select_related('learner')
                .get(pk=goal_id, learner__user=actor)
            )
            return goal._close_locked(actor=actor)

    def close(self, *, actor=None):
        """Public transition delegates to the transaction-safe close service."""
        self._validate_actor(actor)
        if self.pk is None:
            raise ValidationError('An academic goal must be saved before closing.')
        transitioned = type(self).close_goal(goal_id=self.pk, actor=actor)
        self.__dict__.update(transitioned.__dict__)
        return self

    def _mark_achieved_locked(
        self,
        *,
        actor,
        evidence_pool,
        definition_id_lookup,
    ):
        """Apply confirmation after the common enrolment/evidence/goal locks."""
        self._validate_actor(actor)
        if self.status != self.STATUS_ACTIVE:
            raise ValidationError(
                'Only an active academic goal can be marked achieved.'
            )
        evidence = self.readiness_evidence(
            evidence_pool=evidence_pool,
            definition_id_lookup=definition_id_lookup,
        )
        if evidence is None:
            raise ValidationError('This academic goal is not ready for achievement.')
        framework_snapshot = self.creation_evidence_snapshot['framework']
        self._lifecycle_transition_token = _ACADEMIC_GOAL_LIFECYCLE_TRANSITION
        self.status = self.STATUS_ACHIEVED
        self.achieved_at = timezone.now()
        self.closed_at = None
        self.confirmed_by = actor
        self.achievement_evidence_snapshot = self.evidence_snapshot(
            evidence,
            level_definitions=framework_snapshot['level_definitions'],
            level_definition_id=evidence._academic_goal_level_definition_id,
        )
        self.save(
            update_fields=[
                'status',
                'achieved_at',
                'closed_at',
                'confirmed_by',
                'achievement_evidence_snapshot',
            ]
        )

    @classmethod
    def confirm_achievement(cls, *, goal_id, actor):
        """Confirm with the global enrolment -> evidence -> goal lock order."""
        with transaction.atomic():
            identity = (
                cls.objects.filter(
                    pk=goal_id,
                    learner__user=actor,
                )
                .values('pk', 'learner_id', 'continuity_code')
                .first()
            )
            if identity is None:
                raise cls.DoesNotExist
            enrollment_ids = list(
                StudentSubject.objects.select_for_update()
                .filter(
                    student_profile_id=identity['learner_id'],
                    continuity_code=identity['continuity_code'],
                )
                .order_by('pk')
                .values_list('pk', flat=True)
            )
            evidence_ids = list(
                CBCGrade.objects.select_for_update()
                .filter(
                    student_subject_id__in=enrollment_ids,
                )
                .order_by('pk')
                .values_list('pk', flat=True)
            )
            evidence_pool = list(
                CBCGrade.objects.filter(pk__in=evidence_ids)
                .select_related('student_subject', 'framework')
                .order_by('academic_grade', 'year', 'term', 'created_at', 'pk')
            )
            definition_id_lookup = cls._definition_id_lookup(evidence_pool)
            goal = (
                cls.objects.select_for_update()
                .select_related(
                    'learner',
                )
                .get(pk=goal_id, learner__user=actor)
            )
            goal._mark_achieved_locked(
                actor=actor,
                evidence_pool=evidence_pool,
                definition_id_lookup=definition_id_lookup,
            )
            return goal

    def mark_achieved(self, *, actor=None, evidence_pool=None):
        """Public transition delegates to the transaction-safe lock service."""
        self._validate_actor(actor)
        if self.pk is None:
            raise ValidationError('An academic goal must be saved before confirmation.')
        transitioned = type(self).confirm_achievement(goal_id=self.pk, actor=actor)
        self.__dict__.update(transitioned.__dict__)

    @staticmethod
    def _definition_id_lookup(evidence_pool):
        lookup = {
            evidence.pk: evidence.level_definition_id_snapshot
            for evidence in evidence_pool
            if evidence.level_definition_id_snapshot is not None
        }
        missing = [
            evidence
            for evidence in evidence_pool
            if evidence.level_definition_id_snapshot is None
        ]
        if not missing:
            return lookup
        live_definitions = {
            (framework_id, code): definition_id
            for framework_id, code, definition_id in (
                PerformanceLevelDefinition.objects.filter(
                    framework_id__in={item.framework_id for item in missing},
                    code__in={item.level for item in missing},
                ).values_list('framework_id', 'code', 'pk')
            )
        }
        lookup.update({
            evidence.pk: live_definitions.get(
                (evidence.framework_id, evidence.level)
            )
            for evidence in missing
        })
        return lookup

    def readiness_evidence(
        self,
        *,
        evidence_pool=None,
        definition_id_lookup=None,
    ):
        if self.status != self.STATUS_ACTIVE:
            return None
        current_order = self._snapshot_order(self.creation_evidence_snapshot)
        framework_snapshot = self.creation_evidence_snapshot['framework']
        if evidence_pool is None:
            evidence_pool = (
                CBCGrade.objects.filter(
                    student_subject__student_profile=self.learner,
                    student_subject__continuity_code=self.continuity_code,
                )
                .select_related('student_subject', 'framework')
                .order_by('academic_grade', 'year', 'term', 'created_at', 'pk')
            )
        evidence_pool = list(evidence_pool)
        if definition_id_lookup is None:
            definition_id_lookup = self._definition_id_lookup(evidence_pool)
        frozen_definitions = framework_snapshot['level_definitions']
        later = []
        for evidence in evidence_pool:
            if (
                evidence.student_subject.student_profile_id != self.learner_id
                or evidence.student_subject.continuity_code != self.continuity_code
                or evidence.framework_id != framework_snapshot['id']
                or self._evidence_order(evidence) <= current_order
            ):
                continue
            definition_id = definition_id_lookup.get(evidence.pk)
            if (
                evidence.level_definition_id_snapshot is None
                and str(definition_id) not in frozen_definitions
            ):
                definition_id = next(
                    (
                        int(frozen_id)
                        for frozen_id, definition in frozen_definitions.items()
                        if definition['code'] == evidence.level
                    ),
                    None,
                )
            if str(definition_id) not in frozen_definitions:
                continue
            evidence._academic_goal_level_definition_id = definition_id
            later.append(evidence)
        if not later:
            return None
        latest = later[-1]
        rank = frozen_definitions[str(latest._academic_goal_level_definition_id)][
            'rank'
        ]
        if rank is None or rank < self.target_level_rank:
            return None
        return latest

    @classmethod
    def batch_readiness(cls, goals):
        active_goals = [goal for goal in goals if goal.status == cls.STATUS_ACTIVE]
        if not active_goals:
            return {}
        learner_ids = {goal.learner_id for goal in active_goals}
        continuity_codes = {goal.continuity_code for goal in active_goals}
        evidence = list(
            CBCGrade.objects.filter(
                student_subject__student_profile_id__in=learner_ids,
                student_subject__continuity_code__in=continuity_codes,
            )
            .select_related('student_subject', 'framework')
            .order_by('academic_grade', 'year', 'term', 'created_at', 'pk')
        )
        definition_id_lookup = cls._definition_id_lookup(evidence)
        return {
            goal.pk: goal.readiness_evidence(
                evidence_pool=evidence,
                definition_id_lookup=definition_id_lookup,
            )
            for goal in active_goals
        }

    def __str__(self):
        return f"{self.learner} — {self.continuity_code}: {self.status}"
