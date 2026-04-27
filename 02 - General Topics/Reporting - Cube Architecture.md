# Kebony Cube — Unified Reporting & Budget Architecture

> **Status:** Architecture proposal — for SteerCo validation
> **Date:** 8 April 2026
> **Author:** Olivier Eberhard (VVF)
> **Reference:** ArcelorMittal Flat Carbon Europe — unified management cube (2018–2022)

---

## Executive Summary

One Odoo module. One fact table. Six dimensions. Two data feeds (actuals from SQL, budget from input forms). Replaces both the reporting strategy (Fabric/Power BI) and the budget module with a single unified structure.

**Cost:** ~6 weeks development vs. €300k+ Fabric deployment.
**Outcome:** One version of the truth — from raw material to CEO dashboard.

---

## The Insight

At ArcelorMittal Flat Carbon Europe, dozens of plants across the continent were unified under one analytical cube. The secret was not technology — it was **one Chart of Accounts that mixed financial accounts, managerial KPIs, and physical metrics into a single dimension**. A simple star schema with governance.

Kebony has the same need at a smaller scale: financial P&L, production KPIs, inventory metrics, cash flow, headcount — all in one place, budget vs. actual, with drill-down by entity, country, chain, period.

**This can be built natively in Odoo.**

---

## Star Schema

```
         PERIOD          ENTITY          VERSION
         (month)       (INC, BNV)     (BP, RF1, ACT)
            │               │               │
            └───────┬───────┘               │
                    │                       │
    ACCOUNT ────── FACT ──────────────── VERSION
   (unified       (value)
    CoA + KPIs)     │
                ┌───┴────┐
                │        │
           DIMENSION    UOM
          (country,   (EUR, USD,
           chain,      m³, LF, ft³,
           area,       boards, %,
           location,   days, FTE,
           BU)         kg, hours)
```

**6 dimensions + 1 value column.** Every KPI, every budget line, every actual — same structure.

---

## Dimension 1: ACCOUNT (the unified Chart of Accounts)

This is the core innovation. The account dimension is NOT just GL accounts. It's a **unified hierarchy** mixing financial, volume, operational, and people metrics.

```
ACCOUNT (kebony.cube.account)
│
├── 1. Financial (P&L Waterfall)
│   ├── REV        Revenue
│   ├── COGS-W     COGS — Wood
│   ├── COGS-C     COGS — Chemical
│   ├── COGS-V     COGS — Conversion
│   ├── COGS-M     COGS — Machining / RDK
│   ├── GM1        Gross Margin 1 (= REV - COGS)
│   ├── SGA        SG&A expenses
│   ├── MKT        Marketing
│   ├── EBITDA     (= GM1 - SGA - MKT)
│   ├── DA         Depreciation & Amortization
│   └── EBIT       (= EBITDA - DA)
│
├── 2. Volume
│   ├── VOL-SALES  Sales volume
│   ├── VOL-PROD   Production output
│   ├── VOL-DL     Dryer loads (count)
│   ├── VOL-INV    Inventory level
│   └── VOL-BACKLOG Order backlog
│
├── 3. Operational KPIs
│   ├── KPI-OTIF   On-time in-full %
│   ├── KPI-DSO    Days sales outstanding
│   ├── KPI-DOS    Days of stock
│   ├── KPI-OEE    Overall equipment effectiveness %
│   ├── KPI-SCRAP  Scrap rate %
│   └── KPI-YIELD  Process yield %
│
├── 4. Cash Flow (indirect method)
│   ├── CF-EBITDA  (ref → Financial.EBITDA)
│   ├── CF-DINV    Δ Inventory
│   ├── CF-DAR     Δ Accounts Receivable
│   ├── CF-DAP     Δ Accounts Payable
│   ├── CF-DWCR    Δ Other Working Capital
│   ├── CF-OCF     Operating Cash Flow (= EBITDA + ΔWCR)
│   ├── CF-CAPEX   Capital expenditure
│   ├── CF-FCF     Free Cash Flow (= OCF - Capex)
│   └── CF-CASH    Cash position (closing)
│
└── 5. People
    ├── PPL-FTE    Headcount (FTE)
    └── PPL-COST   Personnel cost
```

**Key property:** Each account has a `uom_allowed` list — REV only accepts EUR/USD, VOL-SALES accepts m³/LF/boards, KPI-OTIF accepts %, PPL-FTE accepts FTE. This enforces data quality at input.

