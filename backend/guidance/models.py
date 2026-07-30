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
            if subject.category.casefold() != 'elective':
                messages.append('Subject must be an elective.')
            if not subject.is_active:
                messages.append('Subject must be active.')
            if messages:
                errors[field_name] = messages

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.code} — {self.title}'


class SchoolOffering(models.Model):
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
