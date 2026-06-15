from app.models.domain import Trend


class MonitoringAgent:
    def trends(self) -> list[Trend]:
        return [
            Trend(id="healthcare-ai", label="Healthcare AI", direction="up", score=92, change=14),
            Trend(id="computer-vision", label="Computer Vision", direction="up", score=86, change=9),
            Trend(id="fintech-ai", label="FinTech AI", direction="flat", score=74, change=2),
            Trend(id="generic-saas", label="Generic SaaS", direction="down", score=61, change=-7),
        ]

