# Lead Generation + Email Verification Pipeline

An n8n pipeline that finds local businesses on Google Maps, looks for a contact email on each business's website, verifies the email, and keeps everything in a Google Sheet that works as a simple CRM. It's the first half of a cold-outreach system aimed at small and medium businesses.

**Stack:** n8n (self-hosted) · Apify Google Maps scraper · HTTP Request + JavaScript Code nodes · MillionVerifier API · Google Sheets

## How it works

```
WF1  Manual trigger → CONFIG (niche + city) → Apify Google Maps scraper → map fields
     → drop listings with no website and no phone → append to Sheet (status = new)

WF2  Read rows where status = new
       ├─ no website ─────────────────────────────────────► status = no_website
       └─ fetch website HTML → extract email
             ├─ no email found ─────────────────────────────► status = no_email
             └─ verify with MillionVerifier
                   ├─ valid / catch-all ────────────────────► status = verified
                   ├─ invalid / disposable ─────────────────► status = invalid_email
                   └─ verifier error, timeout or no key ────► status = unverifiable (email kept)
     → merge all branches → update the Sheet row (matched on phone)
```

## Design decisions

- **The status column is the pipeline's memory.** WF2 reads only `new` rows and every branch writes a final status, so the workflow can be re-run any number of times without reprocessing finished leads or leaving any stuck. The full state machine is in [`docs/state-machine.md`](docs/state-machine.md).
- **"The verifier couldn't run" is kept separate from "the email is bad".** In the first version, every verifier API error was written as `invalid_email`, which wrongly discarded good addresses. v3 marks these `unverifiable` and keeps the email so it can be retried.
- **Each result is paired with its own lead.** Code nodes match results to leads by item index. An earlier bug applied one lead's result to every row.
- **Rows are matched on phone number**, not business name, because names were sometimes truncated by the scraper.
- **Failures don't stop the run.** Website fetches use "Never Error" with a 15 s timeout, so one dead site doesn't crash the batch.

## Files

| File | What it is |
|---|---|
| `workflows/workflow-1-lead-scraper.json` | WF1: Google Maps → Sheet |
| `workflows/workflow-2-email-finder-verifier.json` | WF2 v3: email finder and verifier, with full edge-case handling |
| `docs/state-machine.md` | Every status value and edge case the pipeline handles |

## Setup

1. In n8n, go to **Workflows → Import from File** and import both JSON files.
2. Create a Google Sheet with a `Leads` tab and these columns: `business_name, website, phone, rating, review_count, address, category, source, status, email, email_status`.
3. Replace the placeholders:
   - `YOUR_GOOGLE_SHEET_ID` in all Sheets nodes, then connect your Google credential.
   - `YOUR_APIFY_TOKEN` in the Apify node.
   - `YOUR_MILLIONVERIFIER_KEY` in the Verify Email node.
4. Set your niche and city in **CONFIG - Edit Me** (for example `dentists in Los Angeles`), then run WF1, then WF2.

API keys are placeholders in this repo. In production, keep them in n8n credentials rather than in node parameters.

## Roadmap

- **WF3:** an LLM qualifies each verified lead (cold/warm/hot) and writes a personalised first line, returning strict JSON.
- **WF4:** rate-limited sending across rotated mailboxes, with timed follow-ups.
- **WF5:** reply detection that stops all automation for that lead and alerts the owner.
