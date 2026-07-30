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


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    grade = models.IntegerField(
        choices=[(9, 'Grade 9'), (10, 'Grade 10')],
        validators=[MinValueValidator(9), MaxValueValidator(10)],
    )
    category = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

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

    student_subject = models.ForeignKey(
        StudentSubject, on_delete=models.CASCADE, related_name='grades'
    )
    term = models.IntegerField(choices=TERM_CHOICES)
    year = models.IntegerField()
    level = models.CharField(max_length=10, choices=GRADE_LEVEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student_subject', 'term', 'year')
        ordering = ['year', 'term']

    def __str__(self):
        return f"{self.student_subject} — T{self.term} {self.year}: {self.level}"
