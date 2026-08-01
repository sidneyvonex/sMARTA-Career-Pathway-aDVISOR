from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
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
    grade = models.IntegerField(
        choices=[(9, 'Grade 9'), (10, 'Grade 10')],
        validators=[MinValueValidator(9), MaxValueValidator(10)],
    )
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_selectable_in_combination = models.BooleanField(default=False)

    class Meta:
        ordering = ['grade', 'category', 'name']

    def __str__(self):
        return f"{self.code} — {self.name}"


class StudentSubject(models.Model):
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='enrolled_subjects'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student_profile', 'subject')

    def __str__(self):
        return f"{self.student_profile} — {self.subject.code}"


class CBCGrade(models.Model):
    TERM_CHOICES = [(1, 'Term 1'), (2, 'Term 2'), (3, 'Term 3')]
    SOURCE_CHOICES = [('learner', 'Learner'), ('school', 'School')]

    student_subject = models.ForeignKey(
        StudentSubject, on_delete=models.CASCADE, related_name='grades'
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

        subject_grade = self.student_subject.subject.grade
        if self.academic_grade != subject_grade:
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
                self.academic_grade = self.student_subject.subject.grade
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
