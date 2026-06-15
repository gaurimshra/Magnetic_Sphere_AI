import json
from hashlib import sha1
from typing import Any

from app.core.config import Settings
from app.models.domain import Company, Signal, SignalType
from app.repositories.demo_data import COMPANIES, SIGNALS


class SignalAgent:
    signal_type: SignalType | None = None

    def run(self, companies: list[Company]) -> list[Signal]:
        company_ids = {company.id for company in companies}
        return [
            signal
            for signal in SIGNALS
            if signal.company_id in company_ids
            and (self.signal_type is None or signal.type == self.signal_type)
        ]


class FundingAgent(SignalAgent):
    signal_type = SignalType.funding


class HiringAgent(SignalAgent):
    signal_type = SignalType.hiring


class NewsAgent(SignalAgent):
    signal_type = SignalType.news


class SocialAgent(SignalAgent):
    signal_type = SignalType.social


class TechStackAgent(SignalAgent):
    signal_type = SignalType.tech_stack


class CompetitorSentimentAgent(SignalAgent):
    signal_type = SignalType.competitor


class RSSNewsAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, companies: list[Company]) -> list[Signal]:
        if not self.settings.enable_live_integrations:
            return []

        try:
            import feedparser
            import httpx
        except ImportError:
            return []

        feeds = [feed.strip() for feed in self.settings.news_rss_feeds.split(",") if feed.strip()]
        keywords = [keyword.strip().lower() for keyword in self.settings.target_keywords.split(",") if keyword.strip()]
        signals: list[Signal] = []

        for feed_url in feeds:
            try:
                response = httpx.get(feed_url, timeout=self.settings.external_request_timeout)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
            except (httpx.HTTPError, ValueError):
                continue
            for entry in parsed.entries[:20]:
                title = str(getattr(entry, "title", ""))
                summary = str(getattr(entry, "summary", ""))
                text = f"{title} {summary}".lower()
                if keywords and not any(keyword in text for keyword in keywords):
                    continue

                matched_company = self._match_company(companies, text)
                if not matched_company:
                    continue

                signal_id = sha1(f"{matched_company.id}:{title}".encode("utf-8")).hexdigest()[:16]
                signals.append(
                    Signal(
                        id=f"rss-{signal_id}",
                        company_id=matched_company.id,
                        type=SignalType.news,
                        title=title[:140] or "Live news signal",
                        summary=self._clean_summary(summary),
                        source=str(getattr(entry, "link", feed_url)),
                        strength=72,
                        occurred_at=str(getattr(entry, "published", ""))[:10] or "2026-06-10",
                    )
                )
        return signals

    def _match_company(self, companies: list[Company], text: str) -> Company | None:
        for company in companies:
            if company.name.lower() in text:
                return company
        return None

    def _clean_summary(self, summary: str) -> str:
        cleaned = " ".join(summary.replace("\n", " ").split())
        return cleaned[:260] or "Live RSS signal matched the target company and keywords."


class NewsAPIAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, companies: list[Company]) -> list[Signal]:
        if not self.settings.enable_live_integrations or not self.settings.news_api_key:
            return []

        try:
            import httpx
        except ImportError:
            return []

        signals: list[Signal] = []
        keywords = [keyword.strip() for keyword in self.settings.target_keywords.split(",") if keyword.strip()]

        for company in companies:
            query_terms = [f'"{company.name}"', *keywords[:5]]
            params = {
                "q": " OR ".join(query_terms),
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": self.settings.news_api_page_size,
                "apiKey": self.settings.news_api_key,
            }

            try:
                response = httpx.get(
                    self.settings.news_api_url,
                    params=params,
                    timeout=self.settings.external_request_timeout,
                )
                response.raise_for_status()
                articles = response.json().get("articles", [])
            except (httpx.HTTPError, ValueError, AttributeError):
                continue

            for article in articles[:5]:
                title = str(article.get("title") or "")
                description = str(article.get("description") or "")
                text = f"{title} {description}".lower()
                if company.name.lower() not in text:
                    continue

                article_url = str(article.get("url") or "NewsAPI")
                signal_id = sha1(f"{company.id}:{article_url}:{title}".encode("utf-8")).hexdigest()[:16]
                signals.append(
                    Signal(
                        id=f"newsapi-{signal_id}",
                        company_id=company.id,
                        type=SignalType.news,
                        title=title[:140] or "Live NewsAPI signal",
                        summary=self._clean_summary(description),
                        source=article_url,
                        strength=80,
                        occurred_at=str(article.get("publishedAt") or "")[:10] or "2026-06-10",
                    )
                )

        return signals

    def _clean_summary(self, summary: str) -> str:
        cleaned = " ".join(summary.replace("\n", " ").split())
        return cleaned[:260] or "Live NewsAPI article matched the target company."


def load_target_companies(settings: Settings | None = None) -> list[Company]:
    if settings and settings.target_companies_json:
        configured = _load_configured_companies(settings.target_companies_json)
        if configured:
            return configured
    return COMPANIES


def _load_configured_companies(raw_json: str) -> list[Company]:
    try:
        raw_companies = json.loads(raw_json)
    except json.JSONDecodeError:
        return []

    if not isinstance(raw_companies, list):
        return []

    companies: list[Company] = []
    for index, raw_company in enumerate(raw_companies):
        if not isinstance(raw_company, dict):
            continue
        normalized = _normalize_company(raw_company, index)
        if normalized:
            companies.append(normalized)
    return companies


def _normalize_company(raw_company: dict[str, Any], index: int) -> Company | None:
    name = str(raw_company.get("name") or "").strip()
    if not name:
        return None

    company_id = str(raw_company.get("id") or name.lower().replace(" ", "-")).strip()
    website = str(raw_company.get("website") or raw_company.get("domain") or "").strip()
    if website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"

    return Company(
        id=company_id or f"company-{index + 1}",
        name=name,
        industry=str(raw_company.get("industry") or "Unknown").strip(),
        region=str(raw_company.get("region") or "Unknown").strip(),
        stage=str(raw_company.get("stage") or "Unknown").strip(),
        description=str(raw_company.get("description") or f"Configured target account: {name}.").strip(),
        website=website or f"https://example.com/{company_id}",
        competitors=_string_list(raw_company.get("competitors")),
        technologies=_string_list(raw_company.get("technologies")),
    )


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []
