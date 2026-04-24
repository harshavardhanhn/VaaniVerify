from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import Gather, VoiceResponse

from backend.config import get_settings
from backend.database import get_db
from backend.models.order import OrderStatus
from backend.routes.shared import log_call_event
from backend.services.intent import detect_intent
from backend.services.language import get_prompt, get_twilio_language
from backend.utils.object_id import parse_object_id


router = APIRouter(tags=["voice"])
settings = get_settings()


def _build_gather_response(order_id: str, language: str, attempt: int, key: str = "ask_confirm") -> Response:
    prompt = get_prompt(language, key)
    twilio_lang = get_twilio_language(language)

    voice_response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"/voice-webhook?order_id={order_id}&attempt={attempt}",
        method="POST",
        language=twilio_lang,
        speech_timeout="auto",
    )
    gather.say(prompt, language=twilio_lang)
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
        response.say("Order not found. Goodbye.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    language = order.get("language_preference", "en")
    form_data = await request.form()
    speech_result = (form_data.get("SpeechResult") or "").strip()

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
            return _build_gather_response(order_id, language, attempt + 1, key="no_response")

        await log_call_event(
            db,
            order_id=order_id,
            event="MAX_RETRIES",
            detail="No response after max retries.",
        )
        response = VoiceResponse()
        response.say(get_prompt(language, "max_retries"), language=get_twilio_language(language))
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    intent = detect_intent(speech_result)
    await log_call_event(
        db,
        order_id=order_id,
        event="USER_RESPONSE",
        detail=f"Speech: {speech_result} | Intent: {intent}",
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
        response.say(get_prompt(language, "confirmed"), language=get_twilio_language(language))
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
        response.say(get_prompt(language, "cancelled"), language=get_twilio_language(language))
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
        return _build_gather_response(order_id, language, attempt + 1, key="repeat")

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
        return _build_gather_response(order_id, language, attempt + 1, key="unclear")

    response.say(get_prompt(language, "max_retries"), language=get_twilio_language(language))
    response.hangup()
    await log_call_event(db, order_id=order_id, event="MAX_RETRIES", detail="Unclear response after max retries.")
    return Response(content=str(response), media_type="application/xml")
