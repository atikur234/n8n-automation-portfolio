# WhatsApp Cloud API Automation with Coexistence (n8n + Meta + Cloudflare Tunnel)

A WhatsApp automation proof of concept built on Meta's WhatsApp Business Cloud API, using n8n for the workflow logic and Cloudflare Tunnel for a public HTTPS webhook. It supports **coexistence**: the same phone number stays active in the WhatsApp Business App on a physical phone while the API automation runs. A human and the bot can work the same conversations.

Built as a technical assessment for an AI Automation Intern role.

## Architecture

```
User's WhatsApp ──► Meta Cloud API ──► Cloudflare Tunnel ──► n8n webhook ──► logic ──► Graph API ──► User's WhatsApp
                          ▲                                                                   │
                          └───── same conversation, visible in the WhatsApp Business App ─────┘
                                                   (coexistence)
```

## What's implemented

- Meta Developer App with the WhatsApp product, plus a permanent System User token (never expires)
- Webhook verification: the GET branch checks the verify token and echoes `hub.challenge`
- Inbound message handling: the POST branch parses Meta's nested payload, ignores status callbacks, and replies through the Graph API
- An approved **Utility** message template (`poc_welcome`) with variables, sent when the user types `template`
- **Coexistence**: the number is registered in the WhatsApp Business App and connected to the Cloud API, and both share the same thread
- Public HTTPS through a Cloudflare quick tunnel

## The n8n workflow

| Node | Purpose |
|---|---|
| Webhook (GET verify) → IF verify token matches → Echo `hub.challenge` (200) / Reject (403) | Meta's subscription handshake |
| Webhook (POST message) → IF is a message (not status) | Ignore delivery and read receipts |
| Extract message fields | Pull out the sender, name, message type and text |
| IF text = `template` → Send Template / Send Text Reply | Graph API `/messages` calls; the token is read from the `WHATSAPP_ACCESS_TOKEN` environment variable |
| Respond 200 | Acknowledge quickly so Meta doesn't retry |

## Files

| File | What it is |
|---|---|
| `workflows/whatsapp-cloud-api-poc.json` | n8n workflow export. Credentials are references, not values. |
| `scripts/flask_webhook.py` | Code-only alternative to the n8n workflow (Flask): verify handshake + auto-reply |
| `.env.example` | Required environment variables (placeholders only) |
| `docs/meta-setup.md` | Meta app, WABA, System User token |
| `docs/coexistence.md` | How coexistence is configured, and the Coexistence vs Migrate trap |
| `docs/templates.md` | Template categories, approval, sending with variables |
| `docs/webhook-payloads.md` | Reference payloads for verify, message and status events |
| `docs/cloudflare-tunnel.md` | Getting a public HTTPS URL |
| `docs/workflow-walkthrough.md` | Node-by-node walkthrough |
| `docs/troubleshooting.md` | Symptom → fix list |

## Run it

1. Copy `.env.example` to `.env` and fill in your token, phone number ID and verify token.
2. Start a tunnel: `cloudflared tunnel --url http://localhost:5678`
3. Start n8n with `WEBHOOK_URL` set to the tunnel URL:
   ```bash
   docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n \
     -e WEBHOOK_URL=https://<your-tunnel>.trycloudflare.com/ --env-file .env \
     docker.n8n.io/n8nio/n8n
   ```
4. Import the workflow and activate it. The HTTP nodes read the token and phone number ID from the environment variables.
5. In the Meta app, go to **WhatsApp → Configuration**. Set the callback URL to `https://<tunnel>/webhook/whatsapp`, enter your verify token, click **Verify and save**, and subscribe to `messages`.
6. Test it: send `hello` (you get an automated reply), then `template` (you get the approved template). Then reply by hand from the Business App on the phone, and check that the next inbound message still fires the webhook.

## What I'd add for production

- Verify `X-Hub-Signature-256` against the app secret
- Store conversation state in Postgres
- Generate replies with an LLM between the parser and the reply node
- Use a named tunnel or a hosted deployment for a stable URL; move the Meta app to Live mode
