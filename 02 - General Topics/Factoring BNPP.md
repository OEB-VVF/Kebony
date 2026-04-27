# Factoring — BNP Paribas Fortis (BE)

**Status:** Scoping only — waiting on BNPP's integration spec
**Entity:** Kebony BNV (Belgian operating company)
**Purpose:** Sell open customer invoices to BNPP for working-capital financing
**Owner:** Olivier Eberhard / VVF Consulting
**Date:** 2026-04-24

---

## 1. What factoring means here

Kebony BNV assigns (sells) its open customer invoices to BNPP. BNPP advances ~80–90 % of the invoice value immediately and collects from the end customer. When the customer pays BNPP, the reserve is released (minus fees) back to Kebony.

**Recourse clause:** after **90 days unpaid**, BNPP de-finances the invoice (*définancement*) — the receivable bounces back to Kebony. That's BNPP's problem operationally, but Odoo still needs to reverse the factoring entries when it happens.

## 2. Scope of automation on our side

Two threads — everything else stays manual (credit limits, new customer onboarding, website updates).

### 2.1 Outbound — CSV export (Odoo → BNPP)

Scheduled cron. Two files:

| File | Source model | Scope |
|---|---|---|
| **Customers** | `res.partner` | Subset flagged as factored — VAT, name, address, credit limit, language |
| **Invoices** | `account.move` | Open sale invoices for factored customers — number, date, amount, due date, customer ref, currency |

Filter domain (draft):
- `partner.x_kebony_factor_eligible = True`
- `state = 'posted'`
- `move_type = 'out_invoice'` (maybe `out_refund` too)
- `amount_residual > 0`
- `factor_state != 'assigned'` (not already sent)

### 2.2 Inbound — bank linkage for lettrage

- New `account.journal` type=bank on BNPP factor account
- Statement import: **CODA** (Belgian native format, handled by standard Odoo)
- Reconciliation rules to auto-match BNPP's forwarded customer payments to the original invoice

## 3. Proposed Odoo-side module — `kebony_factoring`

Small footprint, no heavy custom code.

| Artefact | Purpose |
|---|---|
| `kebony.factoring.agreement` (new model) | Agreement-level config: BNPP IBAN, credit limits, fee structure, default threshold, delivery protocol |
| `res.partner.x_kebony_factor_eligible` (Bool) | Which customers are in scope |
| `account.move.factor_state` (Selection: `not_assigned` / `assigned` / `paid` / `defined`) | Invoice lifecycle within factoring |
| `account.move.factor_assignment_id` (M2o) | Link to the assignment batch |
| `ir.cron` | Daily CSV export |
| New bank journal + reconciliation rules | Inbound payments via BNPP |

## 4. Still waiting on BNPP for

1. **CSV field list** — exactly which customer + invoice fields, order, delimiter, encoding, date format
2. **Invoice selection rules** — all sale invoices? threshold? which currencies? include credit notes?
3. **Delivery protocol** — SFTP (host + key)? Email? Their portal API?
4. **Payment statement format** — CODA (standard) or proprietary?
5. **Factor account IBAN** — for the new bank journal
6. **Accounting treatment** — which Belgian account for factor receivable, reserve, fees, and the défi-nancement reversal
7. **Notification regime** — is this *disclosed factoring* (customers notified — invoice text changes) or *undisclosed* (silent)?
8. **Multi-currency** — BNPP Belgium is EUR only?
9. **Recourse scope** — full recourse (90-day unwind) or partial?

## 5. Known design decisions (from Olivier)

- **Credit limits** — uploaded one-time at agreement start. Subsequent changes + new customer additions done **manually on BNPP's portal and mirrored manually in Odoo** → no automation
- **Définancement** — "BNPP's problem" from an operations view; Odoo side needs reversal automation when BNPP flags it
- **Manual-first, automate-only-what-matters** — only the CSV export + bank linkage (lettrage) are in scope for automation

## 6. Implementation waves (once BNPP spec arrives)

