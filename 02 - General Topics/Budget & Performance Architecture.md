# Budget & Performance Architecture

> Version 1.1 — Budget Capture, Forecast & CEO Dashboard
> Module: kebony_bol_report (extension) | Scope: Cross-company (all entities) | Updated: 2026-04-03

---

## 1. Executive Summary

The new CEO wants a **light performance dashboard** with budget vs actual, margin tracking, and last-year reference. Odoo 19's native budget module covers only GL-level P&L budgets with monetary amounts — no volume, no regional breakdown, no margin layers, no stock targets, no cash flow.

This document proposes a **custom budget capture module** covering 8 domains: sales, expenses, production, stock, cash flow, headcount, operational KPIs, and order pipeline — all feeding a single CEO dashboard per company.

**Key constraints**:
- Last-year reference requires a full year of Odoo data → LY columns visible but show **(n/a)** until Jan 2027
- All models are **company-sensitive** — each entity (INC, BNV) maintains its own budget
- US sales area granularity is planned for BP 2027; for BP 2026 all US volume maps to a single area

---

## 2. What Odoo 19 Offers Natively

### 2.1 Financial Budgets (Enterprise)

- Created from the **P&L report** — assign amounts per GL account for a period
- Actuals auto-compare as a % column
- **Dimension**: GL account only. No region, no product, no volume
- **No import tool** — manual entry via P&L interface
- **No approval workflow**

### 2.2 Analytic Budgets

- Budget lines per **analytic plan** (Department, Project, Cost Center)
- Tracks: Planned / Committed (POs) / Achieved (posted entries) / Theoretical (pro-rata)
- States: Draft → Open → Revised → Done
- **Still monetary only** — no unit/volume fields

### 2.3 Verdict

| CEO Requirement | Native Odoo | Gap |
|----------------|-------------|-----|
| Sales budget by country/area | No | Major — GL only, no geography |
| Volume targets (m3, LF, LM) | No | Major — monetary only |
| GM1 margin target | No | Major — no margin concept |
| EBITDA budget | No | No configurable subtotals |
| Cash flow forecast | No | No indirect cash flow method |
| Production output targets | No | Not in budget scope |
| Stock level targets | No | Not in budget scope |
| OTIF / DSO KPIs | No | No KPI framework |
| FTE headcount | No | No headcount planning |
| Last year reference | Partial | P&L can compare periods for actuals, not budgets |
| Reforecast | Basic | "Revised" state = one-time overwrite, no rolling forecast |
| Multi-currency | No | Single company currency |

**Conclusion**: native budgets are useful for the GL expense budget (which we already partially have in cost version). Everything else needs custom work.

---

## 3. Proposed Architecture

### 3.1 Design Principles

1. **One model per budget domain** — keep it simple, avoid a generic "budget line" monster
2. **Period = calendar month** — all budgets stored monthly, aggregated in reports
3. **Version support** — Budget (BP), Reforecast (RF1, RF2…), Actual (computed)
4. **Company-sensitive** — each entity enters its own BP in local currency
5. **CEO dashboard** — Odoo Spreadsheet with PIVOT connections, one per entity + consolidated

### 3.2 Budget Domains Overview

```
                         ┌──────────────────────────┐
                         │    CEO Dashboard          │
                         │  (Odoo Spreadsheet)       │
                         │  Per company + consol.    │
                         └────────┬─────────────────┘
                                  │
    ┌──────────┬──────────┬───────┼───────┬──────────┬──────────┬──────────┐
    │          │          │       │       │          │          │          │
 ┌──▼──┐  ┌───▼───┐  ┌───▼──┐ ┌─▼──┐ ┌──▼───┐  ┌──▼──┐  ┌───▼───┐  ┌──▼──┐
 │SALES│  │EXPENSE│  │ PROD │ │STCK│ │ CASH │  │ FTE │  │  KPI  │  │PIPE │
 │  1  │  │   2   │  │   3  │ │ 4  │ │FLOW 5│  │  6  │  │   7   │  │  8  │
 └─────┘  └───────┘  └──────┘ └────┘ └──────┘  └─────┘  └───────┘  └─────┘
Country    GL+CC      m3+dryer  m3    EBITDA     BU       OTIF+DSO   Backlog
Area(US)   Monthly    loads     Days  WCR+FCF    Heads    Monthly    Top 10
Rev+Vol              Clear/Rad        Capex
GM1                                   Cash pos.
```

