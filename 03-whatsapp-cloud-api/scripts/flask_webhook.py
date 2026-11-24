"""
Minimal Flask webhook: a code-only alternative to the n8n workflow, for
when n8n is unavailable.

Handles:
  - Meta's GET verification handshake (echoes hub.challenge)
  - POST inbound messages (extracts text, replies via Graph API)

Env vars required:
  WHATSAPP_ACCESS_TOKEN    - long-lived System User token
  WHATSAPP_PHONE_NUMBER_ID - the Cloud API sender's phone number ID
  WHATSAPP_VERIFY_TOKEN    - a string you invented, must match Meta's config

Run:
  pip install flask requests
  python flask_webhook.py

Then expose port 5000 with Cloudflare Tunnel:
  cloudflared tunnel --url http://localhost:5000
"""

import os
import logging

import requests
from flask import Flask, request, abort

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("wa-webhook")

app = Flask(__name__)

ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]
GRAPH_URL = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"


def send_text(to: str, body: str) -> None:
    r = requests.post(
        GRAPH_URL,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        },
        timeout=10,
    )
    log.info("send_text %s → %s", to, r.status_code)
    if not r.ok:
        log.warning("Graph API error: %s", r.text)


def send_template(to: str, name: str, params: list[str]) -> None:
    r = requests.post(
        GRAPH_URL,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": name,
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in params],
                    }
                ],
            },
        },
        timeout=10,
    )
    log.info("send_template %s (%s) → %s", to, name, r.status_code)
    if not r.ok:
        log.warning("Graph API error: %s", r.text)


@app.get("/webhook/whatsapp")
def verify():
    """Meta's verification handshake — must echo hub.challenge as plain text."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        log.info("Webhook verified")
        return challenge, 200
    log.warning("Verification failed: mode=%s token_ok=%s", mode, token == VERIFY_TOKEN)
    abort(403)


@app.post("/webhook/whatsapp")
def receive():
    """Inbound message handler. Always respond 200 quickly — Meta retries otherwise."""
    payload = request.get_json(silent=True) or {}
    try:
        change = payload["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError, TypeError):
        return {"status": "ignored"}, 200

    # Ignore status callbacks (delivery, read, etc.); only process real messages.
    messages = change.get("messages")
    if not messages:
        return {"status": "ignored"}, 200

    msg = messages[0]
    from_number = msg.get("from")
    msg_type = msg.get("type")
    contact = change.get("contacts", [{}])[0].get("profile", {}).get("name", "there")

    if msg_type != "text":
        send_text(from_number, "I can only understand text messages right now.")
        return {"status": "ok"}, 200

    text = (msg.get("text", {}).get("body") or "").strip()
    log.info("Inbound from %s (%s): %r", from_number, contact, text)

    if text.lower() == "template":
        send_template(from_number, "poc_welcome", [contact, "REF-DEMO"])
    else:
        send_text(
            from_number,
            f'Hi {contact}! You said: "{text}". This is an automated reply from '
            "the Cloud API PoC. Reply 'template' to receive the approved template.",
        )

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
