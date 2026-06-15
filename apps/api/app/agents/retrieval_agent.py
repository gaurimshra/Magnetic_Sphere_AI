from app.models.domain import Company
from app.integrations.qdrant_memory import QdrantMemory


class RetrievalAgent:
    """Demo semantic retrieval adapter.

    Replace this with Qdrant collection search when embeddings are available.
    """

    def __init__(self, memory: QdrantMemory | None = None) -> None:
        self.memory = memory

    def index_companies(self, companies: list[Company], use_live_store: bool = True) -> None:
        if use_live_store and self.memory:
            self.memory.upsert_companies(companies)

    def find_similar(
        self,
        company: Company,
        candidates: list[Company],
        use_live_store: bool = True,
    ) -> list[str]:
        if use_live_store and self.memory:
            live_matches = self.memory.find_similar(company)
            if live_matches:
                return live_matches

        matches: list[str] = []
        company_terms = {company.industry.lower(), *[tech.lower() for tech in company.technologies]}
        for candidate in candidates:
            if candidate.id == company.id:
                continue
            candidate_terms = {candidate.industry.lower(), *[tech.lower() for tech in candidate.technologies]}
            if company_terms.intersection(candidate_terms):
                matches.append(candidate.name)
        return matches[:3]
