"""
Pure unit tests for riasec/scoring.py — no database, no Django fixtures.
All inputs are plain Python dicts.
"""
import pytest


# ---------------------------------------------------------------------------
# Fixtures: plain dicts (no DB)
# ---------------------------------------------------------------------------

QUESTIONS = [
    {'id': 1,  'dimension': 'R'},
    {'id': 2,  'dimension': 'I'},
    {'id': 3,  'dimension': 'A'},
    {'id': 4,  'dimension': 'S'},
    {'id': 5,  'dimension': 'E'},
    {'id': 6,  'dimension': 'C'},
    {'id': 7,  'dimension': 'R'},
    {'id': 8,  'dimension': 'I'},
    {'id': 9,  'dimension': 'A'},
    {'id': 10, 'dimension': 'S'},
    {'id': 11, 'dimension': 'E'},
    {'id': 12, 'dimension': 'C'},
    {'id': 13, 'dimension': 'R'},
    {'id': 14, 'dimension': 'I'},
    {'id': 15, 'dimension': 'A'},
    {'id': 16, 'dimension': 'S'},
    {'id': 17, 'dimension': 'E'},
    {'id': 18, 'dimension': 'C'},
    {'id': 19, 'dimension': 'R'},
    {'id': 20, 'dimension': 'I'},
    {'id': 21, 'dimension': 'A'},
    {'id': 22, 'dimension': 'S'},
    {'id': 23, 'dimension': 'E'},
    {'id': 24, 'dimension': 'C'},
    {'id': 25, 'dimension': 'R'},
    {'id': 26, 'dimension': 'I'},
    {'id': 27, 'dimension': 'A'},
    {'id': 28, 'dimension': 'S'},
    {'id': 29, 'dimension': 'E'},
    {'id': 30, 'dimension': 'C'},
]

PATHWAYS = [
    {'id': 1, 'name': 'STEM',                 'description': '...', 'weight_r': 0.25, 'weight_i': 0.40, 'weight_a': 0.05, 'weight_s': 0.05, 'weight_e': 0.15, 'weight_c': 0.10},
    {'id': 2, 'name': 'Social Sciences',       'description': '...', 'weight_r': 0.05, 'weight_i': 0.15, 'weight_a': 0.10, 'weight_s': 0.35, 'weight_e': 0.25, 'weight_c': 0.10},
    {'id': 3, 'name': 'Arts & Sports Science', 'description': '...', 'weight_r': 0.20, 'weight_i': 0.05, 'weight_a': 0.45, 'weight_s': 0.20, 'weight_e': 0.05, 'weight_c': 0.05},
]


def make_responses(scores_by_dim):
    """Build {question_id: score} from {dimension: score} — all 5 questions for a dim get the same score."""
    responses = {}
    for q in QUESTIONS:
        responses[q['id']] = scores_by_dim[q['dimension']]
    return responses


# ---------------------------------------------------------------------------
# compute_dim_scores
# ---------------------------------------------------------------------------

class TestComputeDimScores:
    def test_sums_correctly(self):
        from riasec.scoring import compute_dim_scores
        responses = make_responses({'R': 4, 'I': 5, 'A': 3, 'S': 2, 'E': 4, 'C': 3})
        result = compute_dim_scores(responses, QUESTIONS)
        assert result == {'R': 20, 'I': 25, 'A': 15, 'S': 10, 'E': 20, 'C': 15}

    def test_max_scores_all_5(self):
        from riasec.scoring import compute_dim_scores
        responses = make_responses({'R': 5, 'I': 5, 'A': 5, 'S': 5, 'E': 5, 'C': 5})
        result = compute_dim_scores(responses, QUESTIONS)
        assert all(v == 25 for v in result.values())

    def test_min_scores_all_1(self):
        from riasec.scoring import compute_dim_scores
        responses = make_responses({'R': 1, 'I': 1, 'A': 1, 'S': 1, 'E': 1, 'C': 1})
        result = compute_dim_scores(responses, QUESTIONS)
        assert all(v == 5 for v in result.values())

    def test_returns_all_6_dimensions(self):
        from riasec.scoring import compute_dim_scores
        responses = make_responses({'R': 3, 'I': 3, 'A': 3, 'S': 3, 'E': 3, 'C': 3})
        result = compute_dim_scores(responses, QUESTIONS)
        assert set(result.keys()) == {'R', 'I', 'A', 'S', 'E', 'C'}


