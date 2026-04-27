# US Accrual System — Improvement Backlog

> **Status:** Working paper — for meeting preparation
> **Date:** 8 April 2026
> **Author:** Olivier Eberhard (VVF)

---

## Current State Summary

The EOM accrual engine (`action_run_eom_accruals`) creates journal entries for 5 cost types:
- **Marketing** (4% wood / 1.5% accessory — distributors only)
- **Royalties** (5% wood only)
- **Management Fees** (14% wood / 5% accessory)
- **Sales Rep Commission** (variable rate per rep)
- **Freight** (header-level manual input)

**Not accrued today:** Warehousing / handling costs.

**Analytics posted:** Only Sales Area (on debit/expense line). Country and BU are missing.

**Reversal:** Fully manual. No settlement wizard. No weighted allocation.

---

## Issue 1: Country & BU Analytics on Accrual JEs

### Problem
Accrual journal entries only carry Sales Area analytic. The mandatory Country and BU dimensions are missing, making the JE incomplete for multi-dimensional reporting.

### Solution
When creating accrual JE lines in `action_run_eom_accruals()`, add to the analytic distribution:

| Dimension | Value | Logic |
|-----------|-------|-------|
| Country | US (or Canada if `partner.country_id.code == 'CA'`) | From invoice partner's country |
| BU | **52** (Sales & Distribution) | Default for all accrual types... |
| BU | **60** (Marketing) | ...except marketing accruals |
| Sales Area | (existing) | From invoice header `x_studio_area_of_sales` |

### To Verify
- What is the exact BU analytic ID for code 52 and 60? Need to check the analytic plan structure on the test instance.
- Does Canada ever appear on US entity invoices? If yes, country should be dynamic from partner.

### Code Change
In `kebony_accounting_hub.py` → `action_run_eom_accruals()` → where `analytic_dist` is built for the debit line:

```python
# Current: only sales_area
analytic_dist = {str(sales_area_plan_id): 100}

# New: add country + BU
analytic_dist = {
    str(country_plan_id): 100,   # US or CA
    str(bu_plan_id): 100,        # 52 or 60 (marketing)
    str(sales_area_plan_id): 100,
}
```

---

## Issue 2: Sales Rep & Distributor as Analytical Plans

### Problem
- **Sales rep** commission accruals are tracked via `partner_id` on the liability line — no analytic integration, can't match accrual ↔ vendor bill via analytics.
- **Marketing** accruals are posted without distributor identity — can't report marketing fund balance per distributor.

Both need the same solution: a **new analytic plan** with **auto-created analytic accounts** from partner records.

### Solution: Two New Analytic Plans

| Plan | Source | Trigger | Used On |
|------|--------|---------|---------|
| **Sales Representative** | `res.partner` with `supplier_rank > 0` + is sales rep | Auto-create on partner flag | Sales rep commission accrual JEs + rep vendor bills |
| **Distributor** | `res.partner` with `x_studio_customer_catagory = "Distributor"` | Auto-create on partner flag | Marketing accrual JEs + marketing vendor bills |

### Auto-Creation Mechanism

Two-layer safety:

**Layer 1 — `write()` override on `res.partner`:**
When a partner is flagged as sales rep or distributor, automatically create (or reactivate) an analytic account in the corresponding plan.

```python
class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        res = super().write(vals)
        # Sales Rep plan
        if 'x_studio_sales_representative' in vals or 'supplier_rank' in vals:
            self._kebony_ensure_analytic_account('sales_rep')
        # Distributor plan
        if 'x_studio_customer_catagory' in vals:
            self._kebony_ensure_analytic_account('distributor')
        return res

    def _kebony_ensure_analytic_account(self, plan_type):
        """Create analytic account for this partner if it doesn't exist."""
        plan = self.env.ref(f'kebony_bol_report.analytic_plan_{plan_type}')
        for partner in self:
            existing = self.env['account.analytic.account'].search([
                ('plan_id', '=', plan.id),
                ('partner_id', '=', partner.id),
            ], limit=1)
            if not existing:
                self.env['account.analytic.account'].create({
                    'name': partner.name,
                    'plan_id': plan.id,
                    'partner_id': partner.id,
                    'company_id': partner.company_id.id or False,
                })
```

**Layer 2 — Lazy creation at accrual posting time:**
In `action_run_eom_accruals()`, before building the analytic distribution, call `partner._kebony_ensure_analytic_account(plan_type)`. This catches partners imported via CSV or created before the module was installed.

### On Accrual Posting

| Accrual Type | Analytics Posted |
|-------------|-----------------|
| Marketing | Country + BU(60) + Sales Area + **Distributor** |
| Sales Rep | Country + BU(52) + Sales Area + **Sales Rep** |
| Royalties | Country + BU(52) + Sales Area |
| Mgmt Fees | Country + BU(52) + Sales Area |
| Freight | Country + BU(52) + Sales Area |

### On Vendor Bill Settlement
When booking a rep's invoice or a distributor's marketing invoice, the user (or automation) posts it with the **same analytic tag**. The accrual status report (Issue 3) then shows: accrued per rep/distributor vs. settled.

