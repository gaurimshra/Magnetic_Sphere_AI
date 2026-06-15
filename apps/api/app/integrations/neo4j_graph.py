from app.core.config import Settings
from app.models.domain import Company, GraphEdge, GraphNode


class Neo4jGraph:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.enable_live_integrations
            and self.settings.neo4j_uri
            and self.settings.neo4j_username
            and self.settings.neo4j_password
        )

    def upsert_company(self, company: Company) -> None:
        if not self.enabled:
            return

        try:
            from neo4j import GraphDatabase
        except ImportError:
            return

        try:
            with GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_username, self.settings.neo4j_password),
                connection_timeout=2,
                max_transaction_retry_time=1,
            ) as driver:
                driver.execute_query(
                    """
                    MERGE (c:Company {id: $id})
                    SET c.name = $name,
                        c.industry = $industry,
                        c.stage = $stage,
                        c.region = $region,
                        c.description = $description
                    WITH c
                    UNWIND $technologies AS technology
                      MERGE (t:Technology {name: technology})
                      MERGE (c)-[:USES_TECHNOLOGY]->(t)
                    WITH c
                    UNWIND $competitors AS competitor
                      MERGE (p:Company {name: competitor})
                      MERGE (c)-[:COMPETES_WITH]->(p)
                    """,
                    id=company.id,
                    name=company.name,
                    industry=company.industry,
                    stage=company.stage,
                    region=company.region,
                    description=company.description,
                    technologies=company.technologies,
                    competitors=company.competitors,
                )
        except Exception:
            return

    def graph_for_company(self, company: Company) -> tuple[list[GraphNode], list[GraphEdge]]:
        if not self.enabled:
            return [], []

        try:
            from neo4j import GraphDatabase
        except ImportError:
            return [], []

        try:
            with GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_username, self.settings.neo4j_password),
                connection_timeout=2,
                max_transaction_retry_time=1,
            ) as driver:
                records, _, _ = driver.execute_query(
                    """
                    MATCH (c:Company {id: $id})-[r]-(n)
                    RETURN c.id AS company_id,
                           c.name AS company_name,
                           type(r) AS relationship,
                           coalesce(n.id, n.name) AS node_id,
                           coalesce(n.name, n.id) AS node_name,
                           labels(n)[0] AS node_type
                    LIMIT 25
                    """,
                    id=company.id,
                )
            nodes = [GraphNode(id=company.id, label=company.name, type="company")]
            edges: list[GraphEdge] = []
            seen = {company.id}
            for index, record in enumerate(records):
                node_id = str(record["node_id"])
                if node_id not in seen:
                    nodes.append(
                        GraphNode(
                            id=node_id,
                            label=str(record["node_name"]),
                            type=str(record["node_type"]).lower(),
                        )
                    )
                    seen.add(node_id)
                edges.append(
                    GraphEdge(
                        id=f"{company.id}-neo4j-{index}",
                        source=company.id,
                        target=node_id,
                        label=str(record["relationship"]).replace("_", " ").lower(),
                    )
                )
            return nodes, edges
        except Exception:
            return [], []
