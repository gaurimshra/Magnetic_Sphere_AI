import json
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings, get_settings


IntegrationStatus = dict[str, bool | str]


def integration_status() -> dict[str, IntegrationStatus]:
    settings = get_settings()
    live = settings.enable_live_integrations
    checked_at = datetime.now(UTC).isoformat()
    timeout = min(settings.external_request_timeout, 3.0)

    def status(
        *,
        enabled: bool,
        configured: bool,
        detail: str,
        reachable: bool = False,
        checked: bool = False,
    ) -> IntegrationStatus:
        return {
            "enabled": enabled,
            "configured": configured,
            "reachable": reachable,
            "checked": checked,
            "detail": detail,
            "checked_at": checked_at,
        }

    return {
        "live_integrations": status(
            enabled=live,
            configured=live,
            reachable=live,
            checked=True,
            detail="Live integrations are enabled." if live else "Set ENABLE_LIVE_INTEGRATIONS=true to use external providers.",
        ),
        "gemini": _gemini_status(settings, timeout, status),
        "qdrant": _qdrant_status(settings, timeout, status),
        "neo4j": _neo4j_status(settings, status),
        "slack": _slack_status(settings, timeout, status),
        "hubspot": _hubspot_status(settings, timeout, status),
        "news_api": _news_api_status(settings, timeout, status),
        "github": _github_status(settings, timeout, status),
        "rss_news": _rss_status(settings, timeout, status),
        "target_companies": _target_companies_status(settings, status),
    }


def _enabled(settings: Settings, configured: bool) -> bool:
    return bool(settings.enable_live_integrations and configured)


def _http_reachable(method: str, url: str, **kwargs: Any) -> tuple[bool, str]:
    try:
        response = httpx.request(method, url, **kwargs)
        if response.status_code < 400:
            return True, f"Reachable ({response.status_code})."
        return False, f"Provider returned HTTP {response.status_code}."
    except httpx.HTTPError as exc:
        return False, f"Connectivity check failed: {exc.__class__.__name__}."


def _gemini_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.gemini_api_key)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail=settings.gemini_model)

    reachable, detail = _http_reachable(
        "GET",
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": settings.gemini_api_key},
        timeout=timeout,
    )
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _qdrant_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.qdrant_url)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail=settings.qdrant_url)

    headers = {"api-key": settings.qdrant_api_key} if settings.qdrant_api_key else None
    reachable, detail = _http_reachable(
        "GET",
        f"{settings.qdrant_url.rstrip('/')}/collections",
        headers=headers,
        timeout=timeout,
    )
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _neo4j_status(settings: Settings, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.neo4j_uri and settings.neo4j_username and settings.neo4j_password)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail=settings.neo4j_uri)

    try:
        from neo4j import GraphDatabase

        with GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
            connection_timeout=3,
            max_transaction_retry_time=1,
        ) as driver:
            driver.verify_connectivity()
        return make_status(
            enabled=enabled,
            configured=configured,
            reachable=True,
            checked=True,
            detail="Reachable.",
        )
    except Exception as exc:
        return make_status(
            enabled=enabled,
            configured=configured,
            reachable=False,
            checked=True,
            detail=f"Connectivity check failed: {exc.__class__.__name__}.",
        )


def _slack_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.slack_webhook_url or (settings.slack_bot_token and settings.slack_channel_id))
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(
            enabled=enabled,
            configured=bool(settings.slack_webhook_url or settings.slack_bot_token),
            detail="Missing SLACK_WEBHOOK_URL, or SLACK_BOT_TOKEN plus SLACK_CHANNEL_ID.",
        )

    if settings.slack_bot_token and settings.slack_channel_id:
        reachable, detail = _http_reachable(
            "POST",
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            timeout=timeout,
        )
        return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)

    return make_status(
        enabled=enabled,
        configured=configured,
        reachable=False,
        checked=False,
        detail="Webhook configured; health check skipped to avoid sending a Slack message.",
    )


def _hubspot_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.hubspot_access_token or settings.hubspot_api_key)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail="Missing HubSpot access token.")

    reachable, detail = _http_reachable(
        "GET",
        f"{settings.hubspot_base_url.rstrip('/')}/crm/v3/objects/companies",
        params={"limit": 1},
        headers={"Authorization": f"Bearer {settings.hubspot_access_token}", "Accept": "application/json"},
        timeout=timeout,
    )
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _news_api_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.news_api_key)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail=settings.news_api_url)

    reachable, detail = _http_reachable(
        "GET",
        settings.news_api_url,
        params={"q": "OpenAI", "pageSize": 1, "apiKey": settings.news_api_key},
        timeout=timeout,
    )
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _github_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    configured = bool(settings.github_token)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail=settings.github_api_url)

    reachable, detail = _http_reachable(
        "GET",
        f"{settings.github_api_url.rstrip('/')}/rate_limit",
        headers={
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=timeout,
    )
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _rss_status(settings: Settings, timeout: float, make_status: Any) -> IntegrationStatus:
    feeds = [feed.strip() for feed in settings.news_rss_feeds.split(",") if feed.strip()]
    configured = bool(feeds)
    enabled = _enabled(settings, configured)
    if not enabled:
        return make_status(enabled=enabled, configured=configured, detail="No RSS feeds configured.")

    reachable, detail = _http_reachable("GET", feeds[0], timeout=timeout, follow_redirects=True)
    if reachable:
        detail = f"Reachable first feed; {len(feeds)} configured."
    return make_status(enabled=enabled, configured=configured, reachable=reachable, checked=True, detail=detail)


def _target_companies_status(settings: Settings, make_status: Any) -> IntegrationStatus:
    if not settings.target_companies_json:
        return make_status(
            enabled=False,
            configured=False,
            detail="Using demo target companies.",
            checked=True,
        )

    try:
        companies = json.loads(settings.target_companies_json)
        if not isinstance(companies, list):
            raise ValueError("TARGET_COMPANIES_JSON must be a JSON array.")
        return make_status(
            enabled=True,
            configured=True,
            reachable=True,
            checked=True,
            detail=f"Validated {len(companies)} configured target companies.",
        )
    except (json.JSONDecodeError, ValueError) as exc:
        return make_status(
            enabled=True,
            configured=True,
            reachable=False,
            checked=True,
            detail=f"Invalid TARGET_COMPANIES_JSON: {exc.__class__.__name__}.",
        )
