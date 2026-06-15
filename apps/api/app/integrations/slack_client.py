import httpx

from app.core.config import Settings


class SlackClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.enable_live_integrations
            and (
                self.settings.slack_webhook_url
                or (self.settings.slack_bot_token and self.settings.slack_channel_id)
            )
        )

    def send_alert(self, text: str) -> bool:
        if not self.enabled:
            return False

        if self.settings.slack_webhook_url:
            return self._send_webhook(text)
        return self._send_bot_message(text)

    def _send_webhook(self, text: str) -> bool:
        try:
            response = httpx.post(
                self.settings.slack_webhook_url,
                json={"text": text},
                timeout=10,
            )
            return response.status_code < 300
        except httpx.HTTPError:
            return False

    def _send_bot_message(self, text: str) -> bool:
        try:
            response = httpx.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.settings.slack_bot_token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={"channel": self.settings.slack_channel_id, "text": text},
                timeout=10,
            )
            payload = response.json()
            return response.status_code < 300 and bool(payload.get("ok"))
        except (httpx.HTTPError, ValueError, AttributeError):
            return False