---

## 4. Domain 1 — Sales Budget

### 4.1 Model: `kebony.budget.sales`

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version (BP2026, RF1-2026…) |
| `period` | Date | First day of month |
| `company_id` | M2O | Entity (INC, BNV) |
| `country_id` | M2O | Target country |
| `sales_area_id` | M2O | Sales area (US — optional, null for non-US) |
| `currency_id` | M2O | USD or EUR |
| `amount` | Float | Revenue target in local currency |
| `volume_m3` | Float | Volume target in m3 |
| `volume_lf` | Float | Volume in linear feet (US) |
| `volume_lm` | Float | Volume in linear meters (BE) |
| `cogs_amount` | Float | Expected COGS (for GM1 calc) |
| `gm1_target_pct` | Float | GM1 margin target % |

### 4.2 Sales Area Handling

- **BP 2026**: US budget entered at country level. One `sales_area_id` = "US National" (catch-all). Actuals still break down by real sales area in the dashboard.
- **BP 2027+**: US can decline budget per sales area. Model is ready — just create lines per area.
- **Belgium / EU**: no sales areas. `sales_area_id` stays null. Budget per destination country.

### 4.3 Actual Computation

Actuals come from **existing** data — no double entry:

| Measure | Source | How |
|---------|--------|-----|
| Revenue | `account.move.line` posted invoices | SUM amount by country/period |
| Volume m3 | `x_kebony_total_volume_m3` on invoice | SUM by country/period |
| COGS | `x_studio_cogs` on invoice header | SUM by country/period |
| GM1 | Revenue - COGS | Computed |
| GM1 % | GM1 / Revenue | Computed |

### 4.4 Units

All four units captured per line:
- **Amount** (USD or EUR) — primary financial measure
- **m3** — universal physical volume
- **LF** (US) / **LM** (Belgium) — linear measure in local convention

---

## 5. Domain 2 — Expense Budget (GL)

### 5.1 Current State

The **Cost Version BU Lines** (`kebony.cost.version.bu.line`) already capture planned amounts per Business Unit + GL account. This is close to what we need but:

- Currently stored under manufacturing cost centers only
- Missing: SG&A, marketing, logistics, admin GL accounts
- Missing: period breakdown (cost version is annual, not monthly)

### 5.2 Proposal: Extend Cost Version

Rather than a new model, extend `kebony.cost.version.bu.line` with:

| New Field | Type | Description |
|-----------|------|-------------|
| `period` | Date | Monthly period (null = annual as today) |
| `company_id` | M2O | Entity |

**Migration**: existing annual lines remain valid. New lines can be entered monthly. Dashboard aggregates both (annual / 12 for pro-rata if no monthly detail).

### 5.3 EBITDA Construction

EBITDA is **not a budget line** — it's a computed aggregation:

```
EBITDA = Revenue (Domain 1)
       - COGS (Domain 1)
       - SG&A expenses (Domain 2, specific GL ranges)
       - Marketing (Domain 2)
       + Depreciation add-back (Domain 2, GL 6xx)
       + Amortisation add-back (Domain 2, GL 6xx)
```

The dashboard computes EBITDA from the underlying domains. We define a **GL account mapping** that classifies each account into the EBITDA waterfall.

---

## 6. Domain 3 — Production Budget