| Wave | Scope | Dependency |
|---|---|---|
| **W1 — Config** | `kebony.factoring.agreement` model, partner flag, invoice `factor_state`. No writes, no CSVs yet. | None |
| **W2 — CSV export** | Scheduled cron emits the 2 CSVs. Delivery via mail for testing first, then SFTP. | BNPP field spec |
| **W3 — Bank journal + CODA** | Bank journal on BNPP factor IBAN; reconciliation rules. Test with a real statement. | BNPP IBAN + sample statement |
| **W4 — Accounting treatment** | Journal entries at assignment, advance, payment, defaulted-reversal. | BNPP accounting treatment doc |
| **W5 — Audit / lettrage** | Reports, exception handling (unmatched customer payments, overdue assignments, défi-nancement alerts) | W1–W4 live |

## 7. Pre-go-live test plan (April 2026)

Send BNPP a **representative CSV batch** covering edge cases so they can validate their ingestion before real money flows. Bank-side lettrage cannot be tested offline — that waits for the first live statement.

### 7.1 Hedge-case customer + invoice matrix

| # | Scenario | Customer profile | Invoice profile | What BNPP tests |
|---|---|---|---|---|
| 1 | **Healthy baseline** | Active BE customer, within credit limit | Current, not overdue, EUR, ≥ threshold | Happy path — normal financing |
| 2 | **Overdue, within 90-day window** | Same customer | Invoice past due date but < 90 days | Their "aging" bucket logic; still financed with monitoring |
| 3 | **Near-définancement (> 60, < 90 days)** | Same customer | Due 75-ish days ago | Flag + warning behaviour before recourse trigger |
| 4 | **Définancement candidate (> 90 days)** | Same customer | Due > 90 days ago | Confirm their reject / pushback logic |
| 5 | **Credit-limit breach** | Customer whose outstanding > BNPP credit limit | Incremental invoice tipping over | They either reject or partial-finance |
| 6 | **Credit note** | Active customer | `out_refund` offsetting an earlier invoice | How credits are consumed against the receivable balance |
| 7 | **Partial direct payment** | Active customer | Invoice half-paid by customer to our normal account (not via factor) | Residual amount handling |
| 8 | **No BNPP-approved credit limit** | New customer, not yet on their portal | First invoice | Their reject path for unapproved customers |
| 9 | **Foreign / non-BE customer** | EU or non-EU buyer | EUR invoice | Whether they accept cross-border or only domestic BE |
| 10 | **Non-EUR invoice** | Customer with USD/GBP | USD invoice | Confirm EUR-only (or multi-currency) scope |
| 11 | **Intercompany exclusion** | Kebony INC or KAS as "customer" | Normal invoice | **Must be excluded from the export** — internal transfer, not factorable |
| 12 | **Very small amount** | Active customer | Invoice under any minimum threshold | Their threshold logic |

### 7.2 Generation approach

- Hand-pick **real** invoices + customers from the test Odoo environment that match each row, **or** seed a dedicated test batch in the test branch
- Export via the v0.1 CSV generator (once drafted)
- Mark each row with a **test-case tag** column so BNPP can align findings back to the matrix
- Share CSVs via whatever channel BNPP's integration team prefers (likely email for the test; SFTP for prod)

### 7.3 What we can't test offline

- **Bank linkage / CODA import** — needs a real BNPP statement. Deferred to the first live payment cycle after go-live. Accept that the first week post-go-live is soft-launch for reconciliation.

## 8. Open questions back to Olivier

- Is the full Belgian sales book in scope, or a defined customer subset?
- Is there a minimum invoice amount threshold for factoring?
- Is this the only factoring relationship, or will we have multiple factors later (affects model — one agreement vs many)?
- Test-batch timing: end of April 2026 workable? Which Kebony contact drives the BNPP-side testing?

## 9. References

- [[Terminology Bible]] — Kebony BNV (Belgian entity) + res.company entity_type
- [[Accounting & Margin Architecture]] — US analogue for accruals / margin; factoring is BE-specific and separate
- External: BNPP Fortis factoring docs (pending)

---

## Document history

| Date | Change |
|---|---|
| 2026-04-24 | Initial scoping doc — 2 automation threads (CSV export + bank linkage), `kebony_factoring` module shape, open-items list. Awaiting BNPP integration spec before building. |
| 2026-04-24 | Added §7 Pre-go-live test plan — 12-case hedge matrix (healthy, overdue buckets, credit breach, credit note, partial payment, no credit limit, foreign, non-EUR, intercompany, small amount) for end-of-April BNPP validation. Bank/CODA testing deferred to first live cycle. |
