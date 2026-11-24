# Meta Message Templates

Templates are pre-approved messages you're allowed to send outside the 24-hour customer service window. The assessment requires at least one working template send.

## Why templates exist

WhatsApp rules: once a user messages your business, you have 24 hours to reply freely with any content. After that window closes, you can *only* send a message that matches a pre-approved template. This stops businesses from spamming.

Templates come in three categories:
- **Utility** — order updates, appointment reminders, OTP, receipts. Approves in minutes. Use this for the assessment.
- **Authentication** — one-time passcodes only. Restrictive format.
- **Marketing** — promos, offers. Approves in hours to days, and can be rejected for vague or spammy copy.

## Create a template (fastest path)

1. Meta Business Suite → WhatsApp Manager → **Message Templates** → **Create Template**.
2. Category: **Utility**.
3. Name: `poc_welcome` (lowercase, underscores, ≤ 512 chars, no special chars). This is the identifier your API calls will reference.
4. Language: **English** (or whatever you'll test in — must match the API call exactly).
5. Header: optional. Skip for the first template.
6. Body:
   ```
   Hi {{1}}, thanks for reaching out to our automation demo. Your reference number is {{2}}. A human agent will get back to you shortly.
   ```
   `{{1}}` and `{{2}}` are variables you'll fill in per send.
7. Footer: optional (e.g., "Automated message — do not reply to this SMS").
8. Buttons: skip for the first template.
9. Sample values: provide realistic samples for `{{1}}` and `{{2}}` (e.g., "Atiq", "REF-1042"). Meta rejects templates without them.
10. Submit for review.

Utility templates with sensible copy typically approve in **1–15 minutes**. Watch the status in WhatsApp Manager → Message Templates.

## Send an approved template

Once approved:

```bash
curl -X POST "https://graph.facebook.com/v20.0/<PHONE_NUMBER_ID>/messages" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "<RECIPIENT_MSISDN>",
    "type": "template",
    "template": {
      "name": "poc_welcome",
      "language": {"code": "en"},
      "components": [
        {
          "type": "body",
          "parameters": [
            {"type": "text", "text": "Atiq"},
            {"type": "text", "text": "REF-1042"}
          ]
        }
      ]
    }
  }'
```

Key things to get right:
- `template.name` matches your template name exactly.
- `template.language.code` matches the template's language (e.g., `en` not `en_US` unless you registered `en_US`).
- Parameter order matches `{{1}}`, `{{2}}`, … in the body.

## Wire it into n8n

The bundled workflow (`scripts/n8n-workflow.json`) has a **"Send Template"** node that's disabled by default. To use it:

1. Open the node, update `name` and `parameters` to your template.
2. Enable the node.
3. Trigger it manually (n8n → Execute node) with a test recipient number.

For the demo, put a small trigger — e.g., "send template when incoming message text equals `template`" — so you can trigger it live on video.

## What to include in your README

- The exact template name, category, language.
- The template body (with the `{{n}}` placeholders visible).
- A screenshot of the "Approved" status from WhatsApp Manager (redact IDs).
- One sample API request that triggers the template.

## What to avoid

- Don't submit "Marketing" for the demo — high rejection risk.
- Don't wait until the last hour to submit. Approvals are usually fast but not instant, and rejections require a resubmit.
- Don't put URLs in the body without adding them as a proper button — Meta may flag it.
- Don't include the recipient's number or any personal data in the sample values — use realistic-looking placeholders.
