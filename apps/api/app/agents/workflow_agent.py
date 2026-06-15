from app.models.domain import Company, Opportunity, WorkflowAction
from app.integrations.gemini_client import GeminiClient
from app.integrations.hubspot_client import HubSpotClient
from app.integrations.slack_client import SlackClient


class WorkflowAgent:
    def __init__(
        self,
        gemini_client: GeminiClient | None = None,
        slack_client: SlackClient | None = None,
        hubspot_client: HubSpotClient | None = None,
    ) -> None:
        self.gemini_client = gemini_client
        self.slack_client = slack_client
        self.hubspot_client = hubspot_client

    def build_actions(self, company: Company, score: int) -> list[WorkflowAction]:
        priority = "High Intent Lead" if score >= 80 else "Monitor Lead"
        return [
            WorkflowAction(
                type="email",
                title="Generate outreach email",
                payload=f"Personalized email for {company.name} focused on {company.industry}.",
            ),
            WorkflowAction(
                type="slack",
                title="Send Slack alert",
                payload=f"{priority}: {company.name} scored {score}. Recommended next step: research buyer and send outreach.",
            ),
            WorkflowAction(
                type="crm",
                title="Update CRM",
                payload=f"Create opportunity record for {company.name} with latest signals and score.",
            ),
        ]

    def execute_actions(self, opportunity: Opportunity) -> list[WorkflowAction]:
        actions = opportunity.workflow_actions.copy()
        if opportunity.score < 85:
            return actions

        slack_sent = False
        if self.slack_client:
            slack_sent = self.slack_client.send_alert(
                f"High Intent Lead: {opportunity.company.name}\n"
                f"Score: {opportunity.score} | Confidence: {opportunity.confidence}%\n"
                f"Reason: {opportunity.reasons[0].label if opportunity.reasons else opportunity.summary}\n"
                f"Next action: {opportunity.recommended_action}"
            )

        crm_updated = False
        if self.hubspot_client:
            crm_updated = self.hubspot_client.upsert_company_opportunity(opportunity)

        updated_actions: list[WorkflowAction] = []
        for action in actions:
            if action.type == "slack" and slack_sent:
                updated_actions.append(action.model_copy(update={"status": "sent"}))
            elif action.type == "crm" and crm_updated:
                updated_actions.append(action.model_copy(update={"status": "updated"}))
            else:
                updated_actions.append(action)
        return updated_actions

    def generate_email(self, opportunity: Opportunity, sender_name: str, product_name: str) -> tuple[str, str]:
        if self.gemini_client:
            generated = self.gemini_client.generate_email(opportunity, sender_name, product_name)
            if generated:
                return generated.subject, generated.body

        top_reason = opportunity.reasons[0].label.lower() if opportunity.reasons else "recent growth signals"
        subject = f"{opportunity.company.name} and scaling AI workflows"
        body = (
            f"Hi {opportunity.company.name} team,\n\n"
            f"Congrats on the momentum around {top_reason}. I noticed signals that your team is scaling "
            f"{opportunity.company.industry.lower()} initiatives, including {opportunity.signals[0].title.lower()}.\n\n"
            f"{product_name} helps teams deploy, monitor, and govern AI workflows without slowing product teams down. "
            f"Based on your current stack ({', '.join(opportunity.company.technologies[:3])}), there may be a strong fit.\n\n"
            "Would it be worth a 15-minute conversation next week to compare notes on your AI infrastructure roadmap?\n\n"
            f"Best,\n{sender_name}"
        )
        return subject, body
