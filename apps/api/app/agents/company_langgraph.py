from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, StateGraph

from app.models.domain import (
    AgentStep,
    CompanyAnalysis,
    CompanyIntelligence,
    CompanyReport,
    FundingEvent,
    GraphEdge,
    GraphNode,
    HiringSignal,
    NewsItem,
    TimelineEvent,
)


AGENT_ARCHITECTURE: list[AgentStep] = [
    AgentStep(
        id="signal_agent",
        name="Signal Agent",
        purpose="Resolve the target company, check cached reports, and prepare the signal collection state.",
    ),
    AgentStep(
        id="news_agent",
        name="News Agent",
        purpose="Collect and summarize articles, blogs, press releases, funding news, and RSS/NewsAPI signals.",
    ),
    AgentStep(
        id="hiring_agent",
        name="Hiring Agent",
        purpose="Detect hiring and expansion signals from live sources and derived public signals.",
    ),
    AgentStep(
        id="social_agent",
        name="Social Sentiment Agent",
        purpose="Analyze public conversation and competitor-pain signals from available social/news text.",
    ),
    AgentStep(
        id="tech_stack_agent",
        name="Tech Stack Agent",
        purpose="Identify technologies already used from BuiltWith-like signals, GitHub-like text, and public mentions.",
    ),
    AgentStep(
        id="retrieval_agent",
        name="Retrieval Agent",
        purpose="Store and retrieve similar-company memory through Qdrant when available.",
    ),
    AgentStep(
        id="graph_agent",
        name="Knowledge Graph Agent",
        purpose="Build company relationships between investors, competitors, technologies, news, and hiring.",
    ),
    AgentStep(
        id="reasoning_agent",
        name="Reasoning Agent",
        purpose="Use Gemini reasoning over collected evidence to produce SWOT, risks, opportunities, and recommendations.",
    ),
    AgentStep(
        id="scoring_agent",
        name="Opportunity Scoring Agent",
        purpose="Generate explainable opportunity and confidence scores from signals and reasoning output.",
    ),
    AgentStep(
        id="action_agent",
        name="Workflow Agent",
        purpose="Persist the report and prepare downstream workflow actions such as outreach, Slack, and CRM updates.",
    ),
    AgentStep(
        id="monitoring_agent",
        name="Monitoring Agent",
        purpose="Track cache state, generated timeline, and ongoing report freshness for future refreshes.",
    ),
]


class CompanyGraphState(TypedDict):
    query: str
    force_refresh: bool
    resolved: NotRequired[dict[str, str]]
    cache_key: NotRequired[str]
    cached_report: NotRequired[CompanyReport | None]
    overview: NotRequired[str]
    news: NotRequired[list[NewsItem]]
    funding: NotRequired[list[FundingEvent]]
    hiring: NotRequired[list[HiringSignal]]
    social_signals: NotRequired[list[str]]
    technologies: NotRequired[list[str]]
    company: NotRequired[CompanyIntelligence]
    graph_nodes: NotRequired[list[GraphNode]]
    graph_edges: NotRequired[list[GraphEdge]]
    timeline: NotRequired[list[TimelineEvent]]
    analysis: NotRequired[Any]
    opportunity_score: NotRequired[int]
    confidence: NotRequired[int]
    report: NotRequired[CompanyReport]
    agent_steps: list[AgentStep]


def company_agent_architecture() -> list[AgentStep]:
    return [step.model_copy() for step in AGENT_ARCHITECTURE]


