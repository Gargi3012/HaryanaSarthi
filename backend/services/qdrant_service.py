import os
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from config import settings

class QdrantService:
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.known_collections = set()
        self._initialize_client()

    def _initialize_client(self):
        """
        Initializes the Qdrant client. If QDRANT_URL and QDRANT_API_KEY are configured
        in the settings/environment, it connects to the cloud database. Otherwise, it
        falls back to a local storage database in backend/data/qdrant_db.
        """
        url = settings.QDRANT_URL or os.getenv("QDRANT_URL")
        api_key = settings.QDRANT_API_KEY or os.getenv("QDRANT_API_KEY")

        try:
            if url:
                print(f"[QDRANT] Connecting to Cloud Qdrant endpoint: {url}")
                self.client = QdrantClient(url=url, api_key=api_key)
            else:
                # Ensure local data path exists
                local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
                os.makedirs(local_dir, exist_ok=True)
                local_db_path = os.path.join(local_dir, "qdrant_db")
                print(f"[QDRANT] No Cloud settings. Using local Qdrant DB path: {local_db_path}")
                self.client = QdrantClient(path=local_db_path)
        except Exception as e:
            print(f"[QDRANT INIT ERROR] Failed to initialize Qdrant client: {e}")
            self.client = None

    def ensure_collection(self, collection_name: str, vector_size: int = 384):
        """
        Ensures a collection exists in Qdrant with the correct vector size and Cosine distance metric.
        Caches checked collections to avoid making redundant collection_exists network calls.
        """
        if not self.client:
            return
        if collection_name in self.known_collections:
            return
        try:
            exists = False
            try:
                exists = self.client.collection_exists(collection_name)
            except AttributeError:
                # Fallback check for older qdrant-client versions
                collections = self.client.get_collections().collections
                exists = any(c.name == collection_name for c in collections)

            if not exists:
                print(f"[QDRANT] Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
            self.known_collections.add(collection_name)
        except Exception as e:
            print(f"[QDRANT ERROR] Failed to ensure collection {collection_name}: {e}")

    def upsert_opportunity(self, collection_name: str, item_id: int, vector: List[float], payload: Optional[Dict[str, Any]] = None):
        """
        Upserts a single record's vector and metadata payload to a Qdrant collection.
        """
        if not self.client or not vector:
            return
        try:
            self.ensure_collection(collection_name, len(vector))
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    qmodels.PointStruct(
                        id=item_id,
                        vector=vector,
                        payload=payload or {}
                    )
                ]
            )
        except Exception as e:
            print(f"[QDRANT ERROR] Failed to upsert point {item_id} in {collection_name}: {e}")

    def upsert_opportunity_batch(self, collection_name: str, items: List[Dict[str, Any]], vector_size: int = 384):
        """
        Upserts a batch of points to a Qdrant collection in a single roundtrip.
        Each item dict should look like: {"id": int, "vector": List[float], "payload": Dict}
        """
        if not self.client or not items:
            return
        try:
            self.ensure_collection(collection_name, vector_size)
            points = []
            for item in items:
                points.append(
                    qmodels.PointStruct(
                        id=item["id"],
                        vector=item["vector"],
                        payload=item.get("payload") or {}
                    )
                )
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
        except Exception as e:
            print(f"[QDRANT ERROR] Failed to upsert batch in {collection_name}: {e}")

    def search_opportunities(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        limit: int = 12, 
        ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches a Qdrant collection for similar vectors.
        If a list of IDs is provided, the search is strictly filtered to only search within those IDs.
        """
        if not self.client or not query_vector:
            return []
        try:
            self.ensure_collection(collection_name, len(query_vector))
            
            query_filter = None
            if ids is not None:
                if not ids:
                    return []  # Restricting search to empty list yields no results
                query_filter = qmodels.Filter(
                    must=[
                        qmodels.HasIdCondition(has_id=ids)
                    ]
                )

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            return [{"id": r.id, "score": r.score} for r in results]
        except Exception as e:
            print(f"[QDRANT ERROR] Search failed in collection {collection_name}: {e}")
            return []

# Singleton instance
qdrant_service = QdrantService()