# ---------------------------------------------------------------------------
# holland_code
# ---------------------------------------------------------------------------

class TestHollandCode:
    def test_basic_case(self):
        from riasec.scoring import holland_code
        scores = {'R': 18, 'I': 22, 'A': 14, 'S': 11, 'E': 16, 'C': 13}
        assert holland_code(scores) == 'IRE'

    def test_all_equal_uses_riasec_order(self):
        from riasec.scoring import holland_code
        scores = {'R': 15, 'I': 15, 'A': 15, 'S': 15, 'E': 15, 'C': 15}
        assert holland_code(scores) == 'RIA'

    def test_tie_in_second_and_third(self):
        from riasec.scoring import holland_code
        # R=25, I=20, A=20 — tie between I and A resolved by RIASEC order (I before A)
        scores = {'R': 25, 'I': 20, 'A': 20, 'S': 10, 'E': 10, 'C': 10}
        assert holland_code(scores) == 'RIA'

    def test_returns_exactly_3_letters(self):
        from riasec.scoring import holland_code
        scores = {'R': 18, 'I': 22, 'A': 14, 'S': 11, 'E': 16, 'C': 13}
        result = holland_code(scores)
        assert len(result) == 3
        assert all(c in 'RIASEC' for c in result)


# ---------------------------------------------------------------------------
# compute_pathway_fits
# ---------------------------------------------------------------------------

class TestComputePathwayFits:
    def test_worked_example_from_spec(self):
        from riasec.scoring import compute_pathway_fits
        scores = {'R': 18, 'I': 22, 'A': 14, 'S': 11, 'E': 16, 'C': 13}
        results = compute_pathway_fits(scores, PATHWAYS)
        assert results[0]['pathway']['name'] == 'STEM'
        assert results[0]['rank'] == 1
        assert results[0]['fit_pct'] == 73
        assert results[1]['rank'] == 2
        assert results[2]['rank'] == 3

    def test_returns_all_3_pathways(self):
        from riasec.scoring import compute_pathway_fits
        scores = {'R': 15, 'I': 15, 'A': 15, 'S': 15, 'E': 15, 'C': 15}
        results = compute_pathway_fits(scores, PATHWAYS)
        assert len(results) == 3

    def test_ranks_are_1_2_3(self):
        from riasec.scoring import compute_pathway_fits
        scores = {'R': 20, 'I': 25, 'A': 5, 'S': 5, 'E': 10, 'C': 10}
        results = compute_pathway_fits(scores, PATHWAYS)
        assert [r['rank'] for r in results] == [1, 2, 3]

    def test_fit_pct_is_0_to_100(self):
        from riasec.scoring import compute_pathway_fits
        scores = {'R': 5, 'I': 5, 'A': 5, 'S': 5, 'E': 5, 'C': 5}
        results = compute_pathway_fits(scores, PATHWAYS)
        for r in results:
            assert 0 <= r['fit_pct'] <= 100

    def test_max_scores_give_100_pct(self):
        from riasec.scoring import compute_pathway_fits
        # All 25 for every dimension → fit_score = 25 × (sum of weights) = 25 × 1.0 = 25 → 100%
        scores = {'R': 25, 'I': 25, 'A': 25, 'S': 25, 'E': 25, 'C': 25}
        results = compute_pathway_fits(scores, PATHWAYS)
        for r in results:
            assert r['fit_pct'] == 100

    def test_arts_student_ranks_arts_first(self):
        from riasec.scoring import compute_pathway_fits
        # High A and S scores → Arts & Sports Science should rank #1
        scores = {'R': 10, 'I': 5, 'A': 25, 'S': 25, 'E': 5, 'C': 5}
        results = compute_pathway_fits(scores, PATHWAYS)
        assert results[0]['pathway']['name'] == 'Arts & Sports Science'

    def test_social_student_ranks_social_sciences_first(self):
        from riasec.scoring import compute_pathway_fits
        scores = {'R': 5, 'I': 10, 'A': 10, 'S': 25, 'E': 25, 'C': 20}
        results = compute_pathway_fits(scores, PATHWAYS)
        assert results[0]['pathway']['name'] == 'Social Sciences'
