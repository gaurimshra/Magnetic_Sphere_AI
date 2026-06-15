import httpx

from app.core.config import Settings


class GitHubClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.last_raw_repositories: list[dict] = []

    @property
    def enabled(self) -> bool:
        return bool(self.settings.enable_live_integrations and self.settings.github_token)

    def search_repositories(self, company_name: str, domain: str, limit: int = 5) -> list[dict[str, str]]:
        self.last_raw_repositories = []
        if not self.enabled:
            return []

        query = f'"{company_name}" OR "{domain}"'
        try:
            response = httpx.get(
                f"{self.settings.github_api_url}/search/repositories",
                params={"q": query, "sort": "updated", "order": "desc", "per_page": limit},
                headers={
                    "Authorization": f"Bearer {self.settings.github_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.settings.external_request_timeout,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            self.last_raw_repositories = items if isinstance(items, list) else []
        except (httpx.HTTPError, ValueError, AttributeError):
            return []

        repositories: list[dict[str, str]] = []
        for item in items:
            repositories.append(
                {
                    "name": str(item.get("full_name") or item.get("name") or ""),
                    "description": str(item.get("description") or ""),
                    "language": str(item.get("language") or ""),
                    "url": str(item.get("html_url") or ""),
                }
            )
        return repositories