### 6.1 Model: `kebony.budget.production`

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version |
| `period` | Date | Month |
| `company_id` | M2O | Entity |
| `production_chain` | Selection | `character` (Scots Pine) / `clear` (Radiata) |
| `output_volume_m3` | Float | Target production output in m3 |
| `dryer_loads` | Integer | Number of dryer loads planned |

### 6.2 Actual Computation

| Measure | Source |
|---------|--------|
| Output m3 | Completed Manufacturing Orders (`mrp.production`, state=done), SUM product qty × volume factor, grouped by month + production chain |
| Dryer loads | `kebony.dryer.load` count by month + production chain (state=done) |

### 6.3 Dashboard View

```
PRODUCTION         │  BP    │ Actual │  Var  │  LY
───────────────────┼────────┼────────┼───────┼──────
Character (SP) m3  │   XX   │   XX   │  XX%  │ (n/a)
Character loads    │   XX   │   XX   │  XX%  │
Clear (Rad) m3     │   XX   │   XX   │  XX%  │ (n/a)
Clear loads        │   XX   │   XX   │  XX%  │
TOTAL m3           │   XX   │   XX   │  XX%  │
TOTAL loads        │   XX   │   XX   │  XX%  │
```

---

## 7. Domain 4 — Stock Level Targets

### 7.1 Model: `kebony.budget.stock`

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version |
| `period` | Date | Month |
| `company_id` | M2O | Entity |
| `location_id` | M2O | Stock location (warehouse) |
| `product_category` | Selection | `raw_material`, `semi_finished`, `finished_goods` |
| `target_volume_m3` | Float | Target stock volume in m3 |
| `target_days` | Float | Target days of inventory (DOS) |

### 7.2 Actual Computation

| Measure | Source |
|---------|--------|
| Current stock m3 | `stock.quant` aggregated by location + category |
| Days of stock | Current stock m3 / (trailing 90-day consumption m3 / 90) |

### 7.3 Category Mapping

| Category | Rule |
|----------|------|
| **Raw Material** | White wood input products |
| **Semi-Finished** | Treated but not machined (brown wood / rough sawn) |
| **Finished Goods** | Machined, sellable products |

---

## 8. Domain 5 — Cash Flow Budget

### 8.1 Model: `kebony.budget.cashflow`

Indirect method — monthly cash flow budget derived from EBITDA down to cash position.

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version |
| `period` | Date | Month |
| `company_id` | M2O | Entity |
| **EBITDA** | | |
| `ebitda` | Float | From Domain 1+2 (can be overridden) |
| **Working Capital Changes** | | |
| `delta_inventory` | Float | Δ inventory value (stock target → value) |
| `delta_receivables` | Float | Δ trade receivables (AR) |
| `delta_payables` | Float | Δ trade payables (AP) |
| `delta_other_wcr` | Float | Δ other WCR items (prepayments, accruals) |
| **Investment** | | |
| `capex` | Float | Capital expenditure |
| `other_investing` | Float | Other investing activities |
| **Financial** | | |
| `interest_paid` | Float | Financial costs |
| `other_financial` | Float | Dividends, FX, other |

### 8.2 Computed Fields

```
Operating Cash Flow  = EBITDA - Δ Inventory - Δ AR + Δ AP - Δ Other WCR
Free Cash Flow       = Operating CF - Capex - Other Investing
Net Cash Movement    = FCF - Interest - Other Financial
Closing Cash         = Opening Cash + Net Cash Movement
```

Opening cash = prior month's closing cash (or manual entry for month 1).

### 8.3 Actual Computation

All WCR components readable from balance sheet GL accounts at month-end:

| Component | GL Accounts |
|-----------|-------------|
| Inventory value | 110200 (FIFO valuation) |
| Trade receivables | 120xxx (AR) |
| Trade payables | 200xxx (AP) |
| Cash position | 100xxx (Bank + Cash) |
| Capex | Fixed asset additions (from asset module) |

---

## 9. Domain 6 — FTE Headcount