### Partner Archive = Analytic Archive
When a partner is archived, the corresponding analytic account should also be archived (no new postings allowed, historical data preserved).

---

## Issue 3: Accrual Status Report by Analytical Tag

### Need
A report showing, per accrual type and per analytical dimension:
- **Accrued** (total provisions posted via EOM engine)
- **Settled** (vendor bills booked against provision accounts)
- **Open balance** (accrued − settled)
- **Expired / Released** (manual reversals)

### Design

```
ACCRUAL STATUS REPORT — Q1 2026

Type          Sales Area    Rep/Distributor     Accrued   Settled   Open     Released
────────────────────────────────────────────────────────────────────────────────────────
Marketing     East Coast    Biewer Lumber       12,500    10,000    2,500    0
Marketing     East Coast    ABC Distributors     3,200     3,200        0    0
Marketing     West Coast    Pacific Wood Co      8,200     7,800      400    0
Royalties     East Coast    —                   18,750    15,000    3,750    0
Royalties     West Coast    —                   14,100    14,100        0    0
Mgmt Fees     East Coast    —                   52,500    48,000    4,500    0
Sales Rep     East Coast    Rob Langenfeld       6,200     5,500      700    0
Sales Rep     West Coast    Mako Sales           4,100     4,100        0    0
Freight       East Coast    —                    3,200     3,200        0    0
────────────────────────────────────────────────────────────────────────────────────────
TOTAL                                          122,750   110,900   11,850    0
```

### Implementation
SQL view on `account.move.line` filtered by accrual GL accounts (2155xx), grouped by analytic tags. Could be:
1. An Odoo pivot view (fastest to build)
2. An Odoo Spreadsheet with PIVOT formulas (more polished)
3. A custom report action (most flexible)

**Recommendation:** Start with pivot view, evolve to Spreadsheet.

---

## Issue 4: Weighted Reversal of Royalties & Management Fees

### Problem
When a royalties or management fees invoice arrives (e.g. €1,000 for Q1), we need to:
1. Determine the weight of each sales area in that period's accruals
2. Reverse up to the accrued amount per sales area (never more)
3. Post the difference (actual > accrual) to P&L directly
4. If actual < accrual, release the excess provision

### Example

**Q1 Royalties accrued by sales area:**
| Sales Area | Accrued |
|-----------|---------|
| East Coast | €600 |
| West Coast | €300 |
| Central | €100 |
| **Total** | **€1,000** |

**Vendor invoice arrives:** €900

**Weighted allocation:**
| Sales Area | Weight | Allocated | Reversal | P&L Impact |
|-----------|--------|-----------|----------|------------|
| East Coast | 60% | €540 | DR 215540 / CR 584000 (€540) | €0 |
| West Coast | 30% | €270 | DR 215540 / CR 584000 (€270) | €0 |
| Central | 10% | €90 | DR 215540 / CR 584000 (€90) | €0 |
| **Total** | 100% | **€900** | **€900** | **€0** |

**Remaining accrual:** €1,000 − €900 = €100 stays as provision (or released if period closed).

### If Invoice > Accrual (€1,100 invoice vs €1,000 accrued):
| Sales Area | Weight | Max Reversal | Actual Allocated | P&L (excess) |
|-----------|--------|-------------|-----------------|-------------|
| East Coast | 60% | €600 | €660 → capped at €600 | €60 to P&L |
| West Coast | 30% | €300 | €330 → capped at €300 | €30 to P&L |
| Central | 10% | €100 | €110 → capped at €100 | €10 to P&L |
| **Total** | | **€1,000** | **€1,000 reversed** | **€100 to P&L** |

### Implementation: Settlement Wizard

A wizard triggered from the vendor bill that:
1. Selects accrual type (royalties / mgmt fees / marketing)
2. Selects period (Q1 2026, Q2 2026, etc.)
3. Shows current accrual balances by sales area (from Issue 3 report)
4. Enters the invoice amount
5. Computes weighted allocation + caps
6. Creates the reversal JE (multi-line, per sales area, with analytics)
7. Posts the difference to P&L expense account

### Accounts

| Entry | Debit | Credit |
|-------|-------|--------|
| Reversal (per area) | 2155xx (Provision) | 58xxxx (Expense) |
| Excess to P&L | 58xxxx (Expense) | 2110xx (AP) |
| Vendor bill | 2110xx (AP) | Bank |

---

## Issue 5: Landed Cost PO — Test & User Manual

### What Exists
The landed cost automation flow was built in the bol_report module:
1. Goods PO → Receipt → Estimated LC accrual (auto)
2. Cost PO → Vendor bill → Actual LC posted → Estimated accrual reversed
3. GRNI clearing

### To Do
- [ ] End-to-end test on test instance with real-like data
- [ ] Document the full flow with screenshots
- [ ] Edge cases: partial receipt, multi-line PO, currency conversion
- [ ] User manual (Obsidian + HTML slide deck)

