# Meta Developer App & WhatsApp Cloud API Setup

This walks through the Meta side end-to-end. Expect 60–90 minutes the first time — most of it is UI navigation, not actual work.

## Prerequisites

- A Facebook account (personal is fine for the developer account).
- A **real, unused phone number** that can receive an SMS or voice call for verification. It cannot be currently registered on any consumer WhatsApp account. If it is, uninstall WhatsApp on that number's device and let 24h pass, or use a different SIM.
- The WhatsApp **Business** App (green briefcase icon) installed on the physical phone that will hold the number. Not the consumer app.

## 1. Create a Meta Business Portfolio (formerly Business Manager)

1. Go to https://business.facebook.com.
2. Create a new business portfolio if you don't already have one. Name it whatever you like; evaluators don't see it.
3. Note the **Business Portfolio ID** — you'll see it in Settings → Business Info.

## 2. Create a Meta Developer App

1. Go to https://developers.facebook.com/apps and click **Create App**.
2. Use case: pick **Other**, then app type: **Business**.
3. Name the app (e.g., `wa-cloud-poc`), pick your business portfolio from step 1, submit.
4. On the app dashboard, scroll to **Add products to your app** and click **Set up** on **WhatsApp**.

## 3. Set up WhatsApp inside the app

After clicking Set up on WhatsApp, Meta will either:
- Auto-provision a test WABA and a test phone number, OR
- Ask you to link an existing WABA.

You will later replace the test number with your real number via Coexistence (see `coexistence.md`). For now, note down:
- **App ID** (top of the app dashboard)
- **App Secret** (Settings → Basic → Show, requires password)
- **WABA ID** (WhatsApp → API Setup, "WhatsApp Business Account ID")
- **Test Phone Number ID** (WhatsApp → API Setup, under "From")
- **Temporary access token** (WhatsApp → API Setup, top of page — valid 24h)

## 4. Get a permanent access token (do this — 24h tokens will bite you mid-demo)

Temporary tokens expire in 24h and will silently break your workflow.

1. In the Meta Business Portfolio → Settings → Users → **System Users**, click **Add**.
2. Name it something like `wa-poc-system-user`, give it **Admin** role.
3. Click the new system user → **Add Assets** → select your WhatsApp Business Account → give it **Full control**.
4. Click **Generate new token** on the system user. Select your app. Grant these scopes at minimum:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. Set expiration to **Never**. Copy the token immediately — Meta won't show it again.

This is now your production token. Store it in n8n credentials and in your local `.env`. Never commit it.

## 5. Sanity check with curl

Confirm the token works before you touch n8n:

```bash
curl -X POST "https://graph.facebook.com/v20.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "<YOUR_PERSONAL_WHATSAPP_NUMBER_WITH_COUNTRY_CODE_NO_PLUS>",
    "type": "text",
    "text": {"body": "Hello from Cloud API"}
  }'
```

If the number you're sending **to** hasn't messaged your Cloud API number in the last 24h, this will fail with a "recipient not in allowed list" style error unless the recipient is a WhatsApp test recipient added on the API Setup page. To bypass this constraint for the first test:
- On the API Setup page, add your personal WhatsApp number under **Recipient phone numbers** and complete the confirmation code.
- Retry — you should receive the message.

## 6. Configure the webhook (do this after n8n + Cloudflare Tunnel are up)

In the app dashboard → WhatsApp → **Configuration**:

- **Callback URL**: your Cloudflare Tunnel URL + the n8n webhook path (e.g., `https://friendly-otter-12.trycloudflare.com/webhook/whatsapp`).
- **Verify token**: a string you invent (e.g., `poc_verify_2026`). It must match exactly what you set in the n8n workflow.
- Click **Verify and save**. Meta will hit your webhook with a `GET` — if you get a green check, the handshake worked. If not → `references/troubleshooting.md`.

Then click **Manage** next to Webhook fields and subscribe to at least:
- `messages` (inbound user messages)
- Optionally `message_template_status_update` (see template approvals live)

## 7. What you should now have

- App ID + App Secret (documented in your `.env`)
- WABA ID
- Phone Number ID (test for now; real number after Coexistence)
- **Permanent** access token
- A verify token string
- Webhook subscribed to `messages`

You're ready to move on to Coexistence setup.