**Computed accounts:** GM1, EBITDA, EBIT, OCF, FCF are **never entered** — they are computed from their children. The cube engine resolves the formulas. Same for LY variance.

---

## Dimension 2: UOM (Unit of Measure)

The UoM is a **first-class dimension**, not a column attribute. This means the same account can hold values in multiple units simultaneously.

| Code | Name | Domain |
|------|------|--------|
| EUR | Euro | Financial |
| USD | US Dollar | Financial |
| NOK | Norwegian Krone | Financial |
| M3 | Cubic meters | Volume |
| LM | Linear meters | Volume |
| LF | Linear feet | Volume |
| FT3 | Cubic feet | Volume |
| BRD | Boards (count) | Volume |
| KG | Kilograms | Chemical/weight |
| HRS | Hours | Production |
| PCT | Percentage | KPIs |
| DAYS | Days | KPIs (DSO, DOS) |
| FTE | Full-time equivalent | People |
| DL | Dryer loads (count) | Production |
| UNIT | Unitless count | Generic |

**Example — Sales for USA, March 2026:**

| Account | UoM | BP value | Actual value |
|---------|-----|----------|-------------|
| REV | USD | 450,000 | 412,000 |
| REV | EUR | 415,000 | 380,000 |
| VOL-SALES | M3 | 1,400 | 1,280 |
| VOL-SALES | LF | 46,000 | 42,100 |
| VOL-SALES | BRD | 14,000 | 12,800 |
| GM1 | USD | 135,000 | 127,700 |
| GM1 | PCT | 30% | 31% |

**Budget input:** Controller enters Revenue in USD + Volume in m³. The system can auto-derive EUR (at budget FX rate), LF (at product conversion factor), boards (at average boards/m³).

---

## Dimension 3: ENTITY (Company)

| Code | Name | Currency |
|------|------|----------|
| INC | Kebony Inc. (US) | USD |
| BNV | Kebony BNV (Belgium) | EUR |
| CONS | Consolidated (interco eliminated) | EUR |

Consolidation = sum of entities with intercompany elimination rules on specific accounts (interco revenue, interco COGS, interco inventory).

---

## Dimension 4: PERIOD

Monthly granularity. Fiscal year = calendar year.

| Level | Example | Use |
|-------|---------|-----|
| Month | 2026-03 | Primary grain |
| Quarter | 2026-Q1 | Roll-up (computed) |
| Year | 2026 | Roll-up (computed) |
| YTD | 2026-YTD-03 | Cumulative (computed) |

**Actuals:** Posted by accounting period (Odoo fiscal period).
**Budget:** Entered monthly, locked after approval.

---

## Dimension 5: VERSION

| Code | Name | Editable | Notes |
|------|------|----------|-------|
| BP2026 | Budget Plan 2026 | Locked after approval | Annual budget |
| RF1-2026 | Reforecast 1 (2026) | Locked after approval | Mid-year revision |
| RF2-2026 | Reforecast 2 (2026) | Locked after approval | Q3 revision |
| ACT | Actuals | Auto-computed | From SQL (never manually entered) |
| LY | Last Year Actuals | Auto-computed | = ACT shifted -12 months (from 2027) |

**Variance** is never stored — always computed at query time: `Var% = (ACT - BP) / BP`.

---

## Dimension 6: DIMENSION (flexible analytical axis)

This is the catch-all for business segmentation. It's a **parent-child hierarchy** that supports multiple classification trees.

```
DIMENSION (kebony.cube.dimension)
│
├── GEOGRAPHY
│   ├── USA
│   │   ├── East Coast (US sales area)
│   │   ├── West Coast
│   │   └── Central
│   ├── Belgium
│   ├── France
│   ├── Norway
│   ├── Denmark
│   ├── UK
│   └── Other
│
├── CHAIN (product chain)
│   ├── Character (Scots Pine)
│   └── Clear (Radiata)
│
├── LOCATION (for inventory accounts)
│   ├── Kallo (Belgium plant)
│   ├── Pasadena (US warehouse)
│   ├── Thomson (US warehouse)
│   └── RDK (subcontractor)
│
├── BU (business unit — for expense/people accounts)
│   ├── Sales
│   ├── Operations / Production
│   ├── Admin / Finance
│   ├── Marketing
│   └── Leadership
│
├── STOCK-CAT (for inventory accounts)
│   ├── Raw Material
│   ├── Semi-Finished
│   ├── Finished Goods
│   └── Consignment
│
└── ALL (default — no segmentation)
```

