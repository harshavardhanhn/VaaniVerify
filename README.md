# Multilingual Voice Assistance Bot for Automated Order Confirmation Calls

Production-ready but hackathon-optimized system that auto-calls customers and confirms or cancels orders using voice interactions.

## 1) Project Folder Structure

```text
VaaniVerify/
  backend/
    __init__.py
    config.py
    database.py
    main.py
    models/
      __init__.py
      order.py
    routes/
      __init__.py
      calls.py
      orders.py
      shared.py
      voice.py
    services/
      __init__.py
      intent.py
      language.py
      speech.py
      tts.py
      twilio_service.py
    utils/
      __init__.py
      object_id.py
  frontend/
    index.html
  sample_data/
    sample_orders.json
  .env.example
  .gitignore
  requirements.txt
  README.md
```

## 2) System Architecture

- Backend: FastAPI (Python)
- Voice API: Twilio Programmable Voice
- Speech-to-Text: Twilio speech recognition (`<Gather input="speech">`)
- Text-to-Speech: Twilio `<Say>` with language-specific voices (extensible to Google TTS / Polly)
- Database: MongoDB (via Motor async client)
- Frontend: Lightweight dashboard (HTML/JS) for live demo

Flow:
1. Create order via API/UI.
2. System triggers outbound call.
3. Customer hears localized prompt and replies by voice.
4. Intent detector classifies reply (`yes`, `no`, `repeat`, `unknown`).
5. Order status updates in MongoDB (`Pending`, `Confirmed`, `Cancelled`).
6. Call events are saved as logs and shown in dashboard.

## 3) Complete Backend APIs

### `POST /create-order`
Creates an order and (optionally) auto-triggers call.

Request body:
```json
{
  "customer_name": "Ravi Kumar",
  "phone_number": "+919876543210",
  "order_details": "1x Mixer Grinder",
  "language_preference": "kn",
  "auto_trigger_call": true
}
```

### `POST /trigger-call`
Manually trigger outbound call for an existing order.

Request body:
```json
{
  "order_id": "6809f4fbc4f0db44a9d93452"
}
```

### `POST /voice-webhook`
Twilio webhook endpoint that handles voice responses, retry logic, and status updates.

### `GET /orders`
Returns latest orders for dashboard.

### `GET /logs?limit=50`
Returns call logs for dashboard and demo visibility.

## 4) Twilio Setup Guide

1. Create a Twilio free account and buy/verify a voice-enabled number.
2. Start your local backend.
3. Expose local server publicly (for Twilio webhooks):
   - `ngrok http 8000`
4. Copy public URL into `.env` as `PUBLIC_BASE_URL`.
5. Set Twilio credentials in `.env`:
   - `TWILIO_ENABLED=true`
   - `TWILIO_ACCOUNT_SID=...`
   - `TWILIO_AUTH_TOKEN=...`
   - `TWILIO_PHONE_NUMBER=+1...`
6. Restart app.
7. Trigger order/call from dashboard or API.

Notes:
- If `TWILIO_ENABLED=false`, app uses mock call IDs so local demo still works without real calls.
- For actual calls, destination phone numbers must be E.164 format.

## 5) Local Setup (Step-by-Step)

1. Install MongoDB locally and start it on `mongodb://localhost:27017`.
2. Create and activate Python virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill values.
5. Run app:
   - `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
6. Open dashboard:
   - `http://localhost:8000`

## 6) API Usage Examples

Create order:
```bash
curl -X POST http://localhost:8000/create-order \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name":"Asha",
    "phone_number":"+919900001234",
    "order_details":"2x Organic Honey",
    "language_preference":"hi",
    "auto_trigger_call":true
  }'
```

Manual trigger call:
```bash
curl -X POST http://localhost:8000/trigger-call \
  -H "Content-Type: application/json" \
  -d '{"order_id":"<ORDER_ID>"}'
```

List orders:
```bash
curl http://localhost:8000/orders
```

Fetch logs:
```bash
curl http://localhost:8000/logs?limit=20
```

## 7) Multilingual Support

Supported language keys:
- `en` (English)
- `hi` (Hindi)
- `kn` (Kannada)
- `mr` (Marathi)

The bot speaks and listens using language-specific prompts and Twilio speech language codes.

## 8) Intent Detection

Rule-based classifier in `backend/services/intent.py`:
- `yes`
- `no`
- `repeat`
- `unknown`

Designed for high reliability in hackathon conditions. Easy to swap with ML/NLU later.

## 9) Retry and Error Handling

- No response: retry up to `MAX_RETRIES` (default 2)
- Unclear speech: retry with clarification prompt
- Repeat intent: replay question
- After max retries: keep status as pending, log follow-up event

## 10) Demo Walkthrough (What to Show Judges)

1. Open dashboard on localhost.
2. Create one English order and one regional-language order.
3. Show log entry: `CALL_INITIATED`.
4. Receive call on phone and answer:
   - Say "Yes" for first order -> status changes to `Confirmed`.
   - Say "No" for second order -> status changes to `Cancelled`.
5. Show logs:
   - `USER_RESPONSE`
   - `ORDER_CONFIRMED` / `ORDER_CANCELLED`
6. Show retry path by giving unclear answer:
   - Logs show `UNCLEAR_RESPONSE` and retry attempts.

## 11) Production Hardening Suggestions

- Add auth for APIs (JWT/API keys)
- Add request validation for phone formats
- Add idempotency keys for call triggers
- Add Redis queue for async call scheduling
- Add role-based admin dashboard
- Add observability (structured logs + metrics)

---

This project is optimized for reliability, clear architecture, and a polished demo while remaining simple to run locally.
