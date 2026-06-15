DIMENSIONS = ['R', 'I', 'A', 'S', 'E', 'C']


def compute_dim_scores(responses: dict, questions: list) -> dict:
    """
    Sum responses per RIASEC dimension.

    responses: {question_id: score} where score is 1-5
    questions: list of dicts with 'id' and 'dimension' keys
    returns: {'R': int, 'I': int, 'A': int, 'S': int, 'E': int, 'C': int}
    Each value is the sum of 5 Likert responses (range: 5-25).
    """
    scores = {dim: 0 for dim in DIMENSIONS}
    question_dims = {q['id']: q['dimension'] for q in questions}
    for question_id, score in responses.items():
        dim = question_dims.get(int(question_id))
        if dim:
            scores[dim] += score
    return scores


def holland_code(scores: dict) -> str:
    """
    Derive the 3-letter Holland Code from dimension scores.
    Sorted by score descending; tie-break by RIASEC standard order (R first).
    Example: {'R':18,'I':22,'A':14,'S':11,'E':16,'C':13} → 'IRE'
    """
    sorted_dims = sorted(DIMENSIONS, key=lambda d: (-scores[d], DIMENSIONS.index(d)))
    return ''.join(sorted_dims[:3])


def compute_pathway_fits(scores: dict, pathways: list) -> list:
    """
    Compute fit_score and fit_pct for every pathway, return all ranked.

    scores: {'R': int, ...} — output of compute_dim_scores
    pathways: list of dicts with 'id', 'name', 'description',
              'weight_r', 'weight_i', 'weight_a', 'weight_s', 'weight_e', 'weight_c'

    fit_score = Σ(dim_score × pathway_weight[dim]) for all 6 dimensions
    fit_pct   = round((fit_score / 25.0) × 100)

    Returns: [{'rank': int, 'pathway': dict, 'fit_score': float, 'fit_pct': int}, ...]
    Sorted by fit_score descending; tie-break by pathway id ascending.
    """
    results = []
    for pathway in pathways:
        fit_score = (
            scores['R'] * pathway['weight_r'] +
            scores['I'] * pathway['weight_i'] +
            scores['A'] * pathway['weight_a'] +
            scores['S'] * pathway['weight_s'] +
            scores['E'] * pathway['weight_e'] +
            scores['C'] * pathway['weight_c']
        )
        fit_pct = round((fit_score / 25.0) * 100)
        results.append({
            'pathway': pathway,
            'fit_score': fit_score,
            'fit_pct': fit_pct,
        })

    results.sort(key=lambda x: (-x['fit_score'], x['pathway']['id']))

    for i, result in enumerate(results):
        result['rank'] = i + 1

    return results
