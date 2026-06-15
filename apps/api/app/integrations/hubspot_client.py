import httpx

from app.core.config import Settings
from app.models.domain import Opportunity


type HubSpotResult = tuple[bool, str, str | None]


class HubSpotClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.enable_live_integrations and self.settings.hubspot_access_token)

    def upsert_company_opportunity(self, opportunity: Opportunity) -> bool:
        if not self.enabled:
            return False

        company_created = self._create_company(opportunity)
        deal_created = self._create_deal(opportunity)
        return company_created and deal_created

    def create_company(self, opportunity: Opportunity) -> bool:
        if not self.enabled:
            return False
        return self._create_company(opportunity)

    def create_deal(self, opportunity: Opportunity) -> bool:
        if not self.enabled:
            return False
        return self._create_deal(opportunity)

    def create_company_record(self, opportunity: Opportunity) -> HubSpotResult:
        if not self.enabled:
            return False, "HubSpot is not enabled.", None
        return self._upsert_company_record(opportunity)

    def create_deal_record(self, opportunity: Opportunity) -> HubSpotResult:
        if not self.enabled:
            return False, "HubSpot is not enabled.", None

        company_ok, company_detail, company_id = self._upsert_company_record(opportunity)
        if not company_ok:
            return False, company_detail, None

        deal_ok, deal_detail, deal_id = self._create_deal_record(opportunity)
        if not deal_ok or not deal_id:
            return False, deal_detail, deal_id

        associated = self._associate_deal_to_company(deal_id, company_id) if company_id else False
        if not associated:
            return True, f"{deal_detail} Company association was not confirmed.", deal_id
        return True, f"{deal_detail} Associated with company record {company_id}.", deal_id

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.hubspot_access_token}",
            "Content-Type": "application/json",
        }

    def _create_company(self, opportunity: Opportunity) -> bool:
        ok, _, _ = self._upsert_company_record(opportunity)
        return ok

    def _upsert_company_record(self, opportunity: Opportunity) -> HubSpotResult:
        domain = opportunity.company.website.replace("https://", "").replace("http://", "").split("/")[0]
        existing_id = self._find_company_id(domain)
        if existing_id:
            return True, f"Found existing HubSpot company for {domain}.", existing_id

        payload = {
            "properties": {
                "name": opportunity.company.name,
                "domain": domain,
                "industry": opportunity.company.industry,
                "description": opportunity.company.description,
            }
        }
        ok, detail, record_id = self._post_record("/crm/v3/objects/companies", payload)
        return ok, detail, record_id

    def _create_deal(self, opportunity: Opportunity) -> bool:
        ok, _, _ = self._create_deal_record(opportunity)
        return ok

    def _create_deal_record(self, opportunity: Opportunity) -> HubSpotResult:
        payload = {
            "properties": {
                "dealname": f"{opportunity.company.name} - MagneticSphere Opportunity",
                "pipeline": "default",
                "dealstage": "appointmentscheduled",
                "description": opportunity.summary,
                "amount": str(max(opportunity.score, 1) * 1000),
            }
        }
        return self._post_record("/crm/v3/objects/deals", payload)

    def _post(self, path: str, payload: dict) -> bool:
        ok, _, _ = self._post_record(path, payload)
        return ok

    def _post_record(self, path: str, payload: dict) -> HubSpotResult:
        try:
            response = httpx.post(
                f"{self.settings.hubspot_base_url}{path}",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if response.status_code < 300:
                body = response.json()
                return True, f"HubSpot returned HTTP {response.status_code}.", str(body.get("id") or "")
            if response.status_code == 409:
                return True, "HubSpot reported a duplicate record.", None
            return False, f"HubSpot returned HTTP {response.status_code}.", None
        except (httpx.HTTPError, ValueError, AttributeError) as exc:
            return False, f"HubSpot request failed: {exc.__class__.__name__}.", None

    def _find_company_id(self, domain: str) -> str | None:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "domain",
                            "operator": "EQ",
                            "value": domain,
                        }
                    ]
                }
            ],
            "properties": ["name", "domain"],
            "limit": 1,
        }
        try:
            response = httpx.post(
                f"{self.settings.hubspot_base_url}/crm/v3/objects/companies/search",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if response.status_code >= 300:
                return None
            results = response.json().get("results", [])
            if not results:
                return None
            return str(results[0].get("id") or "") or None
        except (httpx.HTTPError, ValueError, AttributeError, IndexError):
            return None

    def _associate_deal_to_company(self, deal_id: str | None, company_id: str | None) -> bool:
        if not deal_id or not company_id:
            return False
        try:
            response = httpx.put(
                f"{self.settings.hubspot_base_url}/crm/v4/objects/deals/{deal_id}/associations/default/companies/{company_id}",
                headers=self._headers(),
                timeout=15,
            )
            return response.status_code < 300
        except httpx.HTTPError:
            return False
