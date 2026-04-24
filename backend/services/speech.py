from typing import Optional


class SpeechService:
    """Speech normalization layer.

    Twilio already provides speech-to-text via SpeechResult in webhook payload.
    This class keeps the architecture extensible for future Whisper/Google STT usage.
    """

    @staticmethod
    def transcribe_from_twilio(speech_result: Optional[str]) -> str:
        return (speech_result or "").strip()


speech_service = SpeechService()
