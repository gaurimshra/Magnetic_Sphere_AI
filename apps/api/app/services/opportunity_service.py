from uuid import uuid4

from app.agents.knowledge_graph_agent import KnowledgeGraphAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.scoring_agent import ScoringAgent
from app.agents.signal_agents import (
    CompetitorSentimentAgent,
    FundingAgent,
    HiringAgent,
    NewsAPIAgent,
    NewsAgent,
    RSSNewsAgent,
    SocialAgent,
    TechStackAgent,
    load_target_companies,
)
from app.agents.workflow_agent import WorkflowAgent
from app.core.config import get_settings
from app.integrations.gemini_client import GeminiClient
from app.integrations.hubspot_client import HubSpotClient
from app.integrations.neo4j_graph import Neo4jGraph
from app.integrations.qdrant_memory import QdrantMemory
from app.integrations.slack_client import SlackClient
from app.models.domain import AgentRun, Opportunity, OutreachEmail, OutreachRequest, Signal, Trend


class OpportunityService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        gemini_client = GeminiClient(settings)
        slack_client = SlackClient(settings)
        hubspot_client = HubSpotClient(settings)
        qdrant_memory = QdrantMemory(settings)
        neo4j_graph = Neo4jGraph(settings)
        self.signal_agents = [
            FundingAgent(),
            HiringAgent(),
            NewsAgent(),
            RSSNewsAgent(settings),
            NewsAPIAgent(settings),
            SocialAgent(),
            TechStackAgent(),
            CompetitorSentimentAgent(),
        ]
        self.retrieval_agent = RetrievalAgent(memory=qdrant_memory)
        self.graph_agent = KnowledgeGraphAgent(graph=neo4j_graph)
        self.reasoning_agent = ReasoningAgent(gemini_client=gemini_client)
        self.scoring_agent = ScoringAgent()
        self.workflow_agent = WorkflowAgent(
            gemini_client=gemini_client,
            slack_client=slack_client,
            hubspot_client=hubspot_client,
        )
        self.monitoring_agent = MonitoringAgent()

    def run_agents(
        self,
        execute_workflows: bool = True,
        use_live_reasoning: bool = True,
        use_live_stores: bool = True,
    ) -> AgentRun:
        companies = load_target_companies(self.settings)
        self.retrieval_agent.index_companies(companies, use_live_store=use_live_stores)
        all_signals: list[Signal] = []
        for agent in self.signal_agents:
            all_signals.extend(agent.run(companies))

        opportunities: list[Opportunity] = []
        for company in companies:
            company_signals = [signal for signal in all_signals if signal.company_id == company.id]
            similar = self.retrieval_agent.find_similar(company, companies, use_live_store=use_live_stores)
            analysis = self.reasoning_agent.analyze(
                company,
                company_signals,
                similar,
                use_live_ai=use_live_reasoning,
            )
            score, confidence, probability = self.scoring_agent.score(company_signals, analysis["reasons"])
            graph_nodes, graph_edges = self.graph_agent.build_graph(company, use_live_store=use_live_stores)
            actions = self.workflow_agent.build_actions(company, score)
            opportunity = Opportunity(
                id=f"opp-{company.id}",
                company=company,
                opportunity_type=analysis["opportunity_type"],
                score=score,
                confidence=confidence,
                probability=probability,
                summary=analysis["summary"],
                recommended_action="Send personalized outreach within 48 hours."
                if score >= 80
                else "Monitor for another strong buying signal.",
                reasons=analysis["reasons"],
                risks=analysis["risks"],
                signals=sorted(company_signals, key=lambda signal: signal.occurred_at, reverse=True),
                workflow_actions=actions,
                graph_nodes=graph_nodes,
                graph_edges=graph_edges,
            )
            if execute_workflows:
                opportunity = opportunity.model_copy(
                    update={"workflow_actions": self.workflow_agent.execute_actions(opportunity)}
                )
            opportunities.append(opportunity)

        return AgentRun(
            run_id=str(uuid4()),
            status="completed",
            opportunities=sorted(opportunities, key=lambda opportunity: opportunity.score, reverse=True),
            trends=self.trends(),
        )

    def list_opportunities(self) -> list[Opportunity]:
        return self.run_agents(
            execute_workflows=False,
            use_live_reasoning=False,
            use_live_stores=False,
        ).opportunities

    def get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        return next((opportunity for opportunity in self.list_opportunities() if opportunity.id == opportunity_id), None)

    def trends(self) -> list[Trend]:
        return self.monitoring_agent.trends()

    def generate_outreach(self, request: OutreachRequest) -> OutreachEmail:
        opportunity = self.get_opportunity(request.opportunity_id)
        if opportunity is None:
            raise ValueError("Opportunity not found")
        subject, body = self.workflow_agent.generate_email(
            opportunity,
            sender_name=request.sender_name,
            product_name=request.product_name,
        )
        return OutreachEmail(subject=subject, body=body)
