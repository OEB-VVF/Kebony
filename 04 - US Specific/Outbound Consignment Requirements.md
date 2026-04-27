---
title: Outbound Consignment Program — Requirements for Validation
audience: CEO · Head of US · CFO (copy, for information)
status: Draft — pending validation (no code started)
author: Olivier Eberhard (VVF Consulting)
date: 2026-04-20
version: 0.8
module: kebony_bol_report (extension — selling entity Kebony BNV from July 2026)
changelog:
  - 0.8 (2026-04-20) — Softened §6 tone: dropped explanatory framing
    that read as lecturing CFO/CEO on an obvious WCR concept. §6
    now states mechanics, inputs, and levers — no commentary.
  - 0.7 (2026-04-20) — Removed CSO from sign-off and dropped Q13–Q14.
    Selling entity clarified as Kebony BNV from July 2026, so no EU
    activation step is needed. 90-day aging is already per-contract
    dynamic (Q8), which makes a harmonisation question moot. Q3
    reframed from "pending" to "immediate at CEO sign-off — implementation
    starts on validation". CFO restored as decider on financial/
    accounting questions (Q9–Q12, Q15), while remaining on the copy
    list for the overall memo.
  - 0.6 (2026-04-20) — Toned down Working Capital messaging. CFO moved
    from sign-off scope to "copied for information" due to WCR impact.
    §6 reframed as operational information, not a go/no-go gate.
  - 0.5 (2026-04-20) — Added §3.4 Freight Capitalisation: internal transfer
    + transport PO + provision + vendor bill flow, with full accounting.
    Decision confirmed: transfer freight is capitalised into distributor
    inventory value (ASC 330). New Q15 for CFO on variance treatment.
  - 0.4 (2026-04-20) — Removed undefined "Phase 2" references. No second
    phase is scoped or committed; "Out of Scope" list stands on its own
    as deferred items requiring a separate business case.
  - 0.3 (2026-04-20) — Removed proposed timeline section. Build estimated
    at ~1 week including testing; timeline belongs in the implementation
    ticket, not the requirements memo.
  - 0.2 (2026-04-20) — Added CFO + CSO to sign-off. Added Working Capital
    section (§6). Flagged EU optionality — program US-first but mechanism
    must be portable to EU entities, so CSO involvement from day one.
  - 0.1 (2026-04-20) — Initial draft for CEO + Head of US.
---

# Outbound Consignment Program
## Requirements for Validation

> **Purpose.** Operating model, data, controls, and open questions for selling selected Kebony profiles through distributors on consignment. For **CEO · Head of US** sign-off before any code is developed. **CFO is on copy** — decides on financial & accounting questions (§6, Q9–Q12, Q15).
>
> **Selling entity.** From **July 2026**, consignment sales flow through **Kebony BNV**. A single selling entity means no separate geographic rollout step — distributor addresses and currencies are set per agreement.

---

## 1. Executive Summary

The CEO has directed that Kebony sell selected profiles through **consignment stock held at distributor locations**. The distributor holds the goods physically; Kebony retains ownership until invoice. Invoicing is triggered in two ways:

1. The distributor reports a pack as sold (partial or full) — Kebony invoices the **full pack** immediately.
2. If a pack remains unsold after a contractual aging period (**default 90 days**), Kebony auto-invoices the full pack to the distributor.

The program launches with **5 profiles** and is designed to scale to additional products and distributors through configuration (no code change).

---

## 2. Business Scope

| Item | Value |
|---|---|
| Selling entity | **Kebony BNV** (from July 2026) |
| Program start | Pending validation |
| Products in scope at launch | **5 profiles** — list to be confirmed by Head of US |
| Distributors in scope | Configurable — 1..N contracts, each with 1..N shipping addresses |
| Aging trigger | **Dynamic per contract** — default 90 days, editable on each agreement |
| Invoicing unit | **Always full pack** — never partial |
| Currency | Per agreement — Kebony BNV supports multi-currency natively |
| Balance-sheet treatment | Stock remains on **Kebony BNV balance sheet** until invoiced |

---

## 3. End-to-End Operating Flow

### 3.1 Supply to distributor
1. Kebony creates an internal transfer: main US warehouse → distributor consignment location
2. Dedicated route + picking type: **"Resupply Consignment at Customer"** — makes all consignment moves filterable
3. Goods arrive at distributor; **no revenue**, no COGS, no accrual — it is an internal stock movement
4. The arrival date becomes the **clock start** for each lot (pack)

### 3.2 Sale — two trigger paths

**Path A — Distributor reports pack sold (partial or full)**
1. Distributor sends report (CSV upload or in-app wizard; a self-service portal is deferred — see §7)
2. Kebony posts customer invoice for the **full pack**, regardless of whether the distributor sold all of it
3. Stock moves off the consignment location (DR COGS / CR Inventory, revenue recognised)

