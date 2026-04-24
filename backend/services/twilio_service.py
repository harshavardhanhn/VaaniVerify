from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from backend.config import get_settings


settings = get_settings()


class TwilioService:
    def __init__(self) -> None:
        self.enabled = settings.twilio_enabled
        self.client: Optional[Client] = None
        if self.enabled:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def initiate_call(self, to_phone: str, order_id: str, attempt: int = 1) -> str:
        if not self.enabled:
            return f"mock-call-{order_id}-{attempt}-{int(datetime.now(UTC).timestamp())}"

        if self.client is None:
            raise RuntimeError("Twilio client initialization failed.")

        webhook_url = f"{settings.public_base_url}/voice-webhook?order_id={order_id}&attempt={attempt}"

        try:
            call = self.client.calls.create(
                to=to_phone,
                from_=settings.twilio_phone_number,
                url=webhook_url,
                method="POST",
            )
            return call.sid
        except TwilioRestException as exc:
            raise RuntimeError(f"Twilio call failed: {exc.msg}") from exc


twilio_service = TwilioService()
