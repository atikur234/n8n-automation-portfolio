# Webhook Payload Reference

Meta's webhook payloads are deeply nested. Reference these when writing extraction logic.

## Verification GET

Sent by Meta once when you save the Callback URL, and any time you re-verify.

```
GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=<your_token>&hub.challenge=<random_string>
```

You must respond with:
- HTTP 200
- Body = the `hub.challenge` value, as plain text (no quotes, no JSON wrapper)
- Only if `hub.verify_token` matches what you configured. If it doesn't match, respond 403.

## Inbound text message

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "<WABA_ID>",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15555551234",
              "phone_number_id": "<PHONE_NUMBER_ID>"
            },
            "contacts": [
              {
                "profile": { "name": "Atiq" },
                "wa_id": "8801XXXXXXXXX"
              }
            ],
            "messages": [
              {
                "from": "8801XXXXXXXXX",
                "id": "wamid.HBg...==",
                "timestamp": "1735689600",
                "text": { "body": "hello" },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

Extraction paths (JSON path syntax):
- Sender's number → `entry[0].changes[0].value.messages[0].from`
- Message text → `entry[0].changes[0].value.messages[0].text.body`
- Message ID (for reply-to / receipts) → `entry[0].changes[0].value.messages[0].id`
- Sender's WhatsApp profile name → `entry[0].changes[0].value.contacts[0].profile.name`
- Message type → `entry[0].changes[0].value.messages[0].type`
- Your own phone number ID (which number was messaged) → `entry[0].changes[0].value.metadata.phone_number_id`

## Inbound non-text messages

The `messages[0].type` field tells you the shape. Handle at least these gracefully:

- `image` → `messages[0].image.id` (media ID; download separately via `/v20.0/<media_id>`)
- `audio`, `video`, `document` → same pattern with type-named object
- `location` → `messages[0].location.latitude`, `.longitude`
- `sticker` → `messages[0].sticker.id`
- `interactive` → button/list reply, `messages[0].interactive.button_reply.id`
- `reaction` → `messages[0].reaction.message_id`, `.emoji`

For the PoC, gate your reply logic behind `type == 'text'` and either ignore other types or send a canned "I can only understand text for now" reply.

## Status callbacks

Meta also POSTs delivery/read status updates to the same webhook. These have `changes[0].value.statuses[]` instead of `messages[]`. Structure:

```json
{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "statuses": [
              {
                "id": "wamid.HBg...==",
                "status": "delivered",
                "timestamp": "1735689610",
                "recipient_id": "8801XXXXXXXXX"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

Statuses can be `sent`, `delivered`, `read`, `failed`. Gate your workflow with `value.messages` (only run reply logic when messages are present) to avoid processing your own outbound status pings as user messages.

## Signing (optional, but nice)

Meta signs each POST with an `X-Hub-Signature-256` header. To verify:

1. Compute `HMAC-SHA256(app_secret, raw_request_body)` — hex-encoded.
2. Compare against the header value (after stripping the `sha256=` prefix).
3. Reject if mismatched.

n8n doesn't do this out of the box; wire it in a Code node if you want the extra credibility for the video. For a 48-hour PoC, mentioning it in the README as a "next step to production-harden" is fine.
