from uuid import NAMESPACE_URL, uuid5

from app.core.config import Settings
from app.integrations.vectorizer import HashVectorizer
from app.models.domain import Company


class QdrantMemory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.vectorizer = HashVectorizer(settings.vector_size)

    @property
    def enabled(self) -> bool:
        return bool(self.settings.enable_live_integrations and self.settings.qdrant_url)

    def upsert_companies(self, companies: list[Company]) -> None:
        if not self.enabled:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, PointStruct, VectorParams
        except ImportError:
            return

        try:
            client = QdrantClient(url=self.settings.qdrant_url, api_key=self.settings.qdrant_api_key, timeout=2)
            if not client.collection_exists(self.settings.qdrant_collection):
                client.create_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config=VectorParams(size=self.settings.vector_size, distance=Distance.COSINE),
                )
            points = [
                PointStruct(
                    id=str(uuid5(NAMESPACE_URL, company.id)),
                    vector=self.vectorizer.embed(self._company_text(company)),
                    payload={
                        "company_id": company.id,
                        "name": company.name,
                        "industry": company.industry,
                        "stage": company.stage,
                    },
                )
                for company in companies
            ]
            client.upsert(collection_name=self.settings.qdrant_collection, wait=True, points=points)
        except Exception:
            return

    def find_similar(self, company: Company, limit: int = 3) -> list[str]:
        if not self.enabled:
            return []

        try:
            from qdrant_client import QdrantClient
        except ImportError:
            return []

        try:
            client = QdrantClient(url=self.settings.qdrant_url, api_key=self.settings.qdrant_api_key, timeout=2)
            query_vector = self.vectorizer.embed(self._company_text(company))
            results = client.query_points(
                collection_name=self.settings.qdrant_collection,
                query=query_vector,
                limit=limit + 1,
            ).points
            names = []
            for result in results:
                payload = result.payload or {}
                if payload.get("company_id") != company.id and payload.get("name"):
                    names.append(str(payload["name"]))
            return names[:limit]
        except Exception:
            return []

    def _company_text(self, company: Company) -> str:
        return " ".join(
            [
                company.name,
                company.industry,
                company.stage,
                company.description,
                " ".join(company.technologies),
                " ".join(company.competitors),
            ]
        )
