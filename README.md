# n8n Automation Portfolio

Workflow automation projects built with **n8n**: AI-assisted business processes, API integrations and webhook-driven messaging. Each folder has its own README, the exported workflow JSON and setup docs.

| # | Project | What it shows | Stack |
|---|---|---|---|
| 01 | [AI Quote-to-Cash](01-quote-to-cash/) | A customer's free-text enquiry → AI extraction → code-priced quote → Slack approval → CRM deal → accounting invoice → payment link → payment reconciled. 3 workflows plus a 10-case test plan. | n8n, Gemini, Slack, HubSpot API, Xero API (OAuth2), Stripe webhooks, SMTP |
| 02 | [Lead Generation + Email Verification](02-lead-gen-cold-email/) | Google Maps scraping → email discovery on business websites → email verification, managed by a status state machine so re-runs are safe | n8n, Apify, HTTP + JavaScript Code nodes, MillionVerifier, Google Sheets |
| 03 | [WhatsApp Cloud API + Coexistence](03-whatsapp-cloud-api/) | Meta webhook verification, inbound parsing, auto-replies, an approved message template, and a human on the WhatsApp Business App sharing the same number | n8n, Meta Graph API, Cloudflare Tunnel, Flask (alternative) |

## Patterns used across the projects

- **The LLM reads; code decides.** Structured JSON output is validated before anything acts on it, and prices and other business rules stay in deterministic code.
- **Idempotent, re-runnable workflows.** Status fields and duplicate checks mean a retry never double-processes or double-charges.
- **Nothing fails silently.** Bad input goes to a human-review branch, and unhandled failures trigger an error workflow that sends an alert.
- **No secrets in the repo.** Keys live in n8n credentials or environment variables, and the exports contain only placeholders.

## Importing a workflow

In n8n, go to **Workflows → ⋯ → Import from File**, choose the JSON file, then reconnect your own credentials and replace the `YOUR_…` placeholders.

---

Md. Atiqur Rahman Rohid · [github.com/atikur234](https://github.com/atikur234) · [linkedin.com/in/atiqur-rahman-rohid](https://linkedin.com/in/atiqur-rahman-rohid)
