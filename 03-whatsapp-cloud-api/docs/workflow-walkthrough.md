# n8n Workflow Build

This is the actual automation. It receives Meta's webhook (verify + messages), parses inbound text, and sends an automated reply. A separate branch handles template sends.

## Prerequisites

- n8n running locally (Docker or `npx n8n`) on port 5678.
- A Cloudflare Tunnel pointing at `http://localhost:5678` (see `cloudflare-tunnel.md`).
- Your Meta credentials: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, and a `WHATSAPP_VERIFY_TOKEN` string you invented.

## Running n8n locally (fastest way)

Docker one-liner:

```bash
docker run -it --rm \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_SECURE_COOKIE=false \
  -e WEBHOOK_URL=https://<your-tunnel-subdomain>.trycloudflare.com/ \
  docker.n8n.io/n8nio/n8n
```

The `WEBHOOK_URL` env var is important — it tells n8n what public URL to show you for its Webhook nodes. Without it, n8n prints `http://localhost:5678/...` which Meta cannot reach.

Open http://localhost:5678, create the owner account, you're in.

## Import the bundled workflow

1. From n8n's UI, click **Workflows** → the "⋯" menu → **Import from File**.
2. Select `workflows/whatsapp-cloud-api-poc.json` from this folder.
3. The workflow appears with the following nodes wired up:

```
[Webhook: whatsapp]
        │
        ▼
[IF: is verification (GET)?]
   │yes            │no
   ▼               ▼
[Respond hub.challenge]   [Extract message]
                                  │
                                  ▼
                           [IF: text = "template"?]
                              │yes          │no
                              ▼             ▼
                       [Send Template]  [Send Text Reply]
                              │             │
                              └─────┬───────┘
                                    ▼
                             [Respond 200 OK]
```

## Node-by-node configuration

### 1. Webhook node (`whatsapp`)

- HTTP Method: **Both** (accepts GET and POST). If your n8n version doesn't offer "Both", create two Webhook nodes on the same path — one GET, one POST.
- Path: `whatsapp` → full URL will be `https://<tunnel>.trycloudflare.com/webhook/whatsapp`.
- Response: **Using Respond to Webhook node** (so we control the response per branch).
- Authentication: **None** (Meta signs requests but doesn't do HTTP Basic; you'll verify the signature later if you have time — optional for the PoC).

### 2. IF node — "is verification"

- Condition: `{{ $json.query["hub.mode"] }}` equals `subscribe`.
- Meta sends the verify GET with query params `hub.mode`, `hub.verify_token`, `hub.challenge`.

### 3. Respond hub.challenge

- Use a **Respond to Webhook** node.
- Response body: `{{ $json.query["hub.challenge"] }}` (plain text).
- Response code: `200`.
- ALSO check that `{{ $json.query["hub.verify_token"] }}` equals your `WHATSAPP_VERIFY_TOKEN` — if not, respond with 403. The bundled workflow includes this check.

### 4. Extract message (Set node)

Pull the key fields out of the deeply-nested payload:

- `phone_number` = `{{ $json.body.entry[0].changes[0].value.messages[0].from }}`
- `text` = `{{ $json.body.entry[0].changes[0].value.messages[0].text.body }}`
- `message_id` = `{{ $json.body.entry[0].changes[0].value.messages[0].id }}`
- `contact_name` = `{{ $json.body.entry[0].changes[0].value.contacts[0].profile.name }}`

Guard against non-text message types (images, stickers, status updates) with an IF node: only proceed when `messages[0].type == 'text'`.

### 5. IF: text = "template"

- Condition: `{{ $json.text.toLowerCase() }}` equals `template`.
- This lets you trigger the template send live during the video demo by messaging the bot `template`.

### 6. Send Template (HTTP Request node)

- Method: POST
- URL: `https://graph.facebook.com/v20.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages`
- Authentication: Header Auth → Header name `Authorization`, value `Bearer {{ $env.WHATSAPP_ACCESS_TOKEN }}` (use n8n credentials rather than env if you prefer).
- Body: JSON
  ```json
  {
    "messaging_product": "whatsapp",
    "to": "{{ $json.phone_number }}",
    "type": "template",
    "template": {
      "name": "poc_welcome",
      "language": {"code": "en"},
      "components": [
        {
          "type": "body",
          "parameters": [
            {"type": "text", "text": "{{ $json.contact_name }}"},
            {"type": "text", "text": "REF-{{ $now.toMillis() }}"}
          ]
        }
      ]
    }
  }
  ```

### 7. Send Text Reply (HTTP Request node)

Same URL/auth as Send Template, but body:

```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.phone_number }}",
  "type": "text",
  "text": {
    "body": "Hi {{ $json.contact_name }}! You said: \"{{ $json.text }}\". This is an automated reply from the Cloud API PoC. Reply 'template' to receive an approved template message."
  }
}
```

### 8. Respond 200 OK

- **Respond to Webhook** node with body `{"status":"ok"}` and code `200`.
- Meta will retry your webhook if it doesn't get a 200 within a few seconds — so always respond, even if downstream processing fails.

## Credentials — do it properly

Don't hardcode the token in the HTTP Request node. In n8n:

1. **Credentials → Add Credential → Header Auth**.
2. Name: `Meta WhatsApp Cloud API`.
3. Header Name: `Authorization`.
4. Header Value: `Bearer YOUR_ACCESS_TOKEN`.
5. In each HTTP Request node, set Authentication → Predefined Credential Type → Header Auth → select the credential.

Same for the verify token — store it in an env var (`WHATSAPP_VERIFY_TOKEN`) and reference `{{ $env.WHATSAPP_VERIFY_TOKEN }}` in the IF node.

When you export the workflow for GitHub, n8n replaces the credential value with an ID reference — safe to commit. Double-check anyway before pushing.

## Activate

Save, then toggle **Active** in the top right of the workflow editor. Only active workflows respond on their production webhook URLs. The URL you paste into Meta's Configuration is the **production** URL (`/webhook/whatsapp`), not the test URL (`/webhook-test/whatsapp`).

## First live test

1. In Meta app → WhatsApp → Configuration, click **Verify and save** for your callback URL. Should turn green.
2. From your personal WhatsApp, message the Cloud API number: "hello".
3. Watch n8n's **Executions** tab — you should see a fresh execution with all nodes green.
4. Check your WhatsApp — you should get the automated reply.
5. Message "template" — you should get the approved template.

If any step fails, see `troubleshooting.md`.
