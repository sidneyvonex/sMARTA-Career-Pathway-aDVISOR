from django.core.exceptions import ValidationError
from django.db import models, transaction

from accounts.models import StudentProfile


PROVENANCE_FIELDS = frozenset({
    'source_scope',
    'external_key',
    'source_url',
    'education_framework',
    'admission_cycle',
    'effective_date',
    'verification_status',
})
PARENT_FIELDS = frozenset({'institution', 'institution_id', 'programme', 'programme_id'})
CATALOGUE_PROTECTED_FIELDS = PROVENANCE_FIELDS | PARENT_FIELDS | frozenset({
    'name', 'institution_type', 'county', 'website_url', 'code', 'description',
    'subject_code', 'subject_name', 'mapping_kind', 'notes',
    'requirement_summary',
})
# Unicode White_Space plus the four additional C0 separators treated as
# whitespace by Python str.strip()/str.isspace(). Keep the migration's frozen
# copy aligned with this explicit semantic set.
SEMANTIC_WHITESPACE = (
    '\t', '\n', '\v', '\f', '\r', '\x1c', '\x1d', '\x1e', '\x1f', ' ',
    '\x85', '\xa0', '\u1680', '\u2000', '\u2001', '\u2002', '\u2003',
    '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200a',
    '\u2028', '\u2029', '\u202f', '\u205f', '\u3000',
)


def _protected_write_error(fields):
    names = ', '.join(sorted(fields))
    return ValidationError(
        f'Protected catalogue fields ({names}) must use validated instance saves.'
    )


class ValidatedCatalogueQuerySet(models.QuerySet):
    """Keep public bulk APIs from bypassing sourced-record validation."""

    def update(self, **kwargs):
        protected = set(kwargs) & CATALOGUE_PROTECTED_FIELDS
        if protected:
            raise _protected_write_error(protected)
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        protected = set(fields) & CATALOGUE_PROTECTED_FIELDS
        if protected:
            raise _protected_write_error(protected)
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, *args, **kwargs):
        raise _protected_write_error(PROVENANCE_FIELDS)


class ValidatedCatalogueManager(models.Manager.from_queryset(ValidatedCatalogueQuerySet)):
    pass


def _has_non_whitespace(field):
    # MySQL ICU's ``\s`` omits the four C0 separators that Python treats as
    # whitespace, so include them explicitly while keeping the SQL tree flat.
    return models.Q(**{f'{field}__regex': r'[^\s\x0b\x1c-\x1f\x85]'})


