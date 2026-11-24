# AI Quote-to-Cash Automation (n8n + Xero + HubSpot + Stripe + Slack)

An end-to-end quote-to-cash workflow for a fictional Australian cleaning company, **Wattlebright Cleaning (DEMO)**. It takes a customer's free-text enquiry all the way to a paid invoice reconciled in Xero, with the owner approving each quote in Slack.

> Demo project: fictional company, sandbox and test accounts only. No real payments or customer data.

**Stack:** n8n (self-hosted) · Google Gemini (structured output) · JavaScript Code nodes · Slack (send-and-wait approval) · HubSpot CRM v3 API · Xero Accounting API (OAuth2, Demo Company AU) · Stripe Checkout (test mode) with a swappable simulated-payment fallback · SMTP

## What it does

```
Customer enquiry (n8n form, one free-text box)
  → AI extracts the details into a strict JSON schema (service, bedrooms, bathrooms, date, contact, spam flag)
  → code validates them; unclear, incomplete or spam enquiries go to Slack for human review instead of erroring
  → code calculates the quote from a fixed price list (+20% urgency, $150 minimum, +10% GST); the AI never sets a price
  → HubSpot: find or create the contact, create a deal, attach the quote breakdown as a note
  → Slack: owner clicks Approve / Reject (72-hour limit)
      approve → Xero contact + AUTHORISED invoice → total checked to the cent → payment link emailed → HubSpot stage updated
      reject  → polite decline email → HubSpot Closed Lost
      expired → HubSpot Closed Lost + Slack notice
  → payment received (Stripe webhook or simulated payment)
      → duplicate-payment check → payment recorded against the Xero invoice → HubSpot Closed Won → Slack "paid"
```

It's split into **3 workflows**:

| Workflow | Role |
|---|---|
| `Q2C 1 · Enquiry to Payment Link` | Form → AI extraction → quote → CRM → approval → invoice → payment link |
| `Q2C 2 · Payment Received` | Payment webhook → normalise the event → idempotency check → Xero payment → HubSpot won |
| `Q2C 3 · Error Alerts` | n8n Error Trigger → Slack alert, with an email fallback if Slack fails |

## Reliability features

- **The AI reads, code decides.** The LLM output is schema-validated, and pricing is deterministic code, so totals are reproducible and auditable.
- **Bad input goes to human review, not a crash.** Missing details, out-of-range jobs (for example 8 bedrooms), unclear requests and spam each get their own route.
- **Duplicate payment notifications are recorded once.** The invoice's paid status is checked before a payment is recorded.
- **Totals are reconciled.** The Xero invoice total must match the calculated quote to the cent before a payment link is sent.
- **The payment provider is swappable.** Stripe and the simulated payment both produce the same normalised payment object.
- **Failures are never silent.** Every unhandled error raises a Slack alert with a link to the failed execution.

## Testing

A 10-case test pack covers: the happy path, messy text with the email inside the message, a missing email, a returning customer (no duplicate contact), an oversized job, a non-English (Mandarin) enquiry, spam, a duplicate payment webhook, the reject path, and an unclear request. Expected totals: $187.00, $699.60, $165.00, $451.00 and $324.50.

## Files

| File | What it is |
|---|---|
| [`docs/build-spec.md`](docs/build-spec.md) | Full build spec: architecture, node-by-node tables, data model, price list, every Code node, AI prompt and schema, every API call, credential setup, failure modes, test plan, acceptance criteria, security notes and build order |
| `workflows/` | Exported n8n workflows (being added) |

## Security and privacy

- Secrets live in n8n credentials only. Exported workflows contain credential references, never keys.
- Stripe webhooks are signature-verified, and amounts come from the verified event or from Xero, never from the browser.
- Execution data is pruned after 14 days, because it contains personal details.