---

## Issue 6: Warehousing / Handling Cost Accrual

### Current State
`x_studio_warehousing_cost` is a **manual input field** on the invoice header. It's used in the margin calculation formula but **no journal entry is generated**.

### Question
Should we accrue warehousing costs the same way as other accruals?

### If Yes — Design

| Field | Value |
|-------|-------|
| Rate | TBD — per m³ or fixed % of revenue? |
| GL Debit | `59xxxx` (Warehousing expense) — need account code |
| GL Credit | `2155xx` (Warehousing provision) — need account code |
| Base | Same as other accruals (`price_subtotal`) or volume-based? |
| Scope | All US invoices or specific customers? |

### Options

| Approach | How | Pros | Cons |
|----------|-----|------|------|
| **A. Rate-based (like marketing)** | % of revenue | Consistent with other accruals | Warehousing isn't really revenue-driven |
| **B. Volume-based** | $/m³ or $/board | More accurate (handling = physical) | Need volume on every invoice line (already have it) |
| **C. Keep manual** | User inputs per invoice | No code change | Inconsistent, error-prone |

### Recommendation
Option B — Volume-based rate (e.g. $X per m³ shipped). The volume data (`x_kebony_total_volume_m3`) is already computed on every invoice. Rate stored as a company setting or in the accrual rate overrides.

---

## Implementation Status

### Delivered (v1.6.0 — 8 April 2026)

| # | Item | Status | Module Version |
|---|------|--------|----------------|
| 1 | Country + BU analytics on accrual JEs | **DONE** | 1.6.0 |
| 2a | Distributor analytic plan (auto-created from partner) | **DONE** | 1.6.0 |
| 2b | Sales Rep analytic plan (lazy creation at posting) | **DONE** | 1.6.0 |
| 2c | Analytics on BOTH debit + credit lines | **DONE** | 1.6.0 |

### Files Changed

| File | Change |
|------|--------|
| `data/analytic_plan_data.xml` | NEW — Distributor plan (noupdate=1) |
| `models/res_partner.py` | NEW — `write()` override + `_kebony_ensure_analytic_account()` |
| `models/__init__.py` | Added `res_partner` import |
| `models/kebony_accounting_hub.py` | Enhanced EOM engine: `_get_accrual_analytic_plans()`, `_find_country_analytic()`, `_build_accrual_analytic_dist()`, refactored `action_run_eom_accruals()` |
| `__manifest__.py` | Version bump 1.5.0 → 1.6.0, added data file |

### Analytics Per Accrual Type

| Dimension | Marketing | Sales Rep | Royalties | Mgmt Fees | Freight |
|-----------|-----------|-----------|-----------|-----------|---------|
| Country | From partner | From partner | From partner | From partner | From partner |
| BU | **60** (Marketing) | **52** (Sales Int'l) | **52** | **52** | **52** |
| Sales Area | From invoice | From invoice | From invoice | From invoice | From invoice |
| Representative | — | **Auto-created** | — | — | — |
| Distributor | **Auto-created** | — | — | — | — |

### Also Delivered (v1.6.0)

| # | Item | Status |
|---|------|--------|
| 3 | Accrual status report (pivot view) | **DONE** |
| 4 | Settlement wizard (weighted reversal) | **DONE** |
| 5 | Landed cost — tested end-to-end + user guide | **DONE** |
| 6 | Warehousing cost accrual | **DONE** (manual input on invoice, included in margin formula) |

### Additions in v1.6.1 (2026-04-15)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 7 | **Other Costs** accrual type (GL 215595 BS / 599000 P&L) | **DONE** | 7th accrual type, included in SQL view + pivot filter |
| 8 | Accrual Status Report — date + month columns | **DONE** | `month = to_char(date, 'YYYY-MM')`; groupable via Period filter |
| 9 | Accrual Status Report — JE Reference + Detail (label) rows | **DONE** | Pivot now drills Accrual Type → Partner → JE → Detail; list view has same columns |
| 10 | Accrual Status Report — Reversal JE link | **DONE** | LATERAL JOIN on `account_move.reversed_entry_id` surfaces the settlement JE for each accrual |
| 11 | `group_ids` declared explicitly on `action_accrual_status_report` | **DONE** | Fixes "Access Error — Role / Administrator" seen by CFO. Now grants Finance (BU 15), Management (BU 10), BU Admin |
| 12 | Balance Sheet / P&L account pairing documented | **DONE** | Architecture doc `§8 EOM GL Mapping` now explicitly labels 2155xx as BS and 5xxxxx as P&L for all 7 types |

All items delivered.

---

## Open Questions

1. **Warehousing rate:** Per m³? Per board? Fixed %? Who sets the rate?
2. **Reversal frequency:** Monthly? Quarterly? On invoice receipt?
3. **Canada:** Do Canadian sales ever go through Kebony Inc (US entity)? If yes, accrual country is already dynamic (reads partner's country).
4. **Accrual report format:** Pivot view or Odoo Spreadsheet?
