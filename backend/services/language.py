SUPPORTED_LANGUAGES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "mr": "mr-IN",
}

TWILIO_VOICES = {
    "en": "Polly.Raveena",
    "hi": "Polly.Aditi",
    "kn": "Google.kn-IN-Standard-A",
    "mr": "Google.mr-IN-Standard-B",
}

PROMPTS = {
    "en": {
        "ask_confirm": "Hello, this is Automaton AI. Your order is for {order_details}. Do you confirm your order? Please say Yes or press 1, say No or press 2.",
        "confirmed": "Thank you. Your order is confirmed.",
        "cancelled": "Your order has been cancelled.",
        "repeat": "Sure. I will repeat the question.",
        "unclear": "Sorry, I did not understand. Please say Yes or press 1.",
        "no_response": "We could not hear you. Please respond with Yes or No, or press 1 or 2.",
        "max_retries": "We could not capture a clear response. Our team will follow up shortly.",
    },
    "hi": {
        "ask_confirm": "नमस्ते, यह Automaton AI है। आपका ऑर्डर {order_details} के लिए है। कन्फर्म करने के लिए हाँ कहें या 1 दबाएं, रद्द करने के लिए नहीं कहें या 2 दबाएं।",
        "confirmed": "धन्यवाद। आपका ऑर्डर कन्फर्म हो गया है।",
        "cancelled": "आपका ऑर्डर रद्द कर दिया गया है।",
        "repeat": "ठीक है। मैं सवाल दोबारा पूछता हूँ।",
        "unclear": "माफ़ कीजिए, मैं समझ नहीं पाया। कृपया हाँ कहें या 1 दबाएं।",
        "no_response": "हमें आपकी आवाज़ सुनाई नहीं दी। कृपया हाँ या नहीं कहें, या 1 और 2 दबाएं।",
        "max_retries": "हमें स्पष्ट जवाब नहीं मिला। हमारी टीम आपसे जल्द संपर्क करेगी।",
    },
    "kn": {
        "ask_confirm": "ನಮಸ್ಕಾರ, ಇದು Automaton AI. ನಿಮ್ಮ ಆದೇಶವು {order_details} ಗಾಗಿ. ದೃಢೀಕರಿಸಲು ಹೌದು ಎಂದು ಹೇಳಿ ಅಥವಾ 1 ಒತ್ತಿ, ರದ್ದುಗೊಳಿಸಲು ಇಲ್ಲ ಎಂದು ಹೇಳಿ ಅಥವಾ 2 ಒತ್ತಿ.",
        "confirmed": "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಆದೇಶ ದೃಢೀಕರಿಸಲಾಗಿದೆ.",
        "cancelled": "ನಿಮ್ಮ ಆದೇಶ ರದ್ದುಗೊಂಡಿದೆ.",
        "repeat": "ಸರಿ. ನಾನು ಪ್ರಶ್ನೆಯನ್ನು ಮತ್ತೊಮ್ಮೆ ಕೇಳುತ್ತೇನೆ.",
        "unclear": "ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಹೌದು ಎಂದು ಹೇಳಿ ಅಥವಾ 1 ಒತ್ತಿ.",
        "no_response": "ನಿಮ್ಮ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಹೌದು ಅಥವಾ ಇಲ್ಲ ಎಂದು ಹೇಳಿ, ಅಥವಾ 1 ಮತ್ತು 2 ಒತ್ತಿ.",
        "max_retries": "ಸ್ಪಷ್ಟ ಉತ್ತರ ಸಿಗಲಿಲ್ಲ. ನಮ್ಮ ತಂಡ ಶೀಘ್ರದಲ್ಲೇ ಸಂಪರ್ಕಿಸುತ್ತದೆ.",
    },
    "mr": {
        "ask_confirm": "नमस्कार, हे Automaton AI आहे. तुमची ऑर्डर {order_details} साठी आहे. कन्फर्म करण्यासाठी होय म्हणा किंवा 1 दाबा, रद्द करण्यासाठी नाही म्हणा किंवा 2 दाबा.",
        "confirmed": "धन्यवाद. तुमची ऑर्डर कन्फर्म झाली आहे.",
        "cancelled": "तुमची ऑर्डर रद्द करण्यात आली आहे.",
        "repeat": "ठीक आहे. मी प्रश्न पुन्हा विचारतो.",
        "unclear": "माफ करा, मला समजले नाही. कृपया होय म्हणा किंवा 1 दाबा.",
        "no_response": "तुमचा आवाज ऐकू आला नाही. कृपया होय किंवा नाही म्हणा, किंवा 1 आणि 2 दाबा.",
        "max_retries": "स्पष्ट उत्तर मिळाले नाही. आमची टीम लवकरच संपर्क करेल.",
    },
}


def normalize_language(language: str) -> str:
    lang = (language or "").lower().strip()
    if lang == "pending":
        return lang
    if lang not in SUPPORTED_LANGUAGES:
        return "en"
    return lang


def get_prompt(language: str, key: str) -> str:
    lang = normalize_language(language)
    return PROMPTS[lang][key]


def get_twilio_language(language: str) -> str:
    return SUPPORTED_LANGUAGES[normalize_language(language)]

def get_twilio_voice(language: str) -> str:
    return TWILIO_VOICES[normalize_language(language)]

def detect_language(speech: str) -> str | None:
    speech = speech.lower().strip()
    if "english" in speech or "angrezi" in speech: return "en"
    if "hindi" in speech or "hind" in speech: return "hi"
    if "kannada" in speech or "kanada" in speech or "canada" in speech: return "kn"
    if "marathi" in speech or "marati" in speech: return "mr"
    return None
