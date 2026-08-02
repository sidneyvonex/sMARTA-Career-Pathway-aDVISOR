from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import StudentProfile


class SourcedCatalogueRecord(models.Model):
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_HISTORICAL = 'historical'
    VERIFICATION_UNAVAILABLE = 'unavailable'
    VERIFICATION_CHOICES = [
        (VERIFICATION_VERIFIED, 'Verified'),
        (VERIFICATION_HISTORICAL, 'Historical reference'),
        (VERIFICATION_UNAVAILABLE, 'Unavailable'),
    ]

    source_scope = models.CharField(max_length=120)
    external_key = models.CharField(max_length=160)
    source_url = models.URLField(max_length=500)
    education_framework = models.CharField(max_length=120)
    admission_cycle = models.CharField(max_length=80)
    effective_date = models.DateField()
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Institution(SourcedCatalogueRecord):
    TYPE_UNIVERSITY = 'university'
    TYPE_COLLEGE = 'college'
    TYPE_TVET = 'tvet'
    TYPE_OTHER = 'other'
    TYPE_CHOICES = [
        (TYPE_UNIVERSITY, 'University'),
        (TYPE_COLLEGE, 'College'),
        (TYPE_TVET, 'TVET institution'),
        (TYPE_OTHER, 'Other'),
    ]

    name = models.CharField(max_length=240, db_index=True)
    institution_type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    county = models.CharField(max_length=80, blank=True, db_index=True)
    website_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ['name', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['source_scope', 'external_key'],
                name='tertiary_inst_scope_external_uniq',
            ),
        ]
        indexes = [
            models.Index(fields=['education_framework', 'admission_cycle'], name='tert_inst_frame_cycle_idx'),
            models.Index(fields=['verification_status', 'name'], name='tert_inst_status_name_idx'),
        ]

    def __str__(self):
        return self.name


class Programme(SourcedCatalogueRecord):
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name='programmes',
    )
    code = models.CharField(max_length=80, blank=True, db_index=True)
    name = models.CharField(max_length=240, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['institution__name', 'name', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['source_scope', 'external_key'],
                name='tertiary_prog_scope_external_uniq',
            ),
        ]
        indexes = [
            models.Index(fields=['institution', 'name'], name='tert_prog_inst_name_idx'),
            models.Index(fields=['education_framework', 'admission_cycle'], name='tert_prog_frame_cycle_idx'),
            models.Index(fields=['verification_status', 'name'], name='tert_prog_status_name_idx'),
        ]

    def __str__(self):
        return f'{self.institution.name} — {self.name}'


class ProgrammeSubjectReference(SourcedCatalogueRecord):
    KIND_HISTORICAL_REQUIREMENT = 'historical_requirement'
    KIND_EXPLORATORY_ALIGNMENT = 'exploratory_alignment'
    KIND_CHOICES = [
        (KIND_HISTORICAL_REQUIREMENT, 'Historical requirement'),
        (KIND_EXPLORATORY_ALIGNMENT, 'Exploratory alignment'),
    ]

    programme = models.ForeignKey(
        Programme,
        on_delete=models.CASCADE,
        related_name='subject_references',
    )
    subject_code = models.CharField(max_length=80, db_index=True)
    subject_name = models.CharField(max_length=160)
    mapping_kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['subject_name', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['source_scope', 'external_key'],
                name='tertiary_subj_scope_external_uniq',
            ),
            models.CheckConstraint(
                check=models.Q(
                    mapping_kind__in=[
                        'historical_requirement',
                        'exploratory_alignment',
                    ]
                ),
                name='tertiary_subj_mapping_kind_ck',
            ),
        ]
        indexes = [
            models.Index(fields=['programme', 'mapping_kind'], name='tert_subj_prog_kind_idx'),
        ]


class HistoricalAdmissionReference(SourcedCatalogueRecord):
    programme = models.ForeignKey(
        Programme,
        on_delete=models.CASCADE,
        related_name='historical_admission_references',
    )
    requirement_summary = models.TextField()

    class Meta:
        ordering = ['-effective_date', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['source_scope', 'external_key'],
                name='tertiary_hist_scope_external_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(education_framework='KCSE')
                    & models.Q(verification_status='historical')
                ),
                name='tertiary_hist_kcse_reference_ck',
            ),
        ]
        indexes = [
            models.Index(fields=['programme', 'admission_cycle'], name='tert_hist_prog_cycle_idx'),
        ]


class LearnerEducationGoal(models.Model):
    KIND_PRIMARY = 'primary'
    KIND_ALTERNATIVE = 'alternative'
    KIND_CHOICES = [
        (KIND_PRIMARY, 'Primary'),
        (KIND_ALTERNATIVE, 'Alternative'),
    ]

    learner = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='education_goals',
    )
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name='learner_goals',
    )
    programme = models.ForeignKey(
        Programme,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='learner_goals',
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    priority = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='education_goals_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['kind', 'priority', 'created_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['learner', 'kind', 'priority'],
                name='tertiary_goal_learner_slot_uniq',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(kind='primary', priority=1)
                    | models.Q(kind='alternative', priority__in=[1, 2])
                ),
                name='tertiary_goal_kind_priority_ck',
            ),
        ]
        indexes = [models.Index(fields=['learner', 'kind'], name='tert_goal_learner_kind_idx')]

    def clean(self):
        super().clean()
        if self.programme_id and self.institution_id:
            programme_institution_id = (
                self.programme.institution_id
                if 'programme' in self._state.fields_cache
                else Programme.objects.filter(pk=self.programme_id).values_list(
                    'institution_id', flat=True
                ).first()
            )
            if programme_institution_id != self.institution_id:
                raise ValidationError(
                    {'programme': 'The programme must belong to the selected institution.'}
                )

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False, validate_constraints=False)
        return super().save(*args, **kwargs)
