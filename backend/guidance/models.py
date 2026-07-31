from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q


class FrameworkVersionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class FrameworkVersionManager(models.Manager.from_queryset(FrameworkVersionQuerySet)):
    def current(self):
        return self.active().order_by('-effective_date', '-pk').first()


class FrameworkVersion(models.Model):
    code = models.CharField(max_length=40, unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default='')
    source_url = models.URLField(max_length=500)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FrameworkVersionManager()

    class Meta:
        ordering = ['-effective_date', '-created_at']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_active:
                (
                    type(self).objects.select_for_update()
                    .filter(is_active=True)
                    .exclude(pk=self.pk)
                    .update(is_active=False)
                )
            return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.title}'


class PathwayTrack(models.Model):
    framework_version = models.ForeignKey(
        FrameworkVersion,
        on_delete=models.CASCADE,
        related_name='tracks',
    )
    pathway = models.ForeignKey(
        'riasec.Pathway',
        on_delete=models.PROTECT,
        related_name='framework_tracks',
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['pathway__name', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['framework_version', 'code'],
                name='guidance_track_fw_code_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.pathway.name} — {self.name}'


class SubjectCombination(models.Model):
    VERIFICATION_UNVERIFIED = 'unverified'
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_STATUS_CHOICES = [
        (VERIFICATION_UNVERIFIED, 'Unverified'),
        (VERIFICATION_VERIFIED, 'Verified'),
    ]

    framework_version = models.ForeignKey(
        FrameworkVersion,
        on_delete=models.CASCADE,
        related_name='combinations',
    )
    track = models.ForeignKey(
        PathwayTrack,
        on_delete=models.PROTECT,
        related_name='combinations',
    )
    code = models.CharField(max_length=40)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default='')
    related_routes = models.JSONField(default=list)
    subject_one = models.ForeignKey(
        'students.Subject',
        on_delete=models.PROTECT,
        related_name='combinations_as_subject_one',
    )
    subject_two = models.ForeignKey(
        'students.Subject',
        on_delete=models.PROTECT,
        related_name='combinations_as_subject_two',
    )
    subject_three = models.ForeignKey(
        'students.Subject',
        on_delete=models.PROTECT,
        related_name='combinations_as_subject_three',
    )
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=VERIFICATION_UNVERIFIED,
    )
    source_url = models.URLField(max_length=500, blank=True, default='')
    source_checked_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['track__pathway__name', 'track__name', 'title']
        constraints = [
            models.UniqueConstraint(
                fields=['framework_version', 'code'],
                name='guidance_combo_fw_code_uniq',
            ),
            models.CheckConstraint(
                check=(
                    ~Q(subject_one=F('subject_two'))
                    & ~Q(subject_one=F('subject_three'))
                    & ~Q(subject_two=F('subject_three'))
                ),
                name='guidance_combo_subjects_distinct',
            ),
        ]

    @property
    def subjects(self):
        return (self.subject_one, self.subject_two, self.subject_three)

    def clean(self):
        super().clean()
        errors = {}

        if (
            self.track_id
            and self.framework_version_id
            and self.track.framework_version_id != self.framework_version_id
        ):
            errors['track'] = 'Track must belong to the selected framework version.'

        subject_ids = [
            subject_id
            for subject_id in (
                self.subject_one_id,
                self.subject_two_id,
                self.subject_three_id,
            )
            if subject_id is not None
        ]
        if len(subject_ids) != len(set(subject_ids)):
            errors['subject_two'] = 'Select exactly three distinct elective subjects.'

        for field_name in ('subject_one', 'subject_two', 'subject_three'):
            subject_id = getattr(self, f'{field_name}_id')
            if subject_id is None:
                continue
            subject = getattr(self, field_name)
            messages = []
            if subject.grade != 10:
                messages.append('Subject must be a Grade 10 subject.')
            if not subject.is_selectable_in_combination:
                messages.append('Subject must be selectable in an official combination.')
            if not subject.is_active:
                messages.append('Subject must be active.')
            if messages:
                errors[field_name] = messages

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.code} — {self.title}'


class SchoolOffering(models.Model):
    VERIFICATION_UNVERIFIED = 'unverified'
    VERIFICATION_VERIFIED = 'verified'
    VERIFICATION_DEMONSTRATION = 'demonstration'
    VERIFICATION_STATUS_CHOICES = [
        (VERIFICATION_UNVERIFIED, 'Unverified'),
        (VERIFICATION_VERIFIED, 'Verified'),
        (VERIFICATION_DEMONSTRATION, 'Demonstration'),
    ]

    school = models.ForeignKey(
        'accounts.School',
        on_delete=models.CASCADE,
        related_name='guidance_offerings',
    )
    combination = models.ForeignKey(
        SubjectCombination,
        on_delete=models.PROTECT,
        related_name='school_offerings',
    )
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=VERIFICATION_UNVERIFIED,
    )
    source_url = models.URLField(max_length=500, blank=True, default='')
    source_checked_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school__name', 'combination__title']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'combination'],
                name='guidance_school_combo_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.school.name} — {self.combination.title}'


class LearnerCombinationChoice(models.Model):
    STATUS_SAVED = 'saved'
    STATUS_PROVISIONAL = 'provisional'
    STATUS_CHOICES = [
        (STATUS_SAVED, 'Saved'),
        (STATUS_PROVISIONAL, 'Provisional'),
    ]

    student_profile = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='combination_choices',
    )
    combination = models.ForeignKey(
        SubjectCombination,
        on_delete=models.PROTECT,
        related_name='learner_choices',
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_SAVED,
    )
    learner_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['student_profile', 'combination'],
                name='guidance_learner_combo_uniq',
            ),
            models.UniqueConstraint(
                fields=['student_profile'],
                condition=Q(status='provisional'),
                name='guidance_one_provisional_choice',
            ),
        ]

    def clean(self):
        super().clean()
        if not self.combination_id:
            return
        combination = self.combination
        current_framework = FrameworkVersion.objects.current()
        if (
            current_framework is None
            or combination.framework_version_id != current_framework.pk
            or not combination.is_active
            or not combination.track.is_active
        ):
            raise ValidationError({
                'combination': 'Choose an active combination from the current guidance framework.'
            })

    def __str__(self):
        return f'{self.student_profile} - {self.combination.code} ({self.status})'


class LearnerPlan(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_READY = 'ready_for_review'
    STATUS_REVIEWED = 'reviewed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_READY, 'Ready for review'),
        (STATUS_REVIEWED, 'Reviewed'),
    ]

    student_profile = models.OneToOneField(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='learner_plan',
    )
    provisional_choice = models.ForeignKey(
        LearnerCombinationChoice,
        on_delete=models.PROTECT,
        related_name='plans',
    )
    learner_reason = models.TextField(blank=True, default='')
    review_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        errors = {}
        if (
            self.provisional_choice_id
            and self.student_profile_id
            and self.provisional_choice.student_profile_id != self.student_profile_id
        ):
            errors['provisional_choice'] = 'The provisional choice must belong to this learner.'
        if (
            self.provisional_choice_id
            and self.provisional_choice.status
            != LearnerCombinationChoice.STATUS_PROVISIONAL
        ):
            errors['provisional_choice'] = 'Select the learner\'s current provisional choice.'
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.student_profile} - {self.review_status}'


class PlanMilestone(models.Model):
    plan = models.ForeignKey(
        LearnerPlan,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    title = models.CharField(max_length=160)
    due_date = models.DateField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'created_at', 'pk']

    def __str__(self):
        return self.title