**Not every account uses every dimension.** Revenue is segmented by Geography + Chain. Production by Chain only. FTE by BU only. Inventory by Location + Stock-Cat. The account definition specifies which dimension branches are valid.

---

## Fact Table

```sql
CREATE TABLE kebony_cube_fact (
    id              SERIAL PRIMARY KEY,
    account_id      INT NOT NULL,    -- → kebony.cube.account
    entity_id       INT NOT NULL,    -- → res.company
    period_id       INT NOT NULL,    -- → kebony.cube.period (YYYY-MM)
    version_id      INT NOT NULL,    -- → kebony.cube.version (BP/RF/ACT)
    dimension_id    INT NOT NULL,    -- → kebony.cube.dimension
    uom_id          INT NOT NULL,    -- → kebony.cube.uom
    value           FLOAT NOT NULL,  -- the number

    -- Metadata
    source          VARCHAR,         -- 'budget_input' | 'sql_actual' | 'computed'
    last_updated    TIMESTAMP
);

-- Unique constraint: one value per intersection
UNIQUE (account_id, entity_id, period_id, version_id, dimension_id, uom_id)
```

**That's it.** One table. Six foreign keys. One value. Every KPI in the company.

---

## Two Data Feeds

### Feed 1: Actuals (SQL Views → Fact Table)

Automated SQL statements that read from live Odoo tables and insert/update into the fact table with `version_id = ACT`.

**Example — Revenue actuals:**
```sql
SELECT
    'REV' as account,
    move.company_id as entity,
    to_char(move.date, 'YYYY-MM') as period,
    'ACT' as version,
    partner.country_id as dimension,  -- geography
    move.currency_id as uom,          -- EUR or USD
    SUM(line.credit - line.debit) as value
FROM account_move_line line
JOIN account_move move ON move.id = line.move_id
JOIN account_account acct ON acct.id = line.account_id
JOIN res_partner partner ON partner.id = move.partner_id
WHERE move.state = 'posted'
  AND acct.code LIKE '700%'           -- revenue accounts
GROUP BY move.company_id, to_char(move.date, 'YYYY-MM'),
         partner.country_id, move.currency_id
```

**Example — Production actuals:**
```sql
SELECT
    'VOL-PROD' as account,
    mo.company_id as entity,
    to_char(mo.date_start, 'YYYY-MM') as period,
    'ACT' as version,
    family.family_type as dimension,  -- chain (character/clear)
    'M3' as uom,
    SUM(mo.qty_produced * tmpl.x_studio_volume_m3) as value
FROM mrp_production mo
JOIN product_product pp ON pp.id = mo.product_id
JOIN product_template tmpl ON tmpl.id = pp.product_tmpl_id
JOIN kebony_planning_family family ON family.id = tmpl.kebony_planning_family_id
WHERE mo.state = 'done'
GROUP BY mo.company_id, to_char(mo.date_start, 'YYYY-MM'),
         family.family_type
```

**Refresh cadence:** Nightly batch (cron job) or on-demand button. Actuals are always recomputed, never manually adjusted.

### Feed 2: Budget (Input Forms → Fact Table)

Manual entry by controllers via Odoo forms. Each budget domain maps to a specific set of accounts.

**Sales budget form:** Entity + Country + Month → Revenue (EUR/USD) + Volume (m³) + GM1 target (%)
**Expense budget form:** Entity + GL Account + Cost Center + Month → Amount (EUR)
**Production budget form:** Entity + Chain + Month → Output m³ + Dryer loads
**Stock budget form:** Entity + Location + Category + Month → Target m³ + Target days
**Cash flow form:** Entity + Month → ΔWCR assumptions + Capex plan
**FTE form:** Entity + BU + Month → FTE count + Cost

Each form writes directly to the fact table. Version = BP2026 (or RF1, RF2...).

---

## CEO Dashboard

The CEO dashboard is an **Odoo Spreadsheet** with PIVOT formulas pointing at the fact table. One spreadsheet, multiple tabs:

| Tab | Accounts | Dimensions | UoMs |
|-----|----------|-----------|------|
| Sales | REV, VOL-SALES, GM1 | Geography | EUR/USD + m³/LF |
| P&L Waterfall | REV → EBITDA | ALL | EUR |
| Production | VOL-PROD, VOL-DL, KPI-SCRAP | Chain | m³ + DL + % |
| Inventory | VOL-INV, KPI-DOS | Location × Stock-Cat | m³ + days |
| Cash Flow | CF-* | ALL | EUR |
| People | PPL-FTE, PPL-COST | BU | FTE + EUR |
| KPIs | KPI-OTIF, KPI-DSO | Geography | % + days |

