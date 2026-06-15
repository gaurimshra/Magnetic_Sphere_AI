import json
import re
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.integrations.gemini_client import GeminiClient
from app.integrations.github_client import GitHubClient
from app.integrations.hubspot_client import HubSpotClient
from app.integrations.neo4j_graph import Neo4jGraph
from app.integrations.qdrant_memory import QdrantMemory
from app.integrations.slack_client import SlackClient
from app.models.domain import (
    Company,
    CompanyIntelligence,
    CompanyReport,
    FundingEvent,
    GraphEdge,
    GraphNode,
    HiringSignal,
    NewsItem,
    RawCompanySignal,
    ReportHistoryItem,
    TimelineEvent,
    WorkflowActionResult,
)
from app.repositories.company_report_repository import CompanyReportRepository


KNOWN_COMPANIES = {
    "openai": {"name": "OpenAI", "domain": "openai.com", "industry": "Artificial Intelligence"},
    "openai.com": {"name": "OpenAI", "domain": "openai.com", "industry": "Artificial Intelligence"},
    "anthropic": {"name": "Anthropic", "domain": "anthropic.com", "industry": "Artificial Intelligence"},
    "anthropic.com": {"name": "Anthropic", "domain": "anthropic.com", "industry": "Artificial Intelligence"},
    "perplexity": {"name": "Perplexity", "domain": "perplexity.ai", "industry": "AI Search"},
    "perplexity.ai": {"name": "Perplexity", "domain": "perplexity.ai", "industry": "AI Search"},
    "cursor": {"name": "Cursor", "domain": "cursor.com", "industry": "AI Developer Tools"},
    "cursor.com": {"name": "Cursor", "domain": "cursor.com", "industry": "AI Developer Tools"},
    "reddit": {"name": "Reddit", "domain": "reddit.com", "industry": "Social Media"},
    "reddit.com": {"name": "Reddit", "domain": "reddit.com", "industry": "Social Media"},
    "gemini": {"name": "Google Gemini", "domain": "gemini.google.com", "industry": "Artificial Intelligence"},
    "opencv": {"name": "OpenCV", "domain": "opencv.org", "industry": "Computer Vision"},
    "opencv.org": {"name": "OpenCV", "domain": "opencv.org", "industry": "Computer Vision"},
    "computer vision": {
        "name": "Computer Vision Market",
        "domain": "opencv.org",
        "industry": "Computer Vision",
    },
    "microsoft": {"name": "Microsoft", "domain": "microsoft.com", "industry": "Cloud and AI"},
    "microsoft.com": {"name": "Microsoft", "domain": "microsoft.com", "industry": "Cloud and AI"},
    "notion": {"name": "Notion", "domain": "notion.so", "industry": "Productivity Software"},
    "notion.so": {"name": "Notion", "domain": "notion.so", "industry": "Productivity Software"},
    "tesla": {"name": "Tesla", "domain": "tesla.com", "industry": "Electric Vehicles and Energy"},
    "tesla.com": {"name": "Tesla", "domain": "tesla.com", "industry": "Electric Vehicles and Energy"},
}

