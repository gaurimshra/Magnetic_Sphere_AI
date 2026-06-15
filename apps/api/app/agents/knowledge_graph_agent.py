from app.models.domain import Company, GraphEdge, GraphNode
from app.integrations.neo4j_graph import Neo4jGraph
from app.repositories.demo_data import graph_for_company


class KnowledgeGraphAgent:
    """Demo GraphRAG adapter.

    Replace `build_graph` with Neo4j writes and graph queries in production.
    """

    def __init__(self, graph: Neo4jGraph | None = None) -> None:
        self.graph = graph

    def build_graph(
        self,
        company: Company,
        use_live_store: bool = True,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        if use_live_store and self.graph:
            self.graph.upsert_company(company)
            nodes, edges = self.graph.graph_for_company(company)
            if nodes and edges:
                return nodes, edges

        return graph_for_company(company)
