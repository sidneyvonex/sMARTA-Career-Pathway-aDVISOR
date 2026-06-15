from django.db import models
from accounts.models import StudentProfile

GRADE_LEVEL_CHOICES = [
    ('EE1', 'Exceeding Expectation (lower)'),
    ('EE2', 'Exceeding Expectation (upper)'),
    ('ME1', 'Meeting Expectation (lower)'),
    ('ME2', 'Meeting Expectation (upper)'),
    ('AE1', 'Approaching Expectation (lower)'),
    ('AE2', 'Approaching Expectation (upper)'),
    ('BE1', 'Below Expectation (lower)'),
    ('BE2', 'Below Expectation (upper)'),
]


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    grade = models.IntegerField(choices=[(9, 'Grade 9'), (10, 'Grade 10')])
    category = models.CharField(max_length=50)

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