### 9.1 Model: `kebony.budget.fte`

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version |
| `period` | Date | Month |
| `company_id` | M2O | Entity |
| `business_unit_id` | M2O | BU (Sales, Operations, Admin, Leadership…) |
| `fte_count` | Float | Number of FTEs (0.5 for part-time) |
| `total_cost` | Float | Total personnel cost for the BU |

### 9.2 Actual Computation

- If HR module active: `hr.employee` count by department, mapped to BU
- If not: manual entry or payroll GL totals by cost center

---

## 10. Domain 7 — Operational KPIs

### 10.1 Model: `kebony.budget.kpi`

Flexible KPI budget — each line is a named KPI with target and actual.

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | M2O | Budget version |
| `period` | Date | Month |
| `company_id` | M2O | Entity |
| `kpi_code` | Selection | See below |
| `target_value` | Float | Budget target |
| `actual_value` | Float | Computed or manual |

### 10.2 KPI Registry

| Code | Name | Budgetable? | Actual Source |
|------|------|-------------|--------------|
| `otif` | On-Time In-Full Delivery % | Yes | `stock.picking`: promised date vs done date |
| `dso` | Days Sales Outstanding | Yes (US) | AR balance / (revenue / 90). US-sensitive (90% factoring + prepayment) |
| `claim_rate` | Quality Claim Rate % | Future | Claims / shipments |
| `crm_projects` | Architectural Projects in Pipe | Future (CRM) | `crm.lead` count by stage |

DSO is mostly relevant for the US (Belgium has factoring and prepayment). Still worth tracking.

---

## 11. Domain 8 — Order Pipeline (Actuals Only)

No budget — these are **actuals-only** indicators on the dashboard.

### 11.1 Order Backlog

| Measure | Source |
|---------|--------|
| Backlog value | Confirmed SO not yet fully shipped — SUM `sale.order.line` qty remaining × price |
| Backlog m3 | SUM remaining qty × volume factor |
| Backlog count | Number of open SO |

Already available from the SO Backorder report. Displayed as a trend line on the dashboard.

### 11.2 Top 10 Customers

| Measure | Source |
|---------|--------|
| Revenue YTD | Posted invoices grouped by partner, TOP 10 |
| Volume YTD | Same, m3 |
| vs LY | Same period last year (from 2027) |

Actuals only — no BP per customer for now. Model supports it if they decide to budget per customer later.

---

## 12. Budget Version Model

### 12.1 Model: `kebony.budget.version`

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | e.g. "BP 2026", "RF1 2026 Q2" |
| `fiscal_year` | Integer | 2026 |
| `version_type` | Selection | `budget`, `reforecast` |
| `sequence` | Integer | For reforecast ordering (RF1=1, RF2=2…) |
| `state` | Selection | `draft`, `approved`, `locked` |
| `company_id` | M2O | Entity this version belongs to |

All domain models reference this version. Each company has its own versions.

### 12.2 Workflow

```
Draft ──► Approved ──► Locked
              │
              └──► (Create RF1 as copy, modify, approve)
```

---

## 13. CEO Dashboard

### 13.1 Recommended Approach: Odoo Spreadsheet

Rather than building a custom dashboard view, use **Odoo Spreadsheet** (Enterprise):

**Why**:
- Live connection to Odoo data (PIVOT functions)
- Budget data entered in our custom models, actuals from standard Odoo
- Flexible layout — the CEO can rearrange without IT
- YoY comparison via two PIVOT calls (current year vs. prior year)
- Publishable as a dashboard to specific user groups
- No custom frontend development