def run_company_agent_graph(service: Any, query: str, force_refresh: bool = False) -> CompanyReport:
    service._begin_signal_capture()
    workflow = StateGraph(CompanyGraphState)
    workflow.add_node("signal_agent", _wrap("signal_agent", _signal_agent(service)))
    workflow.add_node("news_agent", _wrap("news_agent", _news_agent(service)))
    workflow.add_node("hiring_agent", _wrap("hiring_agent", _hiring_agent(service)))
    workflow.add_node("social_agent", _wrap("social_agent", _social_agent()))
    workflow.add_node("tech_stack_agent", _wrap("tech_stack_agent", _tech_stack_agent(service)))
    workflow.add_node("retrieval_agent", _wrap("retrieval_agent", _retrieval_agent(service)))
    workflow.add_node("graph_agent", _wrap("graph_agent", _graph_agent(service)))
    workflow.add_node("reasoning_agent", _wrap("reasoning_agent", _reasoning_agent(service)))
    workflow.add_node("scoring_agent", _wrap("scoring_agent", _scoring_agent(service)))
    workflow.add_node("action_agent", _wrap("action_agent", _action_agent(service)))
    workflow.add_node("monitoring_agent", _wrap("monitoring_agent", _monitoring_agent()))

    workflow.set_entry_point("signal_agent")
    workflow.add_conditional_edges(
        "signal_agent",
        _route_after_signal,
        {"cached": "monitoring_agent", "live": "news_agent"},
    )
    workflow.add_edge("news_agent", "hiring_agent")
    workflow.add_edge("hiring_agent", "social_agent")
    workflow.add_edge("social_agent", "tech_stack_agent")
    workflow.add_edge("tech_stack_agent", "retrieval_agent")
    workflow.add_edge("retrieval_agent", "graph_agent")
    workflow.add_edge("graph_agent", "reasoning_agent")
    workflow.add_edge("reasoning_agent", "scoring_agent")
    workflow.add_edge("scoring_agent", "action_agent")
    workflow.add_edge("action_agent", "monitoring_agent")
    workflow.add_edge("monitoring_agent", END)

    graph = workflow.compile()
    final_state = graph.invoke(
        {
            "query": query,
            "force_refresh": force_refresh,
            "agent_steps": company_agent_architecture(),
        }
    )
    if final_state.get("cache_key") and final_state.get("report"):
        service.repository.save(final_state["cache_key"], final_state["report"])
        service._save_captured_signals()
    return final_state["report"]


def _route_after_signal(state: CompanyGraphState) -> str:
    return "cached" if state.get("cached_report") else "live"


def _wrap(agent_id: str, fn: Any) -> Any:
    def wrapped(state: CompanyGraphState) -> CompanyGraphState:
        started = perf_counter()
        try:
            next_state = fn(state)
            status = "completed"
            output_summary = _output_summary(agent_id, next_state)
        except Exception as exc:
            next_state = state.copy()
            status = "failed"
            output_summary = str(exc)[:240]
        duration_ms = round((perf_counter() - started) * 1000)
        next_state["agent_steps"] = _update_step(
            next_state["agent_steps"],
            agent_id,
            status=status,
            input_summary=_input_summary(agent_id, state),
            output_summary=output_summary,
            duration_ms=duration_ms,
        )
        if "report" in next_state:
            next_state["report"] = next_state["report"].model_copy(update={"agent_steps": next_state["agent_steps"]})
        return next_state

    return wrapped


def _signal_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        resolved = service.resolve_company(state["query"])
        cache_key = service._cache_key(resolved["domain"])
        cached = None if state["force_refresh"] else service.repository.get_latest(cache_key)
        next_state = state.copy()
        next_state.update({"resolved": resolved, "cache_key": cache_key, "cached_report": cached})
        if cached:
            next_state["report"] = cached.model_copy(update={"agent_steps": next_state["agent_steps"]})
        return next_state

    return node


def _news_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        resolved = state["resolved"]
        news = service._search_news(resolved["name"], resolved["domain"])
        overview = service._fetch_overview(resolved["name"])
        funding = service._funding_events(news)
        next_state = state.copy()
        next_state.update({"news": news, "overview": overview, "funding": funding})
        return next_state

    return node


def _hiring_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        next_state = state.copy()
        next_state["hiring"] = service._hiring_signals(state["resolved"]["name"], state.get("news", []))
        return next_state

    return node


def _social_agent() -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        signals: list[str] = []
        for item in state.get("news", []):
            text = f"{item.title} {item.summary}".lower()
            if any(keyword in text for keyword in ("complaint", "pricing", "popular", "adoption", "partnership")):
                signals.append(item.title)
        next_state = state.copy()
        next_state["social_signals"] = signals[:8]
        return next_state

    return node


def _tech_stack_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        next_state = state.copy()
        next_state["technologies"] = service._detect_technologies(
            state.get("news", []),
            state.get("overview", ""),
            state["resolved"]["name"],
            state["resolved"]["domain"],
        )
        return next_state

    return node


def _retrieval_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        resolved = state["resolved"]
        analysis_seed = service._fallback_analysis(
            resolved,
            state.get("overview", ""),
            state.get("news", []),
            state.get("hiring", []),
            state.get("funding", []),
            state.get("technologies", []),
        )
        company = service._company_from_parts(resolved, state, analysis_seed)
        service._store_memory(company)
        next_state = state.copy()
        next_state["company"] = company
        return next_state

    return node


