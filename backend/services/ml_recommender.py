import json
import numpy as np
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

def safe_num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def cosine_similarity_score(v1: list, v2: list) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

async def search_opportunities_vector(
    db: AsyncSession,
    model_class,
    user_vector: list[float],
    limit: int = 12,
    filters: list = None
) -> list:
    """
    Search and rank opportunities using dense vector similarity.
    Applies optional SQLAlchemy filters first, then calculates similarity scores.
    """
    if not user_vector:
        # Fallback to standard database query if user vector is missing
        query = select(model_class)
        if filters:
            for f in filters:
                query = query.where(f)
        query = query.limit(limit)
        result = await db.execute(query)
        records = result.scalars().all()
        for r in records:
            r.ml_score = 0.5  # default neutral score
        return list(records)

    # 1. Fetch records with filtering
    query = select(model_class)
    if filters:
        for f in filters:
            query = query.where(f)
            
    result = await db.execute(query)
    records = result.scalars().all()
    
    # 2. Compute similarity scores
    scored_records = []
    for r in records:
        score = 0.0
        if r.embedding:
            emb = r.embedding
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    emb = []
            score = cosine_similarity_score(user_vector, emb)
        scored_records.append((r, score))
        
    # 3. Sort by score descending
    scored_records.sort(key=lambda x: x[1], reverse=True)
    
    # 4. Extract top N results
    results = []
    for r, score in scored_records[:limit]:
        # Dynamically set ml_score on the record object for serializer access
        r.ml_score = score
        results.append(r)
        
    return results