from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SignalType(StrEnum):
    funding = "Funding"
    hiring = "Hiring"
    news = "News"
    social = "Social"
    tech_stack = "Tech Stack"
    competitor = "Competitor"


class Signal(BaseModel):
    id: str
    company_id: str
    type: SignalType
    title: str
    summary: str
    source: str
    strength: int = Field(ge=0, le=100)
    occurred_at: str


class Company(BaseModel):
    id: str
    name: str
    industry: str
    region: str
    stage: str
    description: str
    website: str
    competitors: list[str]
    technologies: list[str]


class ScoreReason(BaseModel):
    label: str
    impact: int = Field(ge=0, le=100)
    evidence: str


class WorkflowAction(BaseModel):
    type: str
    title: str
    payload: str
    status: str = "ready"


class WorkflowActionRequest(BaseModel):
    action: str
    company: str


class WorkflowActionResult(BaseModel):
    action: str
    status: str
    detail: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class Opportunity(BaseModel):
    id: str
    company: Company
    opportunity_type: str
    score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    probability: int = Field(ge=0, le=100)
    summary: str
    recommended_action: str
    reasons: list[ScoreReason]
    risks: list[str]
    signals: list[Signal]
    workflow_actions: list[WorkflowAction]
    graph_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]


class Trend(BaseModel):
    id: str
    label: str
    direction: str
    score: int
    change: int


class OutreachRequest(BaseModel):
    opportunity_id: str
    sender_name: str = "Avery from MagneticSphere"
    product_name: str = "Cloud AI Platform"


class OutreachEmail(BaseModel):
    subject: str
    body: str


class CompanyReportRequest(BaseModel):
    query: str
    force_refresh: bool = False


class FundingEvent(BaseModel):
    title: str
    summary: str
    source: str
    occurred_at: str


class NewsItem(BaseModel):
    title: str
    summary: str
    source: str
    occurred_at: str


class HiringSignal(BaseModel):
    title: str
    summary: str
    source: str
    strength: int = Field(ge=0, le=100)
    occurred_at: str


class CompanyIntelligence(BaseModel):
    company_name: str
    domain: str
    industry: str
    headquarters: str
    employees: str
    funding: list[FundingEvent]
    investors: list[str]
    competitors: list[str]
    technologies: list[str]
    recent_news: list[NewsItem]
    hiring_signals: list[HiringSignal]
    overview: str


class CompanyAnalysis(BaseModel):
    executive_summary: str
    swot_analysis: list[str]
    growth_signals: list[str]
    risks: list[str]
    competitive_landscape: list[str]
    opportunities: list[str]
    ai_recommendations: list[str]


class TimelineEvent(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    category: str
    occurred_at: str


class AgentStep(BaseModel):
    id: str
    name: str
    purpose: str
    status: str = "pending"
    input_summary: str = ""
    output_summary: str = ""
    duration_ms: int = 0


class RawCompanySignal(BaseModel):
    id: str
    company_key: str
    company_name: str
    domain: str
    provider: str
    signal_type: str
    source: str
    title: str
    url: str = ""
    raw_snippet: str
    raw_payload: dict[str, Any] = {}
    extracted_entities: list[str] = []
    confidence: int = Field(ge=0, le=100)
    occurred_at: str
    captured_at: str
    dedup_key: str
    duplicate_of: str | None = None


class ReportHistoryItem(BaseModel):
    id: str
    company_name: str
    domain: str
    generated_at: str
    opportunity_score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    score_delta: int = 0
    timeline_delta: int = 0
    alert: str = ""


class CompanyReport(BaseModel):
    id: str
    company: CompanyIntelligence
    analysis: CompanyAnalysis
    graph_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]
    timeline: list[TimelineEvent]
    opportunity_score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    generated_at: str
    cached: bool = False
    agent_steps: list[AgentStep] = []
    score_delta: int = 0
    timeline_delta: int = 0
    score_alert: str = ""


class AgentRun(BaseModel):
    run_id: str
    status: str
    opportunities: list[Opportunity]
    trends: list[Trend]