Each tab shows: **BP | Actual | Var% | LY** columns. Filter by entity (INC/BNV/Consolidated) and period.

---

## Implementation

### Models (Odoo)

| Model | Purpose | Records |
|-------|---------|---------|
| `kebony.cube.account` | Unified CoA (financial + KPI + volume) | ~40 |
| `kebony.cube.uom` | Unit of measure dimension | ~15 |
| `kebony.cube.period` | Monthly periods | 12/year |
| `kebony.cube.version` | BP, RF, ACT, LY | ~5 |
| `kebony.cube.dimension` | Flexible analytical axis (parent-child) | ~30 |
| `kebony.cube.fact` | The fact table | ~10k rows/year |

### Views

| View | Purpose |
|------|---------|
| Account tree + form | Define the unified CoA hierarchy |
| Dimension tree | Manage the dimension hierarchy |
| Budget input form (per domain) | Controller data entry |
| Fact table pivot | Ad-hoc analysis |
| Odoo Spreadsheet | CEO Dashboard |

### Automation

| Job | Schedule | What |
|-----|----------|------|
| Refresh actuals | Nightly (cron) | Run SQL views, upsert into fact table |
| Compute derived accounts | After refresh | GM1, EBITDA, FCF, variances |
| LY population | Jan 1 each year | Copy prior year ACT → LY version |

### Effort

| Phase | Weeks | What |
|-------|-------|------|
| 1 — Core models + fact table | 1 | Models, security, menus |
| 2 — Actuals SQL views | 2 | ~15 SQL views covering all account families |
| 3 — Budget input forms | 1 | 6 domain forms writing to fact table |
| 4 — CEO Dashboard | 1 | Odoo Spreadsheet with PIVOTs |
| 5 — Excel import/export | 0.5 | Template-based budget import |
| 6 — Testing + validation | 0.5 | With controller, real data |
| **Total** | **~6 weeks** | |

---

## Why This Works

1. **One table** — no data silos, no ETL pipelines, no Bronze/Silver/Gold layers
2. **Two feeds** — actuals are automated (SQL), budget is manual (forms). They never mix.
3. **Six dimensions** — enough to slice any KPI any way the CEO wants
4. **UoM as dimension** — same account in EUR, USD, m³, LF, %, days — no column explosion
5. **Computed accounts** — GM1, EBITDA, FCF are formulas, never entered, never wrong
6. **Governance built-in** — account defines allowed UoMs and dimensions. Can't enter revenue in kg.
7. **Odoo-native** — no external tools, no licences, no consultants. Same team that builds it maintains it.
8. **Scalable** — add a new KPI = add one account row. Add a new country = add one dimension row. Zero code change.

---

## Comparison with Fabric Approach

| Aspect | Fabric Stack | Odoo Cube |
|--------|-------------|-----------|
| Architecture | 7 sources → ETL → Lakehouse → Power BI | Odoo → SQL views → Fact table → Spreadsheet |
| Sources | 7 (Odoo, Prediktor, Salesforce, D365, AX, Perfion, WordPress) | 1 (Odoo) + daily MES log |
| Layers | Bronze → Silver → Gold → Semantic → Dashboard | Fact table → Spreadsheet |
| KPI definitions | ETL transforms (Data Factory) | SQL views (in Odoo) |
| Budget entry | External tool or Excel upload | Odoo forms (native) |
| Dashboard | Power BI (separate licence) | Odoo Spreadsheet (included) |
| Year 1 cost | €265–485k | €30–50k |
| Ongoing cost | €115–185k/year | €5–10k/year |
| Team needed | Data engineers + BI analysts + Odoo devs | Odoo devs only |
| Time to value | 6–12 months | 6 weeks |
| Copilot AI | Yes (Phase 3) | No (but Odoo AI evolving) |

---

## Open Questions

1. **Dimension granularity** — Is Geography × Chain sufficient for sales, or do we need Geography × Chain × Product Group?
2. **Currency conversion** — Budget FX rate per version? Or always entity currency?
3. **Intercompany elimination** — Needed for consolidated view? Which accounts?
4. **MES integration** — Daily manual log or API from Prediktor? Or defer entirely?
5. **Access control** — Who can enter budget? Who can view actuals? By entity?