TECH_KEYWORDS = {
    "AWS": [" aws ", "amazon web services"],
    "Azure": [" azure ", "microsoft cloud"],
    "GCP": [" google cloud ", " gcp "],
    "Kubernetes": ["kubernetes", " k8s "],
    "React": ["react"],
    "Next.js": ["next.js", "nextjs"],
    "Python": ["python"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "OpenCV": ["opencv"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Docker": ["docker"],
}


class GeminiReport(BaseModel):
    executive_summary: str
    swot_analysis: list[str]
    growth_signals: list[str]
    risks: list[str]
    competitive_landscape: list[str]
    opportunities: list[str]
    ai_recommendations: list[str]
    competitors: list[str] = []
    technologies: list[str] = []
    investors: list[str] = []


class CompanyIntelligenceService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.repository = CompanyReportRepository(self.settings)
        self.gemini = GeminiClient(self.settings)
        self.github = GitHubClient(self.settings)
        self.memory = QdrantMemory(self.settings)
        self.graph = Neo4jGraph(self.settings)
        self.slack = SlackClient(self.settings)
        self.hubspot = HubSpotClient(self.settings)
        self._captured_signals: list[RawCompanySignal] = []

    def generate_report(self, query: str, force_refresh: bool = False) -> CompanyReport:
        from app.agents.company_langgraph import run_company_agent_graph

        return run_company_agent_graph(self, query, force_refresh=force_refresh)

    def get_company(self, company: str) -> CompanyReport | None:
        resolved = self.resolve_company(company)
        return self.repository.get_latest(self._cache_key(resolved["domain"]), max_age_hours=24 * 365)

    def history(self, company: str | None = None, limit: int = 20) -> list[ReportHistoryItem]:
        key = self._cache_key(self.resolve_company(company)["domain"]) if company else None
        return self.repository.history(key, limit=limit)

    def signals(self, company: str, limit: int = 50) -> list[RawCompanySignal]:
        resolved = self.resolve_company(company)
        return self.repository.list_signals(self._cache_key(resolved["domain"]), limit=limit)

    def execute_report_action(self, company: str, action: str) -> WorkflowActionResult:
        report = self.get_company(company)
        if report is None:
            report = self.generate_report(company)

        normalized = action.lower().strip()
        if normalized == "slack":
            if not self.slack.enabled:
                return WorkflowActionResult(
                    action=action,
                    status="skipped",
                    detail="Slack needs ENABLE_LIVE_INTEGRATIONS=true and either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN plus SLACK_CHANNEL_ID.",
                )
            sent = self.slack.send_alert(
                f"{report.company.company_name} score {report.opportunity_score} "
                f"({report.confidence}% confidence): {report.analysis.executive_summary[:220]}"
            )
            return WorkflowActionResult(
                action=action,
                status="sent" if sent else "failed",
                detail="Slack alert attempted. If this failed, check Slack scopes, channel access, or webhook validity.",
            )

        if normalized in {"hubspot_company", "hubspot_deal", "hubspot"}:
            if not self.hubspot.enabled:
                return WorkflowActionResult(action=action, status="skipped", detail="HubSpot is not configured or live integrations are disabled.")
            opportunity = self._report_to_opportunity(report)
            if normalized == "hubspot_company":
                updated, detail, record_id = self.hubspot.create_company_record(opportunity)
                return WorkflowActionResult(
                    action=action,
                    status="created" if updated else "failed",
                    detail=f"{detail}{f' Record ID: {record_id}.' if record_id else ''}",
                )
            if normalized == "hubspot_deal":
                updated, detail, record_id = self.hubspot.create_deal_record(opportunity)
                return WorkflowActionResult(
                    action=action,
                    status="created" if updated else "failed",
                    detail=f"{detail}{f' Deal ID: {record_id}.' if record_id else ''}",
                )
            updated = self.hubspot.upsert_company_opportunity(opportunity)
            return WorkflowActionResult(action=action, status="updated" if updated else "failed", detail="HubSpot company/deal action attempted.")

        return WorkflowActionResult(action=action, status="failed", detail="Unknown action.")

    def resolve_company(self, query: str) -> dict[str, str]:
        cleaned = " ".join(query.strip().split())
        key = cleaned.lower().replace("https://", "").replace("http://", "").strip("/")
        if key in KNOWN_COMPANIES:
            return KNOWN_COMPANIES[key].copy()

        if "." in key and " " not in key:
            name = key.split(".")[0].replace("-", " ").title()
            return {"name": name, "domain": key, "industry": "Unknown"}

        domain = f"{re.sub(r'[^a-z0-9]+', '', key)}.com"
        return {"name": cleaned.title(), "domain": domain, "industry": "Unknown"}

    def _search_news(self, company_name: str, domain: str) -> list[NewsItem]:
        if not self.settings.enable_live_integrations or not self.settings.news_api_key:
            return []

        queries = [
            f'"{company_name}" funding OR acquisition OR partnership OR revenue OR hiring',
            f'"{company_name}" competitors OR technology OR leadership',
        ]
        articles: list[NewsItem] = []
        seen: set[str] = set()
        for query in queries:
            try:
                response = httpx.get(
                    self.settings.news_api_url,
                    params={
                        "q": query,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": min(self.settings.news_api_page_size, 25),
                        "apiKey": self.settings.news_api_key,
                    },
                    timeout=self.settings.external_request_timeout,
                )
                response.raise_for_status()
                raw_articles = response.json().get("articles", [])
            except (httpx.HTTPError, ValueError, AttributeError):
                continue

            for article in raw_articles:
                title = str(article.get("title") or "").strip()
                source = str(article.get("url") or "").strip()
                if not title or source in seen:
                    continue
                text = f"{title} {article.get('description') or ''}".lower()
                if company_name.lower() not in text and domain.lower() not in text:
                    continue
                seen.add(source)
                self._record_raw_signal(
                    provider="NewsAPI",
                    signal_type="news",
                    company_name=company_name,
                    domain=domain,
                    title=title,
                    url=source,
                    source=source or "NewsAPI",
                    raw_snippet=str(article.get("description") or article.get("content") or title),
                    raw_payload=article if isinstance(article, dict) else {"article": article},
                    extracted_entities=self._extract_entities(f"{title} {article.get('description') or ''}", company_name),
                    confidence=82,
                    occurred_at=str(article.get("publishedAt") or "")[:10] or datetime.now(UTC).date().isoformat(),
                )
                articles.append(
                    NewsItem(
                        title=title[:180],
                        summary=self._clean(str(article.get("description") or article.get("content") or "")),
                        source=source or "NewsAPI",
                        occurred_at=str(article.get("publishedAt") or "")[:10] or datetime.now(UTC).date().isoformat(),
                    )
                )
        return articles[:20]

    def _fetch_overview(self, company_name: str) -> str:
        slug = company_name.replace(" ", "_")
        try:
            response = httpx.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
                timeout=self.settings.external_request_timeout,
            )
            if response.status_code == 200:
                payload = response.json()
                extract = payload.get("extract")
                if extract:
                    resolved = self.resolve_company(company_name)
                    self._record_raw_signal(
                        provider="Wikipedia",
                        signal_type="overview",
                        company_name=resolved["name"],
                        domain=resolved["domain"],
                        title=f"{resolved['name']} public overview",
                        url=f"https://en.wikipedia.org/wiki/{slug}",
                        source="Wikipedia REST API",
                        raw_snippet=str(extract),
                        raw_payload=payload if isinstance(payload, dict) else {"payload": payload},
                        extracted_entities=self._extract_entities(str(extract), resolved["name"]),
                        confidence=70,
                        occurred_at=datetime.now(UTC).date().isoformat(),
                    )
                    return self._clean(str(extract), limit=700)
        except (httpx.HTTPError, ValueError, AttributeError):
            pass
        return f"{company_name} is being analyzed from live news, public web signals, configured company metadata, and AI reasoning."

    def _analyze(
        self,
        resolved: dict[str, str],
        overview: str,
        news: list[NewsItem],
        hiring: list[HiringSignal],
        funding: list[FundingEvent],
        technologies: list[str],
    ) -> GeminiReport:
        fallback = self._fallback_analysis(resolved, overview, news, hiring, funding, technologies)
        if not self.gemini.enabled:
            return fallback

        payload = {
            "company": resolved,
            "overview": overview,
            "recent_news": [item.model_dump() for item in news[:10]],
            "hiring_signals": [item.model_dump() for item in hiring[:5]],
            "funding": [item.model_dump() for item in funding[:5]],
            "technologies": technologies,
            "graph_context": self._graph_context_for_prompt(resolved),
            "memory_context": self._memory_context_for_prompt(resolved, overview, technologies),
            "stored_evidence": [signal.model_dump(exclude={"raw_payload"}) for signal in self._captured_signals[:12]],
        }
        prompt = (
            "You are building a dynamic company intelligence report. "
            "Return only valid JSON with keys: executive_summary, swot_analysis, growth_signals, risks, "
            "competitive_landscape, opportunities, ai_recommendations, competitors, technologies, investors. "
            "All list fields must be arrays of concise strings. Do not invent precise financial numbers unless present in input.\n\n"
            f"Input:\n{json.dumps(payload, default=str)}"
        )
        raw = self.gemini._generate(prompt)
        if not raw:
            return fallback
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return fallback
        try:
            return GeminiReport.model_validate_json(match.group(0))
        except (ValidationError, ValueError):
            return fallback

    def _fallback_analysis(
        self,
        resolved: dict[str, str],
        overview: str,
        news: list[NewsItem],
        hiring: list[HiringSignal],
        funding: list[FundingEvent],
        technologies: list[str],
    ) -> GeminiReport:
        name = resolved["name"]
        news_titles = [item.title for item in news[:3]]
        return GeminiReport(
            executive_summary=(
                f"{name} is showing measurable market activity across "
                f"{len(news)} news signals, {len(hiring)} hiring signals, and {len(funding)} funding or deal signals. "
                f"{overview[:220]}"
            ),
            swot_analysis=[
                f"Strength: recognizable position in {resolved.get('industry', 'its market')}.",
                "Weakness: public data may miss private financial and customer details.",
                "Opportunity: recent signals can indicate expansion, partnerships, or buying intent.",
                "Threat: competitors can move faster if outreach and monitoring are delayed.",
            ],
            growth_signals=news_titles or ["No strong live growth signal was found yet."],
            risks=["Validate budget, timing, and decision makers before acting on this report."],
            competitive_landscape=[
                f"{name}'s competitive context should be validated against current customer alternatives."
            ],
            opportunities=[
                "Monitor live news and hiring changes for expansion timing.",
                "Create targeted outreach based on the strongest recent signal.",
            ],
            ai_recommendations=[
                "Refresh this report before sales action.",
                "Add paid firmographic, jobs, and technology-stack APIs for higher confidence.",
            ],
            competitors=[],
            technologies=technologies,
            investors=[],
        )

    def _hiring_signals(self, company_name: str, news: list[NewsItem]) -> list[HiringSignal]:
        signals: list[HiringSignal] = []
        domain = self.resolve_company(company_name)["domain"]
        keywords = ("hiring", "jobs", "careers", "recruit", "headcount", "layoff")
        for item in news:
            text = f"{item.title} {item.summary}".lower()
            if any(keyword in text for keyword in keywords):
                self._record_raw_signal(
                    provider="Derived",
                    signal_type="hiring",
                    company_name=company_name,
                    domain=domain,
                    title=item.title,
                    url=item.source,
                    source=item.source,
                    raw_snippet=item.summary,
                    raw_payload=item.model_dump(),
                    extracted_entities=self._extract_entities(f"{item.title} {item.summary}", company_name),
                    confidence=78,
                    occurred_at=item.occurred_at,
                )
                signals.append(
                    HiringSignal(
                        title=item.title,
                        summary=item.summary,
                        source=item.source,
                        strength=78,
                        occurred_at=item.occurred_at,
                    )
                )
        if not signals:
            signals.append(
                HiringSignal(
                    title=f"{company_name} hiring trend needs live jobs API validation",
                    summary="No direct hiring article was found in the current live-news window.",
                    source="Derived signal",
                    strength=45,
                    occurred_at=datetime.now(UTC).date().isoformat(),
                )
            )
            self._record_raw_signal(
                provider="Derived",
                signal_type="hiring",
                company_name=company_name,
                domain=domain,
                title=signals[-1].title,
                url="",
                source="Derived signal",
                raw_snippet=signals[-1].summary,
                raw_payload=signals[-1].model_dump(),
                extracted_entities=[company_name],
                confidence=45,
                occurred_at=signals[-1].occurred_at,
            )
        return signals

    def _funding_events(self, news: list[NewsItem]) -> list[FundingEvent]:
        events: list[FundingEvent] = []
        keywords = ("funding", "raised", "series", "invest", "valuation", "acquisition", "acquired", "ipo")
        for item in news:
            text = f"{item.title} {item.summary}".lower()
            if any(keyword in text for keyword in keywords):
                self._record_raw_signal(
                    provider="Derived",
                    signal_type="funding",
                    company_name="",
                    domain="",
                    title=item.title,
                    url=item.source,
                    source=item.source,
                    raw_snippet=item.summary,
                    raw_payload=item.model_dump(),
                    extracted_entities=self._extract_entities(f"{item.title} {item.summary}", ""),
                    confidence=76,
                    occurred_at=item.occurred_at,
                )
                events.append(
                    FundingEvent(
                        title=item.title,
                        summary=item.summary,
                        source=item.source,
                        occurred_at=item.occurred_at,
                    )
                )
        return events[:8]

    def _detect_technologies(
        self,
        news: list[NewsItem],
        overview: str,
        company_name: str = "",
        domain: str = "",
    ) -> list[str]:
        github_repositories = self.github.search_repositories(company_name, domain) if company_name and domain else []
        for repo in self.github.last_raw_repositories:
            name = str(repo.get("full_name") or repo.get("name") or "GitHub repository")
            description = str(repo.get("description") or "")
            self._record_raw_signal(
                provider="GitHub",
                signal_type="tech_stack",
                company_name=company_name,
                domain=domain,
                title=name,
                url=str(repo.get("html_url") or ""),
                source="GitHub Search API",
                raw_snippet=f"{name} {description} {repo.get('language') or ''}",
                raw_payload=repo if isinstance(repo, dict) else {"repository": repo},
                extracted_entities=[item for item in [str(repo.get("language") or "")] if item],
                confidence=66,
                occurred_at=str(repo.get("updated_at") or datetime.now(UTC).date().isoformat())[:10],
            )
        github_text = " ".join(
            f"{repo.get('name', '')} {repo.get('description', '')} {repo.get('language', '')}"
            for repo in github_repositories
        )
        text = f"{overview} {' '.join(item.title + ' ' + item.summary for item in news)} {github_text}".lower()
        found = [
            technology
            for technology, keywords in TECH_KEYWORDS.items()
            if any(keyword in f" {text} " for keyword in keywords)
        ]
        for repo in github_repositories:
            language = repo.get("language")
            if language and language not in found:
                found.append(language)
        return found or ["AI", "Cloud", "Data Platform"]

    def _infer_competitors(self, company_name: str, news: list[NewsItem]) -> list[str]:
        competitors: list[str] = []
        for item in news:
            match = re.search(r"competitors? (?:such as|including|like) ([^.]+)", item.summary, flags=re.I)
            if match:
                competitors.extend(part.strip() for part in re.split(r",| and ", match.group(1)) if part.strip())
        return [item for item in competitors if company_name.lower() not in item.lower()][:8]

    def _infer_industry(self, overview: str, news: list[NewsItem]) -> str:
        text = f"{overview} {' '.join(item.title for item in news)}".lower()
        if "vehicle" in text or "automotive" in text:
            return "Automotive and Energy"
        if "artificial intelligence" in text or " ai " in f" {text} ":
            return "Artificial Intelligence"
        if "finance" in text or "bank" in text:
            return "Financial Services"
        if "health" in text:
            return "Healthcare"
        return "Unknown"

    def _build_graph(self, company: CompanyIntelligence) -> tuple[list[GraphNode], list[GraphEdge]]:
        nodes = [GraphNode(id=company.domain, label=company.company_name, type="company")]
        edges: list[GraphEdge] = []

        def add_node(label: str, node_type: str, relation: str) -> None:
            node_id = f"{node_type}-{sha1(label.lower().encode()).hexdigest()[:10]}"
            nodes.append(GraphNode(id=node_id, label=label, type=node_type))
            edges.append(
                GraphEdge(
                    id=f"{company.domain}-{node_id}",
                    source=company.domain,
                    target=node_id,
                    label=relation,
                )
            )

        for investor in company.investors[:6]:
            add_node(investor, "investor", "backed by")
        for competitor in company.competitors[:8]:
            add_node(competitor, "competitor", "competes with")
        for technology in company.technologies[:8]:
            add_node(technology, "technology", "uses")
        for item in company.recent_news[:5]:
            add_node(item.title[:42], "news", "mentioned in")
        for item in company.hiring_signals[:3]:
            add_node(item.title[:42], "hiring", "hiring signal")
        return nodes, edges

    def _timeline(self, company: CompanyIntelligence) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for index, item in enumerate(company.recent_news):
            events.append(
                TimelineEvent(
                    id=f"news-{index}",
                    title=item.title,
                    summary=item.summary,
                    source=item.source,
                    category="news",
                    occurred_at=item.occurred_at,
                )
            )
        for index, item in enumerate(company.funding):
            events.append(
                TimelineEvent(
                    id=f"funding-{index}",
                    title=item.title,
                    summary=item.summary,
                    source=item.source,
                    category="funding",
                    occurred_at=item.occurred_at,
                )
            )
        for index, item in enumerate(company.hiring_signals):
            events.append(
                TimelineEvent(
                    id=f"hiring-{index}",
                    title=item.title,
                    summary=item.summary,
                    source=item.source,
                    category="hiring",
                    occurred_at=item.occurred_at,
                )
            )
        return sorted(events, key=lambda event: event.occurred_at, reverse=True)[:25]

    def _score(self, company: CompanyIntelligence, analysis: GeminiReport) -> tuple[int, int]:
        signal_count = len(company.recent_news) + len(company.hiring_signals) + len(company.funding)
        entity_count = len(company.competitors) + len(company.technologies) + len(company.investors)
        score = min(50 + signal_count * 4 + entity_count * 2, 98)
        confidence = min(45 + signal_count * 5 + len(analysis.ai_recommendations) * 4, 96)
        return score, confidence

    def _company_from_parts(
        self,
        resolved: dict[str, str],
        state: dict[str, Any],
        analysis: GeminiReport,
    ) -> CompanyIntelligence:
        news = state.get("news", [])
        return CompanyIntelligence(
            company_name=resolved["name"],
            domain=resolved["domain"],
            industry=resolved.get("industry") or self._infer_industry(state.get("overview", ""), news),
            headquarters=resolved.get("headquarters") or "Unknown",
            employees=resolved.get("employees") or "Unknown",
            funding=state.get("funding", []),
            investors=analysis.investors[:8],
            competitors=analysis.competitors[:10] or self._infer_competitors(resolved["name"], news),
            technologies=(analysis.technologies or state.get("technologies", []))[:12],
            recent_news=news[:12],
            hiring_signals=state.get("hiring", [])[:8],
            overview=state.get("overview", ""),
        )

    def _store_memory(self, company: CompanyIntelligence) -> None:
        synthetic = Company(
            id=self._cache_key(company.domain),
            name=company.company_name,
            industry=company.industry,
            region=company.headquarters,
            stage=company.employees,
            description=company.overview,
            website=f"https://{company.domain}",
            competitors=company.competitors,
            technologies=company.technologies,
        )
        self.memory.upsert_companies([synthetic])

    def _store_graph(self, company: CompanyIntelligence) -> None:
        synthetic = Company(
            id=self._cache_key(company.domain),
            name=company.company_name,
            industry=company.industry,
            region=company.headquarters,
            stage=company.employees,
            description=company.overview,
            website=f"https://{company.domain}",
            competitors=company.competitors,
            technologies=company.technologies,
        )
        self.graph.upsert_company(synthetic)

    def _begin_signal_capture(self) -> None:
        self._captured_signals = []

    def _save_captured_signals(self) -> None:
        self.repository.save_signals(self._captured_signals)

    def _record_raw_signal(
        self,
        *,
        provider: str,
        signal_type: str,
        company_name: str,
        domain: str,
        title: str,
        url: str,
        source: str,
        raw_snippet: str,
        raw_payload: dict[str, Any],
        extracted_entities: list[str],
        confidence: int,
        occurred_at: str,
    ) -> None:
        if not company_name or not domain:
            current = self._captured_signals[0] if self._captured_signals else None
            company_name = company_name or (current.company_name if current else "Unknown")
            domain = domain or (current.domain if current else "unknown")
        key = self._cache_key(domain)
        dedup_key = sha1(f"{key}:{provider}:{signal_type}:{url or title}".lower().encode()).hexdigest()
        if any(signal.dedup_key == dedup_key for signal in self._captured_signals):
            return
        self._captured_signals.append(
            RawCompanySignal(
                id=f"signal-{dedup_key[:16]}",
                company_key=key,
                company_name=company_name,
                domain=domain,
                provider=provider,
                signal_type=signal_type,
                source=source,
                title=title[:220],
                url=url,
                raw_snippet=self._clean(raw_snippet, limit=900),
                raw_payload=raw_payload,
                extracted_entities=extracted_entities[:20],
                confidence=confidence,
                occurred_at=occurred_at or datetime.now(UTC).date().isoformat(),
                captured_at=datetime.now(UTC).isoformat(),
                dedup_key=dedup_key,
            )
        )

    def _extract_entities(self, text: str, company_name: str) -> list[str]:
        entities = {company_name} if company_name else set()
        lowered = text.lower()
        for technology, keywords in TECH_KEYWORDS.items():
            if any(keyword.strip().lower() in lowered for keyword in keywords):
                entities.add(technology)
        for match in re.findall(r"\b[A-Z][A-Za-z0-9&.-]{2,}(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,2}\b", text):
            entities.add(match.strip())
        return sorted(item for item in entities if item)[:20]

    def _apply_report_deltas(self, report: CompanyReport, cache_key: str) -> CompanyReport:
        previous = self.repository.previous_report(cache_key, before_report_id=report.id)
        if previous is None:
            return report
        score_delta = report.opportunity_score - previous.opportunity_score
        timeline_delta = max(len(report.timeline) - len(previous.timeline), 0)
        alert = ""
        if abs(score_delta) >= 5:
            direction = "increased" if score_delta > 0 else "decreased"
            top_signal = report.timeline[0].title if report.timeline else "new evidence"
            alert = (
                f"{report.company.company_name} score {direction} from "
                f"{previous.opportunity_score} to {report.opportunity_score} because of {top_signal}."
            )
        return report.model_copy(
            update={"score_delta": score_delta, "timeline_delta": timeline_delta, "score_alert": alert}
        )

    def _graph_context_for_prompt(self, resolved: dict[str, str]) -> list[str]:
        company = Company(
            id=self._cache_key(resolved["domain"]),
            name=resolved["name"],
            industry=resolved.get("industry", "Unknown"),
            region="Unknown",
            stage="Unknown",
            description="",
            website=f"https://{resolved['domain']}",
            competitors=[],
            technologies=[],
        )
        nodes, edges = self.graph.graph_for_company(company)
        return [f"{edge.source} {edge.label} {edge.target}" for edge in edges[:12]] or [node.label for node in nodes[1:8]]

    def _memory_context_for_prompt(self, resolved: dict[str, str], overview: str, technologies: list[str]) -> list[str]:
        company = Company(
            id=self._cache_key(resolved["domain"]),
            name=resolved["name"],
            industry=resolved.get("industry", "Unknown"),
            region="Unknown",
            stage="Unknown",
            description=overview,
            website=f"https://{resolved['domain']}",
            competitors=[],
            technologies=technologies,
        )
        return self.memory.find_similar(company, limit=5)

    def _report_to_opportunity(self, report: CompanyReport) -> Any:
        from app.models.domain import Opportunity, ScoreReason, Signal, SignalType, WorkflowAction

        company = Company(
            id=self._cache_key(report.company.domain),
            name=report.company.company_name,
            industry=report.company.industry,
            region=report.company.headquarters,
            stage=report.company.employees,
            description=report.company.overview,
            website=f"https://{report.company.domain}",
            competitors=report.company.competitors,
            technologies=report.company.technologies,
        )
        signals = [
            Signal(
                id=event.id,
                company_id=company.id,
                type=SignalType.news,
                title=event.title,
                summary=event.summary,
                source=event.source,
                strength=report.confidence,
                occurred_at=event.occurred_at,
            )
            for event in report.timeline[:8]
        ]
        return Opportunity(
            id=f"report-action-{report.id}",
            company=company,
            opportunity_type="Company Intelligence",
            score=report.opportunity_score,
            confidence=report.confidence,
            probability=report.opportunity_score,
            summary=report.analysis.executive_summary,
            recommended_action=report.analysis.ai_recommendations[0] if report.analysis.ai_recommendations else "Review latest signals.",
            reasons=[
                ScoreReason(
                    label="Company report score",
                    impact=report.opportunity_score,
                    evidence=report.analysis.executive_summary,
                )
            ],
            risks=report.analysis.risks,
            signals=signals,
            workflow_actions=[
                WorkflowAction(type="slack", title="Send Slack alert", payload=report.analysis.executive_summary),
                WorkflowAction(type="crm", title="Create HubSpot company/deal", payload=report.company.domain),
            ],
            graph_nodes=report.graph_nodes,
            graph_edges=report.graph_edges,
        )

    def _cache_key(self, domain: str) -> str:
        return domain.lower().replace("https://", "").replace("http://", "").strip("/")

    def _report_id(self, domain: str) -> str:
        return f"report-{sha1(f'{domain}:{datetime.now(UTC).isoformat()}'.encode()).hexdigest()[:16]}"

    def _clean(self, value: str, limit: int = 360) -> str:
        cleaned = " ".join(value.replace("\n", " ").split())
        return cleaned[:limit] or "No summary available from the live source."