def _provenance_constraints(prefix):
    return [
        models.CheckConstraint(check=_has_non_whitespace('source_scope'), name=f'{prefix}_scope_nonempty_ck'),
        models.CheckConstraint(check=_has_non_whitespace('external_key'), name=f'{prefix}_key_nonempty_ck'),
        models.CheckConstraint(check=_has_non_whitespace('source_url'), name=f'{prefix}_url_nonempty_ck'),
        models.CheckConstraint(check=_has_non_whitespace('education_framework'), name=f'{prefix}_frame_nonempty_ck'),
        models.CheckConstraint(check=_has_non_whitespace('admission_cycle'), name=f'{prefix}_cycle_nonempty_ck'),
        models.CheckConstraint(
            check=models.Q(verification_status__in=['verified', 'historical', 'unavailable']),
            name=f'{prefix}_verification_ck',
        ),
    ]


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

    objects = ValidatedCatalogueManager()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        errors = {}
        for field in PROVENANCE_FIELDS - {'effective_date', 'verification_status'}:
            value = getattr(self, field, None)
            if not isinstance(value, str) or not value.strip():
                errors[field] = 'This provenance value is required.'
        if self.verification_status not in dict(self.VERIFICATION_CHOICES):
            errors['verification_status'] = 'Choose a supported verification status.'
        if errors:
            raise ValidationError(errors)

    def _reject_referenced_changes(self, related_queries):
        if not self.pk or not any(query.exists() for query in related_queries):
            return
        original = type(self).objects.filter(pk=self.pk).values(*PROVENANCE_FIELDS).first()
        if original and any(original[field] != getattr(self, field) for field in PROVENANCE_FIELDS):
            raise ValidationError(
                'Catalogue identity and provenance cannot be changed once referenced.'
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                type(self).objects.select_for_update().filter(pk=self.pk).exists()
            self.full_clean(validate_unique=False, validate_constraints=False)
            return super().save(*args, **kwargs)


def _parent_value(parent, field):
    return getattr(parent, field)


def _validate_parent_coherence(child, parent, parent_field):
    # A sourced release shares scope/framework/cycle. Effective dates remain
    # record-specific, and status may differ only when the child is no more
    # authoritative than its parent (verified > historical > unavailable).
    errors = {}
    for field in ('source_scope', 'education_framework', 'admission_cycle'):
        if getattr(child, field) != _parent_value(parent, field):
            errors[field] = f'Must match the selected {parent_field} source release.'
    authority = {'unavailable': 0, 'historical': 1, 'verified': 2}
    if authority.get(child.verification_status, -1) > authority.get(parent.verification_status, -1):
        errors['verification_status'] = (
            f'Cannot be more authoritative than the selected {parent_field}.'
        )
    if errors:
        raise ValidationError(errors)


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
            *_provenance_constraints('tert_inst'),
            models.UniqueConstraint(
                fields=['source_scope', 'external_key'],
                name='tertiary_inst_scope_external_uniq',
            ),
            models.CheckConstraint(
                check=models.Q(institution_type__in=['university', 'college', 'tvet', 'other']),
                name='tert_inst_type_ck',
            ),
        ]
        indexes = [
            models.Index(fields=['education_framework', 'admission_cycle'], name='tert_inst_frame_cycle_idx'),
            models.Index(fields=['verification_status', 'name'], name='tert_inst_status_name_idx'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.institution_type not in dict(self.TYPE_CHOICES):
            raise ValidationError({'institution_type': 'Choose a supported institution type.'})
        if self.pk:
            self._reject_referenced_changes((self.programmes.all(), self.learner_goals.all()))


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
            *_provenance_constraints('tert_prog'),
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

    def clean(self):
        super().clean()
        if self.institution_id:
            _validate_parent_coherence(self, self.institution, 'institution')
        if self.pk:
            original = Programme.objects.filter(pk=self.pk).values('institution_id').first()
            is_referenced = (
                self.subject_references.exists()
                or self.historical_admission_references.exists()
                or self.learner_goals.exists()
            )
            if original and is_referenced and original['institution_id'] != self.institution_id:
                raise ValidationError(
                    'Catalogue identity and provenance cannot be changed once referenced.'
                )
            self._reject_referenced_changes((
                self.subject_references.all(),
                self.historical_admission_references.all(),
                self.learner_goals.all(),
            ))

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.institution_id:
                self.institution = Institution.objects.select_for_update().get(
                    pk=self.institution_id
                )
            return super().save(*args, **kwargs)


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
            *_provenance_constraints('tert_subj'),
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
            models.CheckConstraint(
                check=(
                    ~models.Q(mapping_kind='historical_requirement')
                    | (
                        models.Q(education_framework='KCSE')
                        & models.Q(verification_status='historical')
                    )
                ),
                name='tert_subj_historical_kcse_ck',
            ),
        ]
        indexes = [
            models.Index(fields=['programme', 'mapping_kind'], name='tert_subj_prog_kind_idx'),
        ]

    def clean(self):
        super().clean()
        if self.programme_id:
            _validate_parent_coherence(self, self.programme, 'programme')
        if self.mapping_kind == self.KIND_HISTORICAL_REQUIREMENT and (
            self.education_framework != 'KCSE'
            or self.verification_status != self.VERIFICATION_HISTORICAL
        ):
            raise ValidationError({
                'mapping_kind': 'Historical requirements must be historical KCSE references.'
            })

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.programme_id:
                self.programme = Programme.objects.select_for_update().get(
                    pk=self.programme_id
                )
            return super().save(*args, **kwargs)


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
            *_provenance_constraints('tert_hist'),
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

    def clean(self):
        super().clean()
        if self.programme_id:
            _validate_parent_coherence(self, self.programme, 'programme')
        if (
            self.education_framework != 'KCSE'
            or self.verification_status != self.VERIFICATION_HISTORICAL
        ):
            raise ValidationError(
                'Historical admission references must use KCSE and historical status.'
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.programme_id:
                self.programme = Programme.objects.select_for_update().get(
                    pk=self.programme_id
                )
            return super().save(*args, **kwargs)


def education_choice_identity(institution_id, programme_id):
    programme = programme_id if programme_id is not None else 'none'
    return f'institution:{institution_id}:programme:{programme}'


class LearnerEducationGoalQuerySet(models.QuerySet):
    PROTECTED_FIELDS = frozenset({
        'learner', 'learner_id', 'institution', 'institution_id', 'programme',
        'programme_id', 'choice_identity', 'kind', 'priority', 'created_by',
        'created_by_id',
    })

    def update(self, **kwargs):
        protected = set(kwargs) & self.PROTECTED_FIELDS
        if protected:
            raise ValidationError('Education choices must use validated instance saves.')
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if set(fields) & self.PROTECTED_FIELDS:
            raise ValidationError('Education choices must use validated instance saves.')
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, *args, **kwargs):
        raise ValidationError('Education choices must use validated instance saves.')


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
    choice_identity = models.CharField(max_length=80)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    priority = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='education_goals_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager.from_queryset(LearnerEducationGoalQuerySet)()

    class Meta:
        ordering = ['kind', 'priority', 'created_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['learner', 'kind', 'priority'],
                name='tertiary_goal_learner_slot_uniq',
            ),
            models.UniqueConstraint(
                fields=['learner', 'choice_identity'],
                name='tertiary_goal_learner_choice_uniq',
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
            programme_institution_id = Programme.objects.filter(
                pk=self.programme_id
            ).values_list('institution_id', flat=True).first()
            if programme_institution_id != self.institution_id:
                raise ValidationError(
                    {'programme': 'The programme must belong to the selected institution.'}
                )

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        normalized_update_fields = (
            None if update_fields is None else set(update_fields)
        )
        with transaction.atomic():
            stored = None
            if self.pk:
                stored = type(self).objects.filter(pk=self.pk).values(
                    'learner_id', 'institution_id', 'programme_id'
                ).first()
            relation_fields = {
                'learner_id': {'learner', 'learner_id'},
                'institution_id': {'institution', 'institution_id'},
                'programme_id': {'programme', 'programme_id'},
            }
            if stored is not None and normalized_update_fields is not None:
                for attname, accepted_names in relation_fields.items():
                    if not normalized_update_fields.intersection(accepted_names):
                        setattr(self, attname, stored[attname])

            learner_ids = {self.learner_id}
            if stored is not None:
                learner_ids.add(stored['learner_id'])
            list(StudentProfile.objects.select_for_update().filter(
                pk__in=sorted(learner_ids)
            ).order_by('pk'))
            self.institution = Institution.objects.select_for_update().get(
                pk=self.institution_id
            )
            if self.programme_id:
                self.programme = Programme.objects.select_for_update().get(
                    pk=self.programme_id
                )
            if self.pk:
                locked = type(self).objects.select_for_update().filter(
                    pk=self.pk
                ).values('learner_id', 'institution_id', 'programme_id').first()
                if locked != stored:
                    raise ValidationError(
                        'Education goal changed concurrently; reload it and try again.'
                    )
            self.choice_identity = education_choice_identity(
                self.institution_id, self.programme_id
            )
            if normalized_update_fields is not None:
                relation_names = relation_fields['institution_id'] | relation_fields['programme_id']
                if normalized_update_fields.intersection(relation_names):
                    normalized_update_fields.add('choice_identity')
                kwargs['update_fields'] = normalized_update_fields
            self.full_clean(validate_unique=False, validate_constraints=False)
            return super().save(*args, **kwargs)
