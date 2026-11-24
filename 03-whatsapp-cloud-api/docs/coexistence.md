# Cloud API ↔ WhatsApp Business App Coexistence

This is the assessment's crucial requirement. Read carefully — the UI paths in Meta have shifted a few times and older tutorials describe outdated flows.

## What "coexistence" means

Historically, when you registered a phone number with the WhatsApp Cloud API, Meta would **unregister** that number from any WhatsApp mobile app it was signed into. The number effectively became API-only.

**Coexistence mode** lets the same phone number be active in two places at once:
- The **WhatsApp Business App** on the physical phone (a human can tap and reply).
- The **Cloud API** (your n8n workflow can send/receive).

Both surfaces see the same conversation threads, in near real-time. This is what the assessment is testing that you can configure.

## What coexistence is NOT

- It is not the consumer WhatsApp app. You must use the **WhatsApp Business App** (green briefcase icon).
- It is not multi-device / linked-devices (that's a different consumer feature).
- It is not the on-premises API (a legacy, deprecated product).
- It is not the same as adding a "test recipient" — that's just the sandbox restriction while your app is in development.

## The setup path (2025)

There are two ways to enable coexistence. Use the first if you're the number's owner; use the second if you're a tech provider integrating for someone else.

### Path A — Direct in the WhatsApp Business App (recommended for the assessment)

1. Install **WhatsApp Business** (not consumer) on the physical phone. Register the phone number as normal (SMS verification).
2. Send yourself a test message on the phone to confirm the app is working.
3. In the app: **Settings → Business tools → WhatsApp Business API** (menu label varies by app version; on newer versions look under **Settings → Account → Advanced** for "Cloud API" or "Coexistence"). Tap **Connect to a Meta Business Portfolio**.
4. Sign in to the same Meta account that owns the app you created in `meta-setup.md`. Select the Business Portfolio and WABA to link.
5. The app shows a coexistence consent screen. Approve.
6. On success, back in Meta's **WhatsApp Manager**, this number now appears in **Phone numbers** with a "Coexistence" badge.

### Path B — Embedded Signup with the coexistence flag (developer flow)

If you want to demonstrate the developer-facing flow (nicer for the video), embed Meta's Facebook Login for Business flow with `feature: 'whatsapp_business_app_onboarding'` set. This launches Meta's guided popup that walks the user through selecting their WABA and enabling coexistence.

Minimal snippet:

```html
<script async src="https://connect.facebook.net/en_US/sdk.js"></script>
<script>
  window.fbAsyncInit = function() {
    FB.init({ appId: '<APP_ID>', xfbml: false, version: 'v20.0' });
  };
  function launchSignup() {
    FB.login(function(response) {
      console.log('signup complete', response);
    }, {
      config_id: '<YOUR_EMBEDDED_SIGNUP_CONFIG_ID>',
      response_type: 'code',
      override_default_response_type: true,
      extras: { feature: 'whatsapp_business_app_onboarding' }
    });
  }
</script>
<button onclick="launchSignup()">Enable Coexistence</button>
```

You'll need to create an Embedded Signup Configuration in the Meta app dashboard (Facebook Login for Business → Configurations → Create). This is nice-to-have; Path A is enough for the assessment.

## Confirming coexistence is really on

After setup, do this three-part check — this is exactly what your video demo will show:

1. **API → Phone.** From your machine, send a message via curl (or n8n) to a third phone number. Confirm it arrives on that third phone AND appears in the "Sent" list inside the WhatsApp **Business** App on the coexistence phone.
2. **Phone → API.** From that third phone, send a message back to the coexistence number. Confirm it appears in the WhatsApp Business App AND your n8n webhook fires (check the Executions tab).
3. **Phone-typed reply.** From the coexistence phone's WhatsApp Business App, manually type and send a reply. Confirm delivery on the third phone AND that when the third phone replies again, your n8n webhook still fires.

If all three pass, coexistence is truly working. If step 3 fails, the number probably got kicked into API-only mode — restart from Path A.

## Common gotchas

- **The number was previously on consumer WhatsApp.** Uninstall consumer WhatsApp on that device first, wait an hour, install WhatsApp Business fresh, then re-register.
- **The WhatsApp Business App is out of date.** Coexistence needs a reasonably recent version (roughly late 2024+). Update from the Play Store / App Store before starting.
- **Region availability.** As of writing, coexistence has rolled out broadly but not universally. If Path A doesn't offer the Meta-connect option, update the app and retry.
- **You picked "Migrate" instead of "Coexistence" during setup.** Migration replaces the phone-app registration with API-only. Not what you want.

## What to say in your video

When you get to this beat, narrate it clearly:

> "Notice the same number is registered to my WhatsApp Business App on the phone and also connected to the Cloud API. This is Meta's coexistence mode. I'll now type a reply manually from the phone — you can see it lands on the other side. And when that user replies again, my n8n webhook still receives the event."

This is the beat evaluators will re-watch. Make it unmissable.
