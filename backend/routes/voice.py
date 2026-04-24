from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from backend.config import get_settings
from backend.database import get_db
from backend.models.order import OrderStatus
from backend.routes.shared import log_call_event
from backend.services.intent import detect_intent
from backend.services.language import get_prompt, get_twilio_language, detect_language, get_twilio_voice
from backend.utils.object_id import parse_object_id


router = APIRouter(tags=["voice"])
settings = get_settings()


def _build_gather_response(order_id: str, language: str, attempt: int, key: str = "ask_confirm", order_details: str = "") -> Response:
    prompt = get_prompt(language, key).format(order_details=order_details)
    twilio_lang = get_twilio_language(language)
    twilio_voice = get_twilio_voice(language)

    voice_response = VoiceResponse()
    gather = Gather(
        input="dtmf speech",
        action=f"/voice-webhook?order_id={order_id}&attempt={attempt}",
        method="POST",
        num_digits=1,
        language=twilio_lang,
        speech_timeout="auto",
    )
    gather.say(prompt, language=twilio_lang, voice=twilio_voice)
    voice_response.append(gather)

    # Fallback when user gives no speech and Gather times out.
    voice_response.redirect(f"/voice-webhook?order_id={order_id}&attempt={attempt}", method="POST")
    return Response(content=str(voice_response), media_type="application/xml")


@router.post("/voice-webhook")
async def voice_webhook(request: Request, order_id: str, attempt: int = 1) -> Response:
    db = get_db()
    oid = parse_object_id(order_id)

    order = await db.orders.find_one({"_id": oid})
    if not order:
        response = VoiceResponse()
        response.say("Order not found. Goodbye.", voice="Polly.Raveena")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    language = order.get("language_preference", "pending")
    form_data = await request.form()
    speech_result = (form_data.get("SpeechResult") or "").strip()
    digits = (form_data.get("Digits") or "").strip()

    # Step 1: Language is pending, we need to ask or process language selection.
    if language == "pending":
        if attempt > settings.max_retries:
            response = VoiceResponse()
            response.say("We could not capture a clear response. Our team will follow up shortly.", voice="Polly.Raveena")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        detected_lang = None
        if digits == "1":
            detected_lang = "en"
        elif digits == "2":
            detected_lang = "hi"
        elif digits == "3":
            detected_lang = "kn"
        elif digits == "4":
            detected_lang = "mr"
        elif speech_result:
            detected_lang = detect_language(speech_result)

        if detected_lang:
            await db.orders.update_one(
                {"_id": oid},
                {"$set": {"language_preference": detected_lang, "updated_at": datetime.now(UTC)}}
            )
            await log_call_event(db, order_id=order_id, event="LANGUAGE_SELECTED", detail=f"User selected {detected_lang}")
            return _build_gather_response(order_id, detected_lang, 1, key="ask_confirm", order_details=order.get("order_details", ""))
        
        if speech_result or digits:
            await log_call_event(db, order_id=order_id, event="LANGUAGE_NOT_DETECTED", detail=f"Speech: {speech_result}, Digits: {digits}")
        
        vr = VoiceResponse()
        gather = Gather(
            input="dtmf speech",
            action=f"/voice-webhook?order_id={order_id}&attempt={attempt}",
            method="POST",
            num_digits=1,
            language="en-IN",
            timeout=5
        )
        gather.say("For English, press 1 or say English.", language="en-IN", voice="Polly.Raveena")
        gather.say("हिंदी के लिए, 2 दबाएं या हिंदी बोलें।", language="hi-IN", voice="Polly.Aditi")
        gather.say("ಕನ್ನಡಕ್ಕಾಗಿ, 3 ಒತ್ತಿ ಅಥವಾ ಕನ್ನಡ ಎಂದು ಹೇಳಿ.", language="kn-IN", voice="Google.kn-IN-Standard-A")
        gather.say("मराठीसाठी, 4 दाबा किंवा मराठी बोला.", language="mr-IN", voice="Google.mr-IN-Standard-B")
        vr.append(gather)
        vr.redirect(f"/voice-webhook?order_id={order_id}&attempt={attempt + 1}", method="POST")
        return Response(content=str(vr), media_type="application/xml")

    # Step 2: Language is already selected, process confirmation.
    if not speech_result:
        if attempt < settings.max_retries:
            await db.orders.update_one(
                {"_id": oid},
                {"$set": {"updated_at": datetime.now(UTC)}, "$inc": {"retry_count": 1}},
            )
            await log_call_event(
                db,
                order_id=order_id,
                event="NO_RESPONSE",
                detail=f"No speech detected. Retrying attempt {attempt + 1}.",
            )
            return _build_gather_response(order_id, language, attempt + 1, key="no_response", order_details=order.get("order_details", ""))

        await log_call_event(
            db,
            order_id=order_id,
            event="MAX_RETRIES",
            detail="No response after max retries.",
        )
        response = VoiceResponse()
        response.say(get_prompt(language, "max_retries"), language=get_twilio_language(language), voice=get_twilio_voice(language))
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    intent = "unknown"
    if digits == "1":
        intent = "yes"
    elif digits == "2":
        intent = "no"
    else:
        intent = detect_intent(speech_result)

    await log_call_event(
        db,
        order_id=order_id,
        event="USER_RESPONSE",
        detail=f"Speech: {speech_result} | Digits: {digits} | Intent: {intent}",
    )

    response = VoiceResponse()

    if intent == "yes":
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": OrderStatus.confirmed.value,
                    "last_intent": "yes",
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        response.say(get_prompt(language, "confirmed"), language=get_twilio_language(language), voice=get_twilio_voice(language))
        response.hangup()
        await log_call_event(db, order_id=order_id, event="ORDER_CONFIRMED", detail="Order confirmed by customer.")
        return Response(content=str(response), media_type="application/xml")

    if intent == "no":
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {
                    "status": OrderStatus.cancelled.value,
                    "last_intent": "no",
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        response.say(get_prompt(language, "cancelled"), language=get_twilio_language(language), voice=get_twilio_voice(language))
        response.hangup()
        await log_call_event(db, order_id=order_id, event="ORDER_CANCELLED", detail="Order cancelled by customer.")
        return Response(content=str(response), media_type="application/xml")

    if intent == "repeat" and attempt < settings.max_retries:
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {"last_intent": "repeat", "updated_at": datetime.now(UTC)},
                "$inc": {"retry_count": 1},
            },
        )
        await log_call_event(
            db,
            order_id=order_id,
            event="REPEAT_REQUESTED",
            detail=f"Customer requested repeat. Attempt {attempt + 1}",
        )
        return _build_gather_response(order_id, language, attempt + 1, key="repeat", order_details=order.get("order_details", ""))

    if attempt < settings.max_retries:
        await db.orders.update_one(
            {"_id": oid},
            {
                "$set": {"last_intent": "unknown", "updated_at": datetime.now(UTC)},
                "$inc": {"retry_count": 1},
            },
        )
        await log_call_event(
            db,
            order_id=order_id,
            event="UNCLEAR_RESPONSE",
            detail=f"Unclear response. Retrying attempt {attempt + 1}",
        )
        return _build_gather_response(order_id, language, attempt + 1, key="unclear", order_details=order.get("order_details", ""))

    response.say(get_prompt(language, "max_retries"), language=get_twilio_language(language), voice=get_twilio_voice(language))
    response.hangup()
    await log_call_event(db, order_id=order_id, event="MAX_RETRIES", detail="Unclear response after max retries.")
    return Response(content=str(response), media_type="application/xml")
