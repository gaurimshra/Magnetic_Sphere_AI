import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.models.domain import Company, Opportunity, ScoreReason, Signal


class GeminiReason(BaseModel):
    label: str
    impact: int = Field(ge=0, le=100)
    evidence: str


class GeminiAnalysis(BaseModel):
    opportunity_type: str
    summary: str
    reasons: list[GeminiReason]
    risks: list[str]


class GeminiEmail(BaseModel):
    subject: str
    body: str


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.enable_live_integrations and self.settings.gemini_api_key)

    def analyze_opportunity(
        self,
        company: Company,
        signals: list[Signal],
        similar_companies: list[str],
    ) -> GeminiAnalysis | None:
        if not self.enabled:
            return None

        payload = {
            "company": company.model_dump(),
            "signals": [signal.model_dump() for signal in signals],
            "similar_companies": similar_companies,
        }
        prompt = (
            "You are an opportunity intelligence analyst for a B2B AI platform.\n"
            "Analyze the company and signals. Return only valid JSON with this shape:\n"
            "{"
            '"opportunity_type": "High Intent | Emerging Intent | Monitor", '
            '"summary": "short explanation", '
            '"reasons": [{"label": "reason", "impact": 0-100, "evidence": "specific evidence"}], '
            '"risks": ["risk"]'
            "}\n\n"
            f"Input:\n{json.dumps(payload, default=str)}"
        )
        raw = self._generate(prompt)
        return self._parse_model(raw, GeminiAnalysis)

    def generate_email(
        self,
        opportunity: Opportunity,
        sender_name: str,
        product_name: str,
    ) -> GeminiEmail | None:
        if not self.enabled:
            return None

        payload = {
            "opportunity": opportunity.model_dump(),
            "sender_name": sender_name,
            "product_name": product_name,
        }
        prompt = (
            "Write a concise, personalized B2B outreach email. Return only valid JSON:\n"
            '{"subject": "subject line", "body": "email body"}\n\n'
            "Rules: no fake claims, mention one concrete signal, keep under 170 words.\n\n"
            f"Input:\n{json.dumps(payload, default=str)}"
        )
        raw = self._generate(prompt)
        return self._parse_model(raw, GeminiEmail)

    def _generate(self, prompt: str) -> str | None:
        try:
            from google import genai
        except ImportError:
            return None

        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            for model in self._candidate_models():
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    if response.text:
                        return response.text
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def _candidate_models(self) -> list[str]:
        candidates = [
            self.settings.gemini_model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        deduped: list[str] = []
        for model in candidates:
            if model and model not in deduped:
                deduped.append(model)
        return deduped

    def _parse_model(self, raw: str | None, model: type[BaseModel]) -> Any | None:
        if not raw:
            return None

        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return None

        try:
            return model.model_validate_json(match.group(0))
        except (ValidationError, json.JSONDecodeError):
            return None


def to_score_reasons(reasons: list[GeminiReason]) -> list[ScoreReason]:
    return [
        ScoreReason(label=reason.label, impact=reason.impact, evidence=reason.evidence)
        for reason in reasons
    ]
