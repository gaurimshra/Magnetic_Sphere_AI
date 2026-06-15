from app.models.domain import Company, GraphEdge, GraphNode, Signal, SignalType


COMPANIES = [
    Company(
        id="neurotech-ai",
        name="NeuroTech AI",
        industry="Healthcare AI",
        region="United States",
        stage="Series A",
        description="Clinical workflow automation startup building AI copilots for radiology teams.",
        website="https://example.com/neurotech",
        competitors=["MedAssist Cloud", "ClinicMind"],
        technologies=["AWS", "Kubernetes", "Python", "React"],
    ),
    Company(
        id="vision-labs",
        name="Vision Labs",
        industry="Computer Vision",
        region="Germany",
        stage="Seed",
        description="Manufacturing quality inspection company using multimodal vision models.",
        website="https://example.com/vision-labs",
        competitors=["InspectIQ", "FactorySight"],
        technologies=["Azure", "Docker", "PyTorch", "Next.js"],
    ),
    Company(
        id="finedge",
        name="FinEdge",
        industry="FinTech",
        region="Singapore",
        stage="Growth",
        description="Risk analytics platform modernizing underwriting for SME lenders.",
        website="https://example.com/finedge",
        competitors=["RiskPilot", "LedgerLens"],
        technologies=["GCP", "Go", "Kafka", "PostgreSQL"],
    ),
]


SIGNALS = [
    Signal(
        id="sig-neuro-funding",
        company_id="neurotech-ai",
        type=SignalType.funding,
        title="Raised $20M Series A",
        summary="New funding round led by healthcare-focused investors to expand AI product development.",
        source="Funding announcement",
        strength=96,
        occurred_at="2026-05-24",
    ),
    Signal(
        id="sig-neuro-hiring",
        company_id="neurotech-ai",
        type=SignalType.hiring,
        title="Hiring ML engineers and DevOps leads",
        summary="Career page added eight AI infrastructure roles in two weeks.",
        source="Careers page",
        strength=89,
        occurred_at="2026-05-28",
    ),
    Signal(
        id="sig-neuro-social",
        company_id="neurotech-ai",
        type=SignalType.social,
        title="CEO discusses scaling clinical AI",
        summary="Leadership posts show urgency around reliable model deployment and governance.",
        source="LinkedIn",
        strength=82,
        occurred_at="2026-06-02",
    ),
    Signal(
        id="sig-neuro-tech",
        company_id="neurotech-ai",
        type=SignalType.tech_stack,
        title="Kubernetes and AWS stack detected",
        summary="Cloud-native stack indicates fit for AI infrastructure automation.",
        source="BuiltWith demo adapter",
        strength=78,
        occurred_at="2026-06-05",
    ),
    Signal(
        id="sig-vision-hiring",
        company_id="vision-labs",
        type=SignalType.hiring,
        title="Hiring edge AI deployment team",
        summary="Open roles mention production computer vision and MLOps ownership.",
        source="Job portals",
        strength=86,
        occurred_at="2026-06-01",
    ),
    Signal(
        id="sig-vision-news",
        company_id="vision-labs",
        type=SignalType.news,
        title="Launched factory defect detection pilot",
        summary="Public pilot with an automotive supplier suggests near-term expansion.",
        source="Industry news",
        strength=81,
        occurred_at="2026-05-30",
    ),
    Signal(
        id="sig-finedge-competitor",
        company_id="finedge",
        type=SignalType.competitor,
        title="Users complain about RiskPilot pricing",
        summary="Public forum threads show dissatisfaction with a competing analytics vendor.",
        source="Reddit demo adapter",
        strength=74,
        occurred_at="2026-06-03",
    ),
    Signal(
        id="sig-finedge-news",
        company_id="finedge",
        type=SignalType.news,
        title="Expanding underwriting automation product",
        summary="Product update focuses on faster model-assisted lender workflows.",
        source="Company blog",
        strength=77,
        occurred_at="2026-05-26",
    ),
]


def graph_for_company(company: Company) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes = [
        GraphNode(id=company.id, label=company.name, type="company"),
        GraphNode(id=f"{company.id}-funding", label=company.stage, type="funding"),
        GraphNode(id=f"{company.id}-hiring", label="Hiring Signals", type="hiring"),
        GraphNode(id=f"{company.id}-tech", label=", ".join(company.technologies[:2]), type="technology"),
    ]
    edges = [
        GraphEdge(id=f"{company.id}-e1", source=company.id, target=f"{company.id}-funding", label="raised"),
        GraphEdge(id=f"{company.id}-e2", source=company.id, target=f"{company.id}-hiring", label="expanding"),
        GraphEdge(id=f"{company.id}-e3", source=company.id, target=f"{company.id}-tech", label="uses"),
    ]
    for competitor in company.competitors[:2]:
        competitor_id = f"{company.id}-{competitor.lower().replace(' ', '-')}"
        nodes.append(GraphNode(id=competitor_id, label=competitor, type="competitor"))
        edges.append(GraphEdge(id=f"{company.id}-{competitor_id}", source=company.id, target=competitor_id, label="competes"))
    return nodes, edges