### 13.2 Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  KEBONY — CEO DASHBOARD                  FY 2026  │ Entity: US  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─── SALES ───────────────────────────────────────────────────┐ │
│  │ Country │ BP Rev │ Act Rev │ Var% │ BP m3│ Act m3│ GM1 │GM1%│ │
│  │ USA     │   XX   │   XX    │  XX  │  XX  │  XX   │ XX  │XX% │ │
│  │ Belgium │   XX   │   XX    │  XX  │  XX  │  XX   │ XX  │XX% │ │
│  │ TOTAL   │   XX   │   XX    │  XX  │  XX  │  XX   │ XX  │XX% │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─── P&L WATERFALL ──────────┐  ┌─── CASH FLOW ──────────────┐ │
│  │         │ BP  │ Act │ LY   │  │              │ BP  │ Act    │ │
│  │ Revenue │ XX  │ XX  │(n/a) │  │ EBITDA       │ XX  │ XX     │ │
│  │ COGS    │ XX  │ XX  │      │  │ Δ Inventory  │ XX  │ XX     │ │
│  │ GM1     │ XX  │ XX  │      │  │ Δ AR         │ XX  │ XX     │ │
│  │ GM1 %   │ XX% │ XX% │      │  │ Δ AP         │ XX  │ XX     │ │
│  │ OpEx    │ XX  │ XX  │      │  │ Oper. CF     │ XX  │ XX     │ │
│  │ EBITDA  │ XX  │ XX  │      │  │ Capex        │ XX  │ XX     │ │
│  │ EBITDA% │ XX% │ XX% │      │  │ FCF          │ XX  │ XX     │ │
│  └─────────────────────────────┘  │ Cash Pos.    │ XX  │ XX     │ │
│                                   └──────────────────────────────┘ │
│                                                                  │
│  ┌─── PRODUCTION ─────────────┐  ┌─── INVENTORY ──────────────┐ │
│  │          │ BP  │ Act │ Var │  │ Loc  │ Cat │Tgt m3│Act│Days │ │
│  │ Char m3  │ XX  │ XX  │ XX%│  │ US   │ RM  │  XX  │XX │ XX  │ │
│  │ Char DL  │ XX  │ XX  │ XX%│  │ US   │ FG  │  XX  │XX │ XX  │ │
│  │ Clear m3 │ XX  │ XX  │ XX%│  │ BE   │ RM  │  XX  │XX │ XX  │ │
│  │ Clear DL │ XX  │ XX  │ XX%│  │ BE   │ FG  │  XX  │XX │ XX  │ │
│  │ TOTAL m3 │ XX  │ XX  │ XX%│  └──────────────────────────────┘ │
│  │ TOTAL DL │ XX  │ XX  │ XX%│                                   │
│  └─────────────────────────────┘                                 │
│                                                                  │
│  ┌─── KPIs ───────────┐  ┌─── PEOPLE ──────┐  ┌── BACKLOG ───┐ │
│  │      │Tgt │Act│ LY │  │ BU    │BP │Act  │  │ Orders │  XX │ │
│  │ OTIF │XX% │XX%│n/a │  │ Sales │XX │ XX  │  │ Value  │  XX │ │
│  │ DSO  │XX  │XX │n/a │  │ Ops   │XX │ XX  │  │ m3     │  XX │ │
│  └──────────────────────┘  │ Admin │XX │ XX  │  └──────────────┘ │
│                            │ TOTAL │XX │ XX  │                   │
│  LY = from Jan 2027       └─────────────────┘                   │
└──────────────────────────────────────────────────────────────────┘
```

### 13.3 Last Year Reference

- Dashboard includes LY columns from day one (structure ready)
- Columns show **(n/a)** until Jan 2027 when a full year of Odoo actuals exists
- No manual LY data entry — purely computed from prior-year posted entries

---

## 14. Implementation Plan

### Week 1 — Models + Forms (Development)

All 8 domain models, form/list views, Excel import wizard, security groups, menus. Straightforward Odoo model work — Float fields + foreign keys.

| # | Deliverable |
|---|-------------|
| 1 | `kebony.budget.version` model + form/list views |
| 2 | `kebony.budget.sales` model + entry form (with sales area) |
| 3 | `kebony.budget.production` model + entry form |
| 4 | `kebony.budget.stock` model + entry form |
| 5 | `kebony.budget.cashflow` model + entry form |
| 6 | `kebony.budget.fte` model + entry form |
| 7 | `kebony.budget.kpi` model + entry form |
| 8 | Extend `cost.version.bu.line` with period + company |
| 9 | Import wizard (Excel → budget lines, all domains) |
| 10 | Security groups + menu entries |

### Weeks 2–3 — Controller Input (Finance)

Development does NOT block on this — models are ready. Finance provides:

- GL account mapping for EBITDA waterfall (which accounts = D&A add-back)
- GM1 definition confirmation
- Stock category rules
- Cash flow opening balances
- **Actual BP numbers** (Excel files for import)

### Week 4 — Actuals Engine + Dashboard (Development)

SQL views for budget vs actual, Odoo Spreadsheet with PIVOT connections.

| # | Deliverable |
|---|-------------|
| 11 | Sales, production, stock, cash flow actuals views |
| 12 | EBITDA GL mapping + computation |
| 13 | KPI actuals (OTIF, DSO) + backlog + Top 10 |
| 14 | Budget vs Actual SQL views for PIVOT consumption |
| 15 | Odoo Spreadsheet dashboard with filters (period, version, entity) |
| 16 | LY column structure (auto-populates from 2027) |

### Post Go-Live — Validation

- US-only initially — need real transactional data flowing before meaningful validation
- Dashboard review with CEO once first month of actuals is available
- Belgium / other entities onboarded in a second pass

### Future — CRM Integration

| # | Deliverable | When |
|---|-------------|------|
| 17 | Architectural projects in pipe (CRM lead count by stage) | When CRM is implemented |
| 18 | Pipeline value forecast | When CRM is implemented |

**Total**: ~4 weeks development + validation post go-live.

---

## 15. Data Entry Workflow

### 15.1 Annual Budget (BP)

1. Finance creates a new **Budget Version** for each entity (e.g. "BP 2026 — Kebony INC")
2. Sales budget: enter revenue + volume + GM1 targets per country per month
3. Production budget: enter m3 output + dryer loads per chain per month
4. Expense budget: enter planned amounts per GL + cost center per month
5. Stock targets: enter target m3 + days per location per category
6. Cash flow: enter WCR assumptions, capex plan, financial costs per month
7. FTE: enter headcount + cost per BU per month
8. KPIs: enter OTIF target, DSO target
9. Version is approved and locked

### 15.2 Reforecast

1. Create **RF1** version (copy of BP with actuals YTD frozen)
2. Update remaining months with revised expectations
3. Dashboard shows both BP and RF1 columns

### 15.3 Excel Import

For initial load and annual planning:
- Template Excel with columns matching the budget models
- Import wizard validates and creates/updates lines
- One Excel template per domain (Sales, Production, Cash Flow, etc.)
- Avoids tedious manual entry in Odoo forms

---

## 16. What We Do NOT Build

| Capability | Reason |
|-----------|--------|
| **Real-time budget blocking** (e.g. block PO if over budget) | Not requested; adds friction |
| **Multi-currency consolidation** | Each entity budgets in local currency; dashboard shows side-by-side, no FX translation |
| **Rolling 12-month forecast** | Out of scope — reforecast covers the need |
| **Budget per customer** | Not requested for now — model supports it if needed later |
| **CRM pipeline** | Deferred until CRM module is implemented |

---

## 17. Open Questions

1. **GM1 definition for budget**: Revenue - COGS only, or include accruals (marketing, royalties, commissions)?
2. **Stock categories**: 4th category for **consignment** stock (Biewer)?
3. **Budget approval**: who approves? Single approver or multi-level?
4. **Currency**: does Belgium budget in EUR only, or also NOK for Norway entity?
5. **EBITDA GL mapping**: which GL accounts for D&A add-back? Need account list from finance.
6. **DSO scope**: US only or also track for Belgium (given factoring)?
7. **Production budget owner**: operations team or finance?
8. **Cash flow opening balance**: manual entry for month 1 of each fiscal year?
