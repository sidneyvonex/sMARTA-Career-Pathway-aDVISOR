from django.db import models
from accounts.models import StudentProfile

DIMENSION_CHOICES = [
    ('R', 'Realistic'),
    ('I', 'Investigative'),
    ('A', 'Artistic'),
    ('S', 'Social'),
    ('E', 'Enterprising'),
    ('C', 'Conventional'),
]


class RIASECQuestion(models.Model):
    dimension = models.CharField(max_length=1, choices=DIMENSION_CHOICES)
    text = models.TextField()
    order = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Q{self.order} ({self.dimension}): {self.text[:50]}'


class Pathway(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    weight_r = models.FloatField()
    weight_i = models.FloatField()
    weight_a = models.FloatField()
    weight_s = models.FloatField()
    weight_e = models.FloatField()
    weight_c = models.FloatField()

    def __str__(self):
        return self.name


class RIASECAssessment(models.Model):
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='riasec_assessments'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.student_profile} — {self.submitted_at:%Y-%m-%d %H:%M}'


class RIASECResponse(models.Model):
    assessment = models.ForeignKey(
        RIASECAssessment, on_delete=models.CASCADE, related_name='responses'
    )
    question = models.ForeignKey(
        RIASECQuestion, on_delete=models.CASCADE, related_name='responses'
    )
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('assessment', 'question')

    def __str__(self):
        return f'Assessment {self.assessment_id} Q{self.question_id}: {self.score}'


class RIASECScore(models.Model):
    assessment = models.ForeignKey(
        RIASECAssessment, on_delete=models.CASCADE, related_name='scores'
    )
    dimension = models.CharField(max_length=1, choices=DIMENSION_CHOICES)
    raw_score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('assessment', 'dimension')

    def __str__(self):
        return f'Assessment {self.assessment_id} {self.dimension}: {self.raw_score}'


class Recommendation(models.Model):
    assessment = models.ForeignKey(
        RIASECAssessment, on_delete=models.CASCADE, related_name='recommendations'
    )
    pathway = models.ForeignKey(
        Pathway, on_delete=models.CASCADE, related_name='recommendations'
    )
    rank = models.PositiveSmallIntegerField()
    fit_score = models.FloatField()
    fit_pct = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [('assessment', 'rank'), ('assessment', 'pathway')]
        ordering = ['rank']

    def __str__(self):
        return f'Assessment {self.assessment_id} #{self.rank}: {self.pathway.name} ({self.fit_pct}%)'
