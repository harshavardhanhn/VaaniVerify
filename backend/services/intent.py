from typing import Optional


YES_WORDS = {
    "yes", "yeah", "yup", "confirm", "confirmed", "haan", "ha", "ji", "okay", "ok", "correct",
    "howdu", "houdu", "yesu", "ho", "हो", "हाँ", "हां", "होय", "बरोबर", "ಸರಿ", "ಹೌದು"
}
NO_WORDS = {
    "no", "nope", "cancel", "nah", "nahi", "mat", "beda", "beda", "ಬೇಡ", "नहीं", "नको", "नाही"
}
REPEAT_WORDS = {
    "repeat", "again", "what", "once more", "phirse", "fir se", "dubaara", "punha", "ಮತ್ತೆ",
    "फिर", "फिरसे", "पुन्हा"
}


def detect_intent(text: Optional[str]) -> str:
    if not text:
        return "unknown"

    cleaned = text.strip().lower()
    if not cleaned:
        return "unknown"

    if any(word in cleaned for word in YES_WORDS):
        return "yes"
    if any(word in cleaned for word in NO_WORDS):
        return "no"
    if any(word in cleaned for word in REPEAT_WORDS):
        return "repeat"
    return "unknown"
