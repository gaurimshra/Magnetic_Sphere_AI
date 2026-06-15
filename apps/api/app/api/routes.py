from fastapi import APIRouter, HTTPException

from app.models.domain import (
    AgentRun,
    AgentStep,
    CompanyReport,
    CompanyReportRequest,
    GraphEdge,
    GraphNode,
    Opportunity,
    OutreachEmail,
    OutreachRequest,
    RawCompanySignal,
    ReportHistoryItem,
    TimelineEvent,
    Trend,
    WorkflowActionRequest,
    WorkflowActionResult,
)
from app.agents.company_langgraph import company_agent_architecture
from app.services.company_intelligence_service import CompanyIntelligenceService
from app.services.integration_status import IntegrationStatus, integration_status
from app.services.opportunity_service import OpportunityService

router = APIRouter()
service = OpportunityService()
company_service = CompanyIntelligenceService()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "magneticsphere-api"}


@router.get("/integrations/status")
def get_integration_status() -> dict[str, IntegrationStatus]:
    return integration_status()


@router.get("/agents/architecture", response_model=list[AgentStep])
def get_agent_architecture() -> list[AgentStep]:
    return company_agent_architecture()


@router.post("/company/report", response_model=CompanyReport)
def company_report(request: CompanyReportRequest) -> CompanyReport:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Company query is required")
    return company_service.generate_report(request.query, force_refresh=request.force_refresh)


@router.get("/company/{company}", response_model=CompanyReport)
def get_company(company: str) -> CompanyReport:
    report = company_service.get_company(company)
    if report is None:
        report = company_service.generate_report(company)
    return report


@router.get("/company/{company}/graph", response_model=dict[str, list[GraphNode] | list[GraphEdge]])
def get_company_graph(company: str) -> dict[str, list[GraphNode] | list[GraphEdge]]:
    report = company_service.get_company(company)
    if report is None:
        report = company_service.generate_report(company)
    return {"nodes": report.graph_nodes, "edges": report.graph_edges}


@router.get("/company/{company}/timeline", response_model=list[TimelineEvent])
def get_company_timeline(company: str) -> list[TimelineEvent]:
    report = company_service.get_company(company)
    if report is None:
        report = company_service.generate_report(company)
    return report.timeline


@router.get("/company/{company}/agents", response_model=list[AgentStep])
def get_company_agents(company: str) -> list[AgentStep]:
    report = company_service.get_company(company)
    if report is None:
        report = company_service.generate_report(company)
    return report.agent_steps


@router.get("/company/{company}/history", response_model=list[ReportHistoryItem])
def get_company_history(company: str, limit: int = 20) -> list[ReportHistoryItem]:
    return company_service.history(company, limit=limit)


@router.get("/company/{company}/signals", response_model=list[RawCompanySignal])
def get_company_signals(company: str, limit: int = 50) -> list[RawCompanySignal]:
    return company_service.signals(company, limit=limit)


@router.get("/reports/history", response_model=list[ReportHistoryItem])
def get_report_history(limit: int = 20) -> list[ReportHistoryItem]:
    return company_service.history(limit=limit)


@router.post("/company/action", response_model=WorkflowActionResult)
def execute_company_action(request: WorkflowActionRequest) -> WorkflowActionResult:
    if not request.company.strip():
        raise HTTPException(status_code=400, detail="Company is required")
    return company_service.execute_report_action(request.company, request.action)


@router.post("/agents/run", response_model=AgentRun)
def run_agents() -> AgentRun:
    return service.run_agents()


@router.get("/opportunities", response_model=list[Opportunity])
def list_opportunities() -> list[Opportunity]:
    return service.list_opportunities()


@router.get("/opportunities/{opportunity_id}", response_model=Opportunity)
def get_opportunity(opportunity_id: str) -> Opportunity:
    opportunity = service.get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.get("/trends", response_model=list[Trend])
def trends() -> list[Trend]:
    return service.trends()


@router.post("/outreach", response_model=OutreachEmail)
def outreach(request: OutreachRequest) -> OutreachEmail:
    try:
        return service.generate_outreach(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