**Path B — Aging trigger (automatic)**
1. Daily cron scans all lots sitting on consignment locations
2. If `today − arrival_date > agreement.aging_days` **and** the lot has not yet been invoiced → auto-invoice the full pack to the distributor
3. Same accounting as Path A

### 3.3 Revenue recognition summary
- **No** revenue on supply transfer (internal move).
- Revenue + COGS recognised at invoice posting (Path A or Path B).
- All existing Kebony accrual rules apply at invoice time (royalties, management fees, marketing, sales rep commissions).

### 3.4 Freight capitalisation (transfer cost accounting)

Under **ASC 330**, freight incurred to bring inventory to its present location is capitalised into inventory value. Because Kebony retains ownership of consigned stock at the distributor location, transport costs from the US warehouse to the distributor **must be capitalised** rather than expensed.

This gives COGS at invoice time the true landed cost of each pack — directly improving margin visibility at the Accounting Hub.

**Mechanics (reusing Odoo landed cost pattern already in use for inbound):**

| Step | Event | Journal entry |
|---|---|---|
| 1 | Internal transfer created (main WH → distributor location) | No financial entry (internal stock move, same entity) |
| 2 | Purchase Order raised to freight carrier (estimated cost) | No entry on PO creation |
| 3 | Goods received at distributor · `stock.landed.cost` posted against the transfer picking, based on carrier PO estimate | **DR** Inventory @ distributor (allocated freight per pack) · **CR** Accrued Freight — Consignment *(provision)* |
| 4 | Vendor bill received from carrier | **DR** Accrued Freight — Consignment · **CR** Accounts Payable · variance (if any) handled per Q15 policy |
| 5 | Consignment invoice fires (reported sale or 90-day aging) | **DR** COGS (enriched unit cost = product cost + capitalised freight) · **CR** Inventory · **DR** AR · **CR** Revenue |

**Design notes:**
- Freight allocation method: proportional to **pack count** per shipment (simpler and consistent with how inbound landed cost is allocated today)
- Each lot at the distributor location carries an enriched `x_studio_unit_cost` = product standard cost + allocated freight; COGS at invoice pulls this value
- A new GL account "**Accrued Freight — Consignment**" is added to the US chart of accounts (classified as an AP-side accrual)
- Transfer picking can only be validated once the carrier PO is linked — enforced in UI to prevent unprovisioned transfers

**Working-capital note:** capitalised freight joins the WC envelope in §6 — minor at unit level (single-digit % of product cost) but material at fleet volume.

---

## 4. Proposed Data Model

### 4.1 Model: `kebony.consignment.agreement`
One record per contract.

| Field | Type | Purpose |
|---|---|---|
| `partner_id` | many2one res.partner | Distributor |
| `shipping_address_ids` | many2many res.partner | One or more ship-to locations |
| `product_ids` | many2many product.product | Products covered by the contract (5 profiles at launch) |
| `product_category_id` | many2one product.category | Alternative: derive list from a master category/code |
| `aging_days` | integer | Auto-invoice threshold (default = 90) |
| `pricelist_id` | many2one | Price applied at invoice |
| `auto_invoice` | boolean | Enables/disables Path B |
| `state` | selection | draft / active / closed |
| `notes` | text | Contract reference, commercial terms |

### 4.2 Stock layer
- One `stock.location` per distributor address (`usage = internal`), flagged `x_is_consignment_out = True` and linked to the agreement.
- Each `stock.lot` gains two fields:
  - `consignment_entry_date` — arrival date at the consignment location (clock start)
  - `consignment_invoice_id` — once set, the lot is considered invoiced (idempotency guarantee)

### 4.3 Invoice layer
- Two paths (A and B) both call a single internal method `_create_consignment_invoice(lot)`, which:
  - Posts a full-pack invoice line
  - Sets `lot.consignment_invoice_id`
  - Triggers the standard accrual posting for US entity

---

## 5. Robustness Controls

| Control | Mechanism |
|---|---|
| One invoice per pack, ever | `stock.lot.consignment_invoice_id` — set-once, cron and wizard both check |
| No double invoice | Cron skips any lot with `consignment_invoice_id` already set |
| Dry-run mode | Cron can run in "preview" mode — logs the list of packs that *would* be invoiced, posts nothing; CFO review gate before flipping to live |
| Audit trail | Each agreement shows clock-start per lot, invoice date, trigger source (cron vs user) |
| Full-pack enforcement | Invoice quantity is always the pack size on the lot, never the partial qty reported |
| Access control | Agreement creation and auto-invoice toggle restricted to US Controller group |
| Alerting (optional) | Email to Head of US + CSM N days before auto-invoice fires (see Q5 below) |

