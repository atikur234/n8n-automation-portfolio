# Troubleshooting

Grouped by where the failure happens. Search for the symptom, not the cause.

## Meta side

### "The callback URL or verify token couldn't be validated"

- The GET response body must be the raw `hub.challenge` value, **not** wrapped in JSON, **not** quoted. If n8n's Respond to Webhook is set to JSON mode, switch it to Text.
- The verify token in n8n must match the one you typed into Meta's Configuration exactly. Copy-paste both from a single source of truth.
- The tunnel URL must actually be reachable. Curl it yourself before saving in Meta.
- The workflow must be **Active** (production URL is what Meta hits, not the test URL).

### "Recipient phone number not in allowed list" (error code 131030)

- Your app is still in development mode. Either add the recipient number under WhatsApp → API Setup → Recipient phone numbers and complete the 6-digit code, or move your app to Live mode (requires Business verification, non-trivial for a 48h assessment).
- Tip: for the video, use two numbers you own — the API-registered coexistence number and one personal number added as an allowed recipient. Enough to demonstrate the full loop.

### "Message failed to send" — template not approved

- Check WhatsApp Manager → Message Templates for the exact status.
- Language code must match (`en` vs `en_US` matters).
- Parameter count in the API call must match `{{n}}` placeholders in the body.

### Access token expired

- Temporary tokens live 24h. If your workflow suddenly returns 401s, this is why. Regenerate a System User token with "Never" expiry — see `meta-setup.md` §4.

## Coexistence

### "Register" button is missing in WhatsApp Business App

- Update the app to the latest version.
- Region may not be enabled yet — this has been the biggest wildcard historically. Try Path B (Embedded Signup) in `coexistence.md`, or use a different number.

### Number got kicked off the phone after API registration

- You probably picked "Migrate to Cloud API" instead of "Coexistence" during setup. This is irreversible for that number in the current session; you'll need to re-register on the WhatsApp Business App and repeat the Coexistence flow.

### Webhook stops firing after manually replying from the phone

- If a message the user sends *after* your manual reply still fires the webhook, coexistence is working correctly — the manual reply just doesn't itself generate a webhook (nor should it; it's not an inbound event).
- If new inbound user messages also stop firing, the number has slipped out of coexistence. Recheck WhatsApp Manager for the "Coexistence" badge.

## n8n

### Executions tab shows nothing

- Workflow isn't Active. Toggle it on.
- Meta is hitting the wrong URL. In the Webhook node, check the Production URL vs Test URL and confirm what you gave Meta.
- Cloudflare Tunnel died. Curl the tunnel URL directly to check.

### HTTP Request node returns 400 from Graph API

- Look at the response body — Meta returns descriptive error messages.
- Most common: JSON body malformed. n8n's HTTP Request "Body Content Type" must be `JSON`, and the body itself valid JSON. A stray `{{ … }}` expression that returns `undefined` will corrupt it.

### `WEBHOOK_URL` env var not respected

- n8n must be started with `WEBHOOK_URL=https://<tunnel>.trycloudflare.com/`. If you launched n8n before starting the tunnel, restart n8n after the tunnel is up.

## Cloudflare Tunnel

### Tunnel URL immediately 404s

- Cloudflare's edge takes 10–30 seconds to route a fresh quick tunnel. Wait, then curl again.

### Tunnel returns Cloudflare's error page instead of n8n

- n8n isn't running on the port cloudflared is targeting. `curl http://localhost:5678` locally first.

## Video / demo

### The manual-reply-from-phone beat isn't visually clear

- Film the phone screen and the laptop screen in split view (OBS Studio, free).
- On the laptop, keep the n8n Executions tab open — new executions appearing as messages come in makes the webhook activity visible.
- Narrate specifically: "typing this manually on the phone now" as you tap.
