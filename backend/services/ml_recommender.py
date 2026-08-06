import json
import numpy as np
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from services.qdrant_service import qdrant_service

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
    Tries searching with Qdrant first (with SQL filtering constraints if present),
    and falls back to standard in-memory numpy ranking if Qdrant is unavailable.
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

    collection_name = model_class.__tablename__

    # --- QDRANT SEARCH ROUTE ---
    if qdrant_service.client is not None:
        try:
            qdrant_results = []
            if filters:
                # 1. Apply SQL filters first to get candidate IDs
                candidate_query = select(model_class.id)
                for f in filters:
                    candidate_query = candidate_query.where(f)
                candidate_result = await db.execute(candidate_query)
                candidate_ids = list(candidate_result.scalars().all())

                if not candidate_ids:
                    return []

                # 2. Perform Qdrant search restricted to candidate IDs
                qdrant_results = qdrant_service.search_opportunities(
                    collection_name=collection_name,
                    query_vector=user_vector,
                    limit=limit,
                    ids=candidate_ids
                )
            else:
                # 2. Perform unrestricted Qdrant search
                qdrant_results = qdrant_service.search_opportunities(
                    collection_name=collection_name,
                    query_vector=user_vector,
                    limit=limit
                )

            if qdrant_results:
                # 3. Retrieve full DB objects matching the top Qdrant results
                id_to_score = {item["id"]: item["score"] for item in qdrant_results}
                db_query = select(model_class).where(model_class.id.in_(list(id_to_score.keys())))
                db_result = await db.execute(db_query)
                db_records = list(db_result.scalars().all())

                # 4. Map score back to SQL objects and sort descending
                for r in db_records:
                    r.ml_score = id_to_score.get(r.id, 0.0)
                db_records.sort(key=lambda x: x.ml_score, reverse=True)
                return db_records
            else:
                print(f"[QDRANT WARNING] No search results returned from collection '{collection_name}'. Falling back to local NumPy ranking.")

        except Exception as e:
            print(f"[QDRANT ERROR] Search failed: {e}. Falling back to local NumPy ranking.")

    # --- FALLBACK: IN-MEMORY NUMPY COSINE SIMILARITY ROUTE ---
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
        r.ml_score = score
        results.append(r)
        
    return results