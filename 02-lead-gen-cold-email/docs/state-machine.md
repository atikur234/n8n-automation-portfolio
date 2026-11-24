# Lead pipeline state machine

Each lead carries a `status` column in the Google Sheet. Every workflow reads only the status it owns, and every branch writes a final status, so a re-run never gets stuck or repeats finished work. `new` means "never touched".

## Status values

| status | Meaning | Next step |
|---|---|---|
| `new` | Scraped by WF1, not yet processed | WF2 processes it |
| `no_website` | No website to look for an email on | WF2 skips it; can be handled manually by phone |
| `no_email` | Had a website, but no email was found on it | WF2 skips it (already tried) |
| `unverifiable` | Email found, but the verifier couldn't run (API error, missing key, timeout) | Retry later; the email is kept |
| `invalid_email` | Email found, but the verifier says it's bad | Skip, don't send |
| `verified` | Email found and the verifier says it's good (or catch-all) | Ready for WF3 |
| `ready_to_send` | WF3 wrote the email | WF4 sends it |
| `sent` | WF4 sent email 1 | Follow-up logic |
| `replied` | The lead responded | Stop all automation |
| `bounced` | The email bounced | Stop; mark as bad |

## WF2 edge cases (email finder + verifier)

1. **No website** → `no_website`. Without this, the lead would stay `new` forever and be picked up on every run.
2. **Website is a social or directory page** (Facebook, Yelp and so on) → still tried; if there's no email → `no_email`.
3. **Website fetch fails, times out or the domain is dead** → treated as no email → `no_email`. The HTTP node has "Never Error" turned on, so one dead site doesn't stop the run.
4. **Page loads, but there's no email in the HTML** → `no_email`.
5. **Email found** → verified next.
6. **Verifier API error, missing key or timeout** → `unverifiable`, and the email is kept. An earlier version marked these `invalid_email`, which wrongly threw away good leads.
7. **Verifier says ok/valid** → `verified`.
8. **Verifier says catch_all** → `verified` (send carefully). **unknown** → `unverifiable`.
9. **Verifier says invalid/disposable** → `invalid_email`.
10. **Several emails on one page** → junk addresses (image files, placeholders, tracking domains) are skipped, and business inboxes (`info@`, `contact@`, `office@` …) are preferred.
11. **Pairing** → each verification result is matched to its own lead by index, so results can't be applied to the wrong row.
12. **Sheet updates** match rows on `phone`. Phone numbers are exact and unique, unlike business names, which can get truncated.

## WF1 edge cases (scraper)

- A listing with no website **and** no phone can't be contacted, so the filter drops it.
- Blank ratings are allowed; the AI step treats them as a "low visibility" angle.
- Duplicates across runs: dedupe on `phone` before appending (recommended next step).

## WF3 edge cases (AI personalisation, next stage)

- Read only `status = verified`.
- If the model returns invalid JSON, leave the status unchanged so the lead is retried.
- Set `ready_to_send` only after a successful run.
