import pytest


@pytest.mark.django_db
class TestRIASECQuestionModel:
    def test_30_questions_seeded(self):
        from riasec.models import RIASECQuestion
        assert RIASECQuestion.objects.count() == 30

    def test_each_dimension_has_5_questions(self):
        from riasec.models import RIASECQuestion
        for dim in ['R', 'I', 'A', 'S', 'E', 'C']:
            assert RIASECQuestion.objects.filter(dimension=dim).count() == 5, \
                f'Expected 5 questions for dimension {dim}'

    def test_order_is_unique_1_to_30(self):
        from riasec.models import RIASECQuestion
        orders = set(RIASECQuestion.objects.values_list('order', flat=True))
        assert orders == set(range(1, 31))

    def test_no_two_adjacent_questions_share_dimension(self):
        from riasec.models import RIASECQuestion
        questions = list(RIASECQuestion.objects.order_by('order'))
        for i in range(len(questions) - 1):
            assert questions[i].dimension != questions[i + 1].dimension, \
                f'Adjacent questions {questions[i].order} and {questions[i+1].order} share dimension {questions[i].dimension}'


@pytest.mark.django_db
class TestPathwayModel:
    def test_3_pathways_seeded(self):
        from riasec.models import Pathway
        assert Pathway.objects.count() == 3

    def test_pathway_names(self):
        from riasec.models import Pathway
        names = set(Pathway.objects.values_list('name', flat=True))
        assert names == {'STEM', 'Social Sciences', 'Arts & Sports Science'}

    def test_pathway_weights_sum_to_1(self):
        from riasec.models import Pathway
        for pathway in Pathway.objects.all():
            total = round(
                pathway.weight_r + pathway.weight_i + pathway.weight_a +
                pathway.weight_s + pathway.weight_e + pathway.weight_c, 10
            )
            assert total == 1.0, f'{pathway.name} weights sum to {total}, expected 1.0'
