from backend.services.language import get_prompt, get_twilio_language


class TTSService:
    """TTS phrase selector for Twilio <Say>.

    For local demo this uses Twilio voice language directly.
    Can be replaced by Google TTS / Polly URL audio playback in production.
    """

    @staticmethod
    def get_spoken_prompt(language: str, key: str) -> tuple[str, str]:
        return get_prompt(language, key), get_twilio_language(language)


tts_service = TTSService()