---

## 6. Working Capital

### 6.1 Exposure formula

```
WCR ≈ annual_consignment_volume × unit_cost × aging_days / 365
```

### 6.2 Inputs required (Head of US)

| Input | Purpose |
|---|---|
| Forecast annual volume per profile (packs) | Envelope sizing |
| Pilot distributor volume (first 90 days) | Ramp exposure |
| Unit cost per profile | `volume × cost` |
| Target distributor turn rate (days to sell a pack) | Stress test vs. 90-day backstop |

### 6.3 Levers available

| Lever | Mechanism |
|---|---|
| Monthly dashboard | Accounting Hub widget: open packs × unit cost × age, by distributor + profile |
| Aging buckets | 0–30 / 31–60 / 61–90 / > 90 days, per distributor |
| Pause transfers | Agreement `state = paused` blocks new supply without closing the contract |
| Optional WCR cap per contract | `max_open_value` field (Q9) |

---

## 7. Deferred — Not Included at Launch

The items below are intentionally out of scope. Each would require a separate business case and implementation effort:

- **Distributor self-service portal** — at launch, distributors report sales by CSV upload or via an in-app wizard operated by Kebony. A dedicated portal for distributors is not built.
- **Returns / swaps of consigned packs** — handled manually by the US controller at launch (credit note + manual stock reversal).
- **Automated replenishment rules from distributor stock levels** — supply is manual (Head of US triggers transfer).
- **Consignment-specific commissions / rebates** — existing Kebony accrual logic applies unchanged (royalties, mgmt fees, marketing, sales rep).

---

## 8. Open Questions — Requires Decision Before Build

### Operational (CEO · Head of US)

| # | Question | Option A | Option B | Recommendation |
|---|---|---|---|---|
| Q1 | Does the 90-day clock reset on a partial sale from a pack? | Reset clock on any movement | Keep original arrival date — no reset | **B** — simpler, aligns with "we always invoice full pack" |
| Q2 | Which 5 profiles are in scope at launch? | To be listed | — | Pending Head of US |
| Q3 | Which distributor(s) go live first? | Named at sign-off | — | **Decided at CEO sign-off — implementation starts immediately on validation** |
| Q4 | Pricing at invoice: contract pricelist or standard list price at invoice date? | Pricelist per agreement | Std list price | **A** — contract-level control, predictable |
| Q5 | Who receives the pre-auto-invoice alert? | Head of US + distributor CSM | CFO only | Pending |
| Q6 | If the distributor reports > 1 full pack sold (e.g. 1.2 packs) | Round up to 2 packs invoiced | Return an error — manual review | Pending |
| Q7 | Does the distributor receive a formal dispatch note at supply? | Yes — standard delivery order | No — only invoice matters | **A** — physical audit trail |
| Q8 | Aging default override: can Head of US change per contract? | Yes — `aging_days` editable on agreement | No — system-wide 90 | **A** — aligned with "dynamically set up" |

### Financial & Accounting (CFO decides)

| # | Question | Option A | Option B | Recommendation |
|---|---|---|---|---|
| Q9 | Hard WCR cap per agreement that blocks new transfers? | Yes — `max_open_value` enforced | No — monitor only, no block | Pending CFO |
| Q10 | WCR exposure reporting cadence | Monthly dashboard on Accounting Hub | Weekly email to CFO | Pending CFO |
| Q11 | Credit limit check at auto-invoice time | Block auto-invoice if distributor AR > limit | Invoice anyway, flag controller | Pending CFO |
| Q12 | Treatment of returns after auto-invoice fires | Credit note + re-consign | Credit note only, no re-consign | Pending CFO |
| Q15 | Freight variance (vendor bill ≠ provision) | Threshold-based — small variance to P&L, > 5 % retro-adjusts inventory | Always expense variance to P&L | Pending CFO |

---

## 9. Validation Requested

Please confirm by reply. Each role has a distinct validation scope:

### CEO
- [ ] Strategic intent and selection of pilot distributor(s)
- [ ] Q3 is decided at sign-off (pilot distributor name) — implementation starts immediately on validation

### Head of US (primary operational owner)
- [ ] Product scope — list of the 5 profiles
- [ ] Distributor shipping addresses for launch
- [ ] Forecast volume + unit cost inputs for §6.2
- [ ] Decisions on Q1, Q2, Q4, Q5, Q6, Q7, Q8

### CFO — on copy · decides on financial & accounting
- [ ] Decisions on Q9, Q10, Q11, Q12, Q15

— *Olivier Eberhard · VVF Consulting · 2026-04-20 · v0.8*