def _graph_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        company = state["company"]
        nodes, edges = service._build_graph(company)
        service._store_graph(company)
        next_state = state.copy()
        next_state.update(
            {
                "graph_nodes": nodes,
                "graph_edges": edges,
                "timeline": service._timeline(company),
            }
        )
        return next_state

    return node


def _reasoning_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        analysis = service._analyze(
            state["resolved"],
            state.get("overview", ""),
            state.get("news", []),
            state.get("hiring", []),
            state.get("funding", []),
            state.get("technologies", []),
        )
        company = service._company_from_parts(state["resolved"], state, analysis)
        next_state = state.copy()
        next_state.update({"analysis": analysis, "company": company})
        return next_state

    return node


def _scoring_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        score, confidence = service._score(state["company"], state["analysis"])
        next_state = state.copy()
        next_state.update({"opportunity_score": score, "confidence": confidence})
        return next_state

    return node


def _action_agent(service: Any) -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        company = state["company"]
        analysis = state["analysis"]
        report = CompanyReport(
            id=service._report_id(company.domain),
            company=company,
            analysis=CompanyAnalysis(
                executive_summary=analysis.executive_summary,
                swot_analysis=analysis.swot_analysis[:8],
                growth_signals=analysis.growth_signals[:8],
                risks=analysis.risks[:8],
                competitive_landscape=analysis.competitive_landscape[:8],
                opportunities=analysis.opportunities[:8],
                ai_recommendations=analysis.ai_recommendations[:8],
            ),
            graph_nodes=state.get("graph_nodes", []),
            graph_edges=state.get("graph_edges", []),
            timeline=state.get("timeline", []),
            opportunity_score=state.get("opportunity_score", 0),
            confidence=state.get("confidence", 0),
            generated_at=datetime.now(UTC).isoformat(),
            agent_steps=state["agent_steps"],
        )
        report = service._apply_report_deltas(report, state["cache_key"])
        service.repository.save(state["cache_key"], report)
        service._save_captured_signals()
        next_state = state.copy()
        next_state["report"] = report
        return next_state

    return node


def _monitoring_agent() -> Any:
    def node(state: CompanyGraphState) -> CompanyGraphState:
        report = state["report"].model_copy(update={"agent_steps": state["agent_steps"]})
        next_state = state.copy()
        next_state["report"] = report
        return next_state

    return node


def _update_step(
    steps: list[AgentStep],
    agent_id: str,
    status: str,
    input_summary: str,
    output_summary: str,
    duration_ms: int,
) -> list[AgentStep]:
    updated: list[AgentStep] = []
    for step in steps:
        if step.id == agent_id:
            updated.append(
                step.model_copy(
                    update={
                        "status": status,
                        "input_summary": input_summary,
                        "output_summary": output_summary,
                        "duration_ms": duration_ms,
                    }
                )
            )
        else:
            updated.append(step)
    return updated


def _input_summary(agent_id: str, state: CompanyGraphState) -> str:
    if agent_id == "signal_agent":
        return f"query={state['query']}"
    if "resolved" in state:
        return f"company={state['resolved']['name']}"
    return "waiting for company context"


def _output_summary(agent_id: str, state: CompanyGraphState) -> str:
    if agent_id == "signal_agent":
        return "cache hit" if state.get("cached_report") else f"resolved {state['resolved']['domain']}"
    if agent_id == "news_agent":
        return f"{len(state.get('news', []))} news items, {len(state.get('funding', []))} funding/deal signals"
    if agent_id == "hiring_agent":
        return f"{len(state.get('hiring', []))} hiring signals"
    if agent_id == "social_agent":
        return f"{len(state.get('social_signals', []))} sentiment signals"
    if agent_id == "tech_stack_agent":
        return ", ".join(state.get("technologies", [])[:5]) or "no technologies detected"
    if agent_id == "retrieval_agent":
        return "company memory written or skipped by adapter"
    if agent_id == "graph_agent":
        return f"{len(state.get('graph_nodes', []))} nodes, {len(state.get('graph_edges', []))} edges"
    if agent_id == "reasoning_agent":
        return state.get("analysis").executive_summary[:180] if state.get("analysis") else "no analysis"
    if agent_id == "scoring_agent":
        return f"score={state.get('opportunity_score', 0)}, confidence={state.get('confidence', 0)}"
    if agent_id == "action_agent":
        return "report persisted and workflow actions prepared"
    if agent_id == "monitoring_agent":
        return "report freshness and timeline ready"
    return "completed"
