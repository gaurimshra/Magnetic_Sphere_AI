from app.models.domain import Company, ScoreReason, Signal, SignalType
from app.integrations.gemini_client import GeminiClient, to_score_reasons


class ReasoningAgent:
    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini_client = gemini_client

    def analyze(
        self,
        company: Company,
        signals: list[Signal],
        similar_companies: list[str],
        use_live_ai: bool = True,
    ) -> dict:
        if use_live_ai and self.gemini_client:
            gemini_analysis = self.gemini_client.analyze_opportunity(company, signals, similar_companies)
            if gemini_analysis:
                return {
                    "opportunity_type": gemini_analysis.opportunity_type,
                    "summary": gemini_analysis.summary,
                    "reasons": to_score_reasons(gemini_analysis.reasons),
                    "risks": gemini_analysis.risks,
                }

        signal_types = {signal.type for signal in signals}
        reasons: list[ScoreReason] = []

        if SignalType.funding in signal_types:
            reasons.append(
                ScoreReason(
                    label="Recent funding",
                    impact=96,
                    evidence="New capital usually creates budget for platform adoption and hiring.",
                )
            )

        if SignalType.hiring in signal_types:
            reasons.append(
                ScoreReason(
                    label="Expansion hiring",
                    impact=88,
                    evidence="Open AI and infrastructure roles indicate scaling pressure.",
                )
            )

        if SignalType.social in signal_types or SignalType.competitor in signal_types:
            reasons.append(
                ScoreReason(
                    label="Market intent",
                    impact=82,
                    evidence="Public conversations show active interest or dissatisfaction with alternatives.",
                )
            )

        if SignalType.tech_stack in signal_types:
            reasons.append(
                ScoreReason(
                    label="Tech-stack fit",
                    impact=78,
                    evidence=f"{company.name} already uses cloud-native tools compatible with the product.",
                )
            )

        if similar_companies:
            reasons.append(
                ScoreReason(
                    label="Comparable account memory",
                    impact=70,
                    evidence=f"Similar companies found: {', '.join(similar_companies)}.",
                )
            )

        opportunity_type = "High Intent" if len(reasons) >= 3 else "Emerging Intent"
        summary = (
            f"{company.name} is showing {opportunity_type.lower()} for AI infrastructure. "
            f"The strongest evidence comes from {', '.join(reason.label.lower() for reason in reasons[:3])}."
        )
        risks = []
        if SignalType.funding not in signal_types:
            risks.append("No recent funding signal found, so budget timing may need validation.")
        if SignalType.tech_stack not in signal_types:
            risks.append("Tech-stack compatibility is inferred and should be confirmed in discovery.")

        return {
            "opportunity_type": opportunity_type,
            "summary": summary,
            "reasons": reasons,
            "risks": risks or ["Primary risk is competitor speed; outreach should happen quickly."],
        }
