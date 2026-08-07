def rank_passages(passages, query, rrf_k=60):
    ranked = []
    for p in passages:
        sim = p.get('similarity_score', 0.5)
        ranked.append({**p, 'rrf_score': sim * 0.9})
    return ranked
