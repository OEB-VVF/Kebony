# Analytical Accounting Architecture

**Scope**: All Kebony entities | **Module**: `kebony_bol_report` (future extension)
**Status**: White Paper — not yet implemented

---

## 1. Purpose

Kebony's GL is deliberately simplified: stock movements, production, and sales post to a small number of GL accounts. The analytical layer adds the multi-dimensional reporting structure **without** fragmenting the chart of accounts.

### MVP Principle: Structure First, Rules Later

The **analytic plans and accounts must be accessible from MVP / go-live**. They are the skeleton of all future management reporting — if the dimensions don't exist in the system, no data gets tagged, and nothing can be reported later.

However, the **allocation and auto-posting rules do not need to be 100% tested and fine-tuned on day one**. They can be phased in progressively because:

- Analytic distributions on journal entry lines can be **backfilled** at any time (bulk update or reclass journal)
- EOM allocation wizards can be run **retroactively** on historical periods
- Auto-posting rules can start simple (manual tagging) and be automated incrementally
- Mistakes in allocation are correctable via reclass journals — they don't corrupt the GL

**What must be ready at MVP**: 4 plans created, all analytic account values seeded, `x_kebony_sales_area` field on contacts, journal defaults configured.
**What can be phased**: BoM decomposition, EOM wizards, auto-posting overrides, country distribution of production costs.

The analytical plans differ by entity:

| Plan | Europe (BNV/Holding) | US (INC) | Question it answers |
|------|---------------------|----------|---------------------|
| **Country** | Yes (75 values) | Yes (USA, CAN, ...) | Where did we sell? |
| **Business Unit (BU)** | Yes (shared) | Yes (shared) | Which department owns the cost/revenue? |
| **CM Level** | Yes (shared) | Yes (shared) | Where in the P&L waterfall? |
| **Sales Area** | No | Yes (9 US/CAN regions) | Which US/Canada sales territory? |

Every journal entry line can carry a distribution across all plans simultaneously. This is native Odoo 19 multi-plan analytical distribution — no custom models needed for the plans themselves.

### Why Two Setups?

Kebony operates as an integrated group. Production happens in Belgium (Kallo). Sales happen from two entities:

- **Kebony BNV (Belgium)** sells to 75+ countries worldwide — Country plan tracks destination
- **Kebony Inc. (US)** sells within North America — Sales Area provides the sub-regional granularity that matters for US/Canada sales force management

Country is still needed on the US side because Kebony Inc. sells in **both the US and Canada**, and the margin per country must be tracked. Additionally, intercompany sales from Belgium to the US (BNV → INC) carry a transfer price. The **consolidated Kebony margin** on a sale to a US end-customer includes both the Belgian production margin and the US distribution margin — this must be reconstructable via analytics.

```
                    INTERCOMPANY MARGIN CHAIN
                    ==========================

Belgium (BNV):                                     Country = USA (decided)
  Revenue from IC sale to INC     100 €/m³
  - COGS (production)             -70 €/m³
  = BNV margin on IC sale          30 €/m³   ← tracked in BNV analytics

US (INC):                                          Country = USA or CAN (from end customer)
  Revenue from end customer       180 $/m³
  - COGS (IC purchase from BNV)  -100 €/m³
  - Mgmt fees (reinvoiced to BNV) -11 $/m³   ← reduces INC margin, reallocated to Europe
  = INC margin on resale           69 $/m³   ← tracked in INC analytics

Consolidated Kebony margin:
  End customer revenue            180 $/m³
  - True production cost          -70 €/m³
  = Group margin                  110 $/m³   ← reconstructable from both
```

> **Canada gap**: BNV's IC sale is tagged Country=USA (100%). When INC resells to a Canadian customer, INC's revenue is tagged Country=CAN. This creates a mismatch: BNV's margin on that sale is under USA, but the end-customer is in Canada. **Fine-tuned later** by EOM reallocation of BNV's IC margin proportional to INC's m³ by country.

> **Management fees**: INC pays management fees to Europe (Holding/BNV). This is an intercompany reinvoice that **reduces INC's margin** but must be **normatively reallocated to Europe** in the consolidated P&L. The mgmt fee appears as CORP in INC's CM waterfall, but in the group view it is a European cost funded by INC.

---

## 2. Design Principle: One GL Account, Many Analytics

```
  EUROPE (BNV) JOURNAL ENTRY LINE      US (INC) JOURNAL ENTRY LINE
  ==================================    ==================================
  Account: 500000 (COGS-FG)            Account: 500000 (COGS-FG)
  Debit:   10,000 EUR                  Debit:   12,000 USD

  Analytic Distribution:                Analytic Distribution:
  ┌──────────────────────────────┐      ┌──────────────────────────────┐
  │ Country:   DEU (100%)        │      │ Country:   USA (100%)        │
  │ BU:        Sales Intl (52)   │      │ Sales Area: North East       │
  │ CM Level:  COGS-D            │      │ BU:        Sales Intl (52)   │
  └──────────────────────────────┘      │ CM Level:  COGS-D            │
                                        └──────────────────────────────┘
```

**Why?**

- GL stays clean: one COGS account, one revenue account, one overhead account
- Reporting by country, BU, sales area, or CM level comes from analytic pivot, not from GL structure
- No chart-of-accounts explosion (no "COGS-USA-NorthEast-Sales-GMI" accounts)
- Odoo's native analytic reporting, pivot tables, and budget tools work out of the box

---

## 3. Plan 1: Country

Tracks all revenue and cost by **sales territory / geography**. Primary use: challenge sales force performance by region, analyse margin by destination market.

### Values

| Code | Name |
|------|------|
| ARE | United Arab Emirates |
| ARG | Argentina |
| AUS | Australia |
| AUT | Austria |
| BEL | Belgium |
| BENELUX | Belgium, Netherlands & Luxembourg (region) |
| BIH | Bosnia & Herzegovina |
| BRA | Brazil |
| CAN | Canada |
| CHE | Switzerland |
| CHL | Chile |
| CHN | China |
| CHZ | Czech Republic |
| COL | Colombia |
| COM | Common (shared / unallocated) |
| CRI | Costa Rica |
| CYP | Cyprus |
| DEU | Germany |
| DNK | Denmark |
| DOM | Dominican Republic |
| EGY | Egypt |
| ESP | Spain |
| EST | Estonia |
| FIN | Finland |
| FO | Faroe Islands |
| FRA | France |
| GBR | United Kingdom |
| GEO | Georgia |
| GRC | Greece |
| HKG | Hong Kong |
| HRV | Croatia |
| HUN | Hungary |
| IDN | Indonesia |
| IOT | India |
| IRL | Ireland |
| IRN | Iran |
| ISL | Iceland |
| ISR | Israel |
| ITA | Italy |
| JPN | Japan |
| KEN | Kenya |
| KOR | Korea |
| LTU | Lithuania |
| LUX | Luxembourg |
| LVA | Latvia |
| MAR | Morocco |
| MDV | Maldives |
| ME | Middle East (region) |
| MEX | Mexico |
| MLT | Malta |
| MNE | Montenegro |
| MYS | Malaysia |
| NLD | Netherlands |
| NOR | Norway |
| NZL | New Zealand |
| PAK | Pakistan |
| PHL | Philippines |
| POL | Poland |
| PRT | Portugal |
| PYF | French Polynesia |
| REU | Rest of EU (catch-all) |
| ROU | Romania |
| ROW | Rest of the World (catch-all) |
| RUS | Russia |
| SGP | Singapore |
| SVK | Slovakia |
| SVN | Slovenia |
| SWE | Sweden |
| SYC | Seychelles |
| THA | Thailand |
| TTO | Trinidad and Tobago |
| TUR | Turkey |
| TWN | Taiwan |
| TZS | Tanzania |
| UKR | Ukraine |
| USA | United States |
| VNM | Vietnam |
| ZAF | South Africa |

### Assignment Rules

| Transaction | Country Source |
|---|---|
| Customer invoice | Shipping address country (or partner country) |
| COGS journal entry | Inherited from the sales order / invoice |
| Production costs | Not country-assigned at production time — allocated at EOM |
| Overhead | Allocated at EOM via rules |

---

## 4. Plan 2: Business Unit (BU)

Tracks costs and revenue by **organisational division**. Terminology is "BU" but in practice it is a hybrid between business unit (for revenue-generating divisions) and cost centre (for support functions).

### Values

| Code | Name |
|------|------|
| 10 | Leadership |
| 15 | Finance / IT |
| 20 | Logistics / Warehouse |
| 21 | Planning / Customer Service |
| 30 | Operations |
| 50 | Sales Scandinavia |
| 52 | Sales International |
| 60 | Market (Marketing) |
| 70 | R&D / Product Development / Quality |

### Assignment Rules

| Transaction | BU Source | Entity |
|---|---|---|
| Revenue (customer invoice) | Sales team → Sales Scandinavia (50) or Sales International (52) | All |
| COGS (delivery / stock valuation) | Operations (30) | All |
| Payroll | Department of employee | All |
| Marketing costs (accruals, campaigns, rebates, trade shows) | Market (60) | All |
| Sales rep costs (commissions, accruals) | Sales Scandinavia (50) or Sales International (52) | All |
| Logistics / freight / warehousing | Logistics / Warehouse (20) | All |
| R&D / product development / lab | R&D (70) | All |
| Overhead (corporate, legal, rent, insurance) | Finance / IT (15) or Leadership (10) | All |

---

## 5. Plan 3: Sales Area (US Only)

Tracks revenue and cost by **US/Canada sales territory**. This plan exists only for Kebony Inc. and provides the sub-regional detail needed to manage the North American sales force.

**Sales Area is a contact-level field** on `res.partner`. When a sales order or invoice is created, the Sales Area is inherited automatically:

```
res.partner (customer)          →  field: x_kebony_sales_area
  └→ sale.order (header)        →  inherited from partner
       └→ sale.order.line       →  inherited from header
            └→ account.move     →  inherited from SO
                 └→ account.move.line  →  inherited from invoice header
```

This ensures every revenue line and every COGS line (via SO linkage) carries the correct Sales Area without manual entry.

### Values

| Code | Sales Area |
|------|------------|
| CENTRAL | Central |
| EAST-CAN | East Canada |
| MIDWEST | Midwest |
| N-ROCKIES | N. Rockies |
| NORTH-EAST | North East |
| OEM | OEM |
| SOUTH-EAST | South East |
| WEST | West |
| WEST-CAN | West Canada |

### Assignment Rules

| Transaction | Sales Area Source |
|---|---|
| Sales order | From customer contact (`res.partner.x_kebony_sales_area`) |
| Customer invoice | Inherited from SO header (or from partner if created directly) |
| Invoice lines | Inherited from invoice header |
| COGS (delivery → stock valuation JE) | Inherited from originating SO / invoice |
| US overhead | Allocated at EOM proportional to revenue or m³ per area |

> **Note**: Sales Area is orthogonal to Country. A sale in the "East Canada" area has Country = CAN. A sale in "North East" has Country = USA. Both dimensions are tracked independently.

---

## 6. Plan 4: Contribution Margin (CM) Level

This is the core management reporting axis. It follows the Kebony **P&L waterfall** — every cost and revenue line is tagged with its position in the margin cascade.

### The Kebony P&L Waterfall

```
    Net Sales (Revenue)
    ─────────────────────────────────────────────────
  - COGS Direct (raw wood FIFO, chemicals, packaging)
    ═════════════════════════════════════════════════
  = GM I    (Gross Margin I — material margin)
    ─────────────────────────────────────────────────
  - COGS Indirect (conversion: stacking, autoclave,
                    dryer absorption, plant overhead)
    ═════════════════════════════════════════════════
  = GM II   (Gross Margin II — production margin)
    ─────────────────────────────────────────────────
  - Supply Chain Costs (logistics, warehousing, 3PL)
  - Sales Costs (commissions, sales rep charges)
  - Marketing (accruals, campaigns, rebates)
  - Corporate (leadership, finance, IT, legal)
  - R&D / Product Development
    ═════════════════════════════════════════════════
  = EBITDA pre-ESOP
    ─────────────────────────────────────────────────
  - ESOP
    ═════════════════════════════════════════════════
  = EBITDA
    ─────────────────────────────────────────────────
  - Depreciation & Amortisation
  - Write-offs
    ═════════════════════════════════════════════════
  = EBIT
    ─────────────────────────────────────────────────
  - Financial items (interest, FX)
    ═════════════════════════════════════════════════
  = Net Income
```

### CM Level Analytical Values

| Code   | CM Level                    | What goes here                                                          |
| ------ | --------------------------- | ----------------------------------------------------------------------- |
| REV    | Net Sales                   | Customer invoice revenue lines                                          |
| COGS-D | COGS Direct                 | Raw wood (FIFO), chemicals (ready-mix), packaging                       |
| COGS-I | COGS Indirect               | Conversion absorption: stacking, autoclave, dryer hours, plant overhead |
| SC     | Supply Chain                | Freight, warehousing, 3PL costs, landed costs                           |
| SALES  | Sales Costs                 | Sales rep commissions, sales rep accruals                               |
| MKT    | Marketing                   | Marketing accruals, campaigns, rebates, trade shows                     |
| CORP   | Corporate                   | Leadership, finance, IT, legal, rent, insurance                         |
| RD     | R&D                         | Product development, quality, lab                                       |
| ESOP   | ESOP                        | Employee stock option plan charges                                      |
| DA     | Depreciation & Amortisation | Non-cash charges                                                        |
| FIN    | Financial                   | Interest, FX gains/losses                                               |

### Key Margins Derived

| Margin | Formula |
|--------|---------|
| **GM I** | REV - COGS-D |
| **GM II** | GM I - COGS-I |
| **EBITDA pre-ESOP** | GM II - SC - SALES - MKT - CORP - RD |
| **EBITDA** | EBITDA pre-ESOP - ESOP |
| **EBIT** | EBITDA - DA |
| **Net Income** | EBIT - FIN |

---

## 7. Allocation Mechanism

### The Problem

Not all costs are directly assignable at transaction time:

1. **Production costs** post to a single COGS GL account when goods are sold. The GL entry knows the total cost but not the split between direct materials (GM I) and indirect conversion (GM II).

2. **Overhead** (payroll, rent, utilities) is booked to GL expense accounts by nature. Only a portion is absorbed into production via work centre rates. The **unabsorbed remainder** must be allocated at month-end.

3. **Country** is known for revenue (customer address) but not for production costs — these must be allocated proportionally.

### The Solution: Two-Stage Allocation

```
STAGE 1 — AT TRANSACTION TIME (automatic)
==========================================

Revenue (customer invoice):
  → Country: from customer shipping address
  → Sales Area: from customer (US only)
  → BU: from sales team
  → CM Level: REV

COGS (sale → delivery → COGS journal entry):
  → Country: inherited from invoice / sales order
  → Sales Area: inherited from invoice (US only)
  → BU: Operations (30)
  → CM Level: split by rule (see below)

Production (MO completion → FG valuation):
  → Country: NOT assigned (production is country-agnostic)
  → Sales Area: NOT assigned
  → BU: Operations (30)
  → CM Level: COGS-D for materials, COGS-I for conversion


STAGE 2 — END OF MONTH ALLOCATION (manual / wizard)
====================================================

Unabsorbed costs = Actual department cost - Absorbed via WC rates

Example:
  Operations payroll (actual):     €100,000
  Absorbed via WC rates in MOs:    - €90,000
  ─────────────────────────────────────────
  Unabsorbed:                       €10,000

  → Allocate €10,000 to COGS-I (CM Level)
  → Distribute across countries proportional to m³ sold (decided: always m³)
  → BU stays Operations (30)
```

### COGS Split Rule (GM I vs GM II) — BNV Only

The COGS split between direct materials (COGS-D → GM I) and conversion costs (COGS-I → GM II) **only applies to the production entity (BNV)**. The distribution entity (INC) does not need this split.

#### BNV: BoM-Based Decomposition

When BNV sells a finished good, the COGS journal entry posts one debit line. But the cost contains both direct and indirect components. The split comes from the **BoM cost structure**:

```
BNV Finished Good Cost (from FIFO layer):  €500 / m³
  ├── Raw wood (FIFO):                     €280 / m³  →  COGS-D (GM I)
  ├── Chemical (ready-mix):                 €30 / m³  →  COGS-D (GM I)
  ├── Packaging:                            €10 / m³  →  COGS-D (GM I)
  ├── Stacking absorption:                  €40 / m³  →  COGS-I (GM II)
  ├── Autoclave absorption:                 €50 / m³  →  COGS-I (GM II)
  └── Dryer absorption:                     €90 / m³  →  COGS-I (GM II)
```

**Implementation options** (BNV):

1. **Percentage-based rule**: apply a fixed direct/indirect split ratio (e.g., 64% direct / 36% indirect) derived from standard cost. Simple, fast, updated quarterly.
2. **BoM-based decomposition** ⭐ PREFERRED: at COGS posting time, decompose the FIFO cost via the product's BoM structure. More accurate, leverages Odoo's existing BoM data. Each product already has a BoM with material lines (→ COGS-D) and operation lines with WC rates (→ COGS-I). The ratio can be computed from standard BoM cost and applied to actual FIFO cost.
3. **EOM allocation only**: post COGS to a single CM level, then run a monthly reclass journal to split direct vs indirect based on actual production data.

> **⚠ KEY DESIGN DECISION** — See §14 (Decisions Still To Be Made). BoM-based decomposition is the preferred approach because it uses real product-specific ratios rather than a blanket percentage. However, it requires that BoMs are complete with accurate WC rates and material costs. The fallback (option 1) can be used for products without a valid BoM.

#### INC: No COGS Split Needed

INC is a distribution entity. It purchases finished goods from BNV at a transfer price and resells to end customers. **From INC's perspective, the entire COGS is direct cost (COGS-D)**. There is no conversion happening at INC — no factory, no work centres, no indirect production costs.

```
INC P&L Waterfall:
  Revenue (end customer sale)          $180 / m³
  ─────────────────────────────────────────────
  - COGS (purchase from BNV)           $120 / m³   → 100% COGS-D
  ═════════════════════════════════════════════════
  = GM I                                $60 / m³
  ─────────────────────────────────────────────
  (no conversion costs at INC)
  ═════════════════════════════════════════════════
  = GM II = GM I                        $60 / m³
  ─────────────────────────────────────────────
  - Sales rep accruals                              → SALES
  - Marketing accruals                              → MKT
  - Mgmt fees (reinvoiced to Europe)                 → CORP (reallocated to BNV at group level)
  - Royalties                                        → CORP
  - Freight / warehousing                           → SC
  - Corporate overhead                              → CORP
  ═════════════════════════════════════════════════
  = EBITDA
```

The COGS-D / COGS-I split for the **group consolidated P&L** is reconstructable from BNV's analytics — no need to re-decompose at INC level.

### EOM Allocation Journal Entry (Unabsorbed Costs)

```
Example: Operations payroll unabsorbed = €10,000

  Dr  500000 (COGS-FG)          €10,000
      Analytic: Country=COM, BU=Operations, CM=COGS-I
  Cr  620000 (Payroll clearing)  €10,000
      Analytic: BU=Operations

Then distribute COM → actual countries by m³ share:

  Country allocation (based on m³ sold in month):
    USA:   60% of m³  →  €6,000
    NOR:   25% of m³  →  €2,500
    DEU:   15% of m³  →  €1,500
```

---

## 8. Entity-Specific Scope

Not all features apply to all entities. The table below clarifies what is **common** (all entities) vs **US-only** vs **Europe-only**.

| Feature | Europe (BNV / Holding) | US (INC) | Notes |
|---|---|---|---|
| **Country analytics** | ✅ 75 values | ✅ USA, CAN | All revenue + COGS tagged |
| **BU analytics** | ✅ Shared 9 BUs | ✅ Shared 9 BUs | |
| **CM Level analytics** | ✅ | ✅ | P&L waterfall — same structure both entities |
| **Sales Area analytics** | ❌ | ✅ 9 regions | Contact-level field, US/CAN only |
| **COGS BoM decomposition** (GM I vs GM II) | ✅ Production entity | ❌ Not needed — 100% COGS-D | INC has no conversion; group split comes from BNV |
| **EOM Accruals** (marketing, royalties, mgmt fees, sales rep) | ❌ | ✅ US only | Existing engine in `kebony_accounting_hub.py` |
| **Production cost absorption** (WC rates → MO) | ✅ Kallo plant | ❌ Distribution only | Manufacturing in Belgium |
| **Unabsorbed cost allocation** | ✅ Production overhead | Minimal (no factory) | Belgium allocates factory overhead |
| **Country distribution of production costs** | ✅ COM → countries by m³ | ❌ N/A for INC | INC buys from BNV at transfer price |
| **Intercompany margin tracking** | ✅ IC sale to INC | ✅ IC purchase from BNV | Consolidated margin = BNV margin + INC margin |

### Why CM Level is Needed in Both Entities

Even though INC is a distribution entity (no factory), the P&L waterfall still applies:

- **INC GM I**: Revenue − COGS (purchase price from BNV, FIFO) — all COGS is COGS-D
- **INC GM II**: = GM I (no conversion costs at INC, so COGS-I = 0)
- **INC EBITDA**: GM II − Sales costs − Marketing accruals − Mgmt fees − Royalties − Freight − Warehousing − Corporate overhead
- **INC Net Income**: EBITDA − D&A − Financial

The CM Level plan allows INC to report the same P&L cascade as BNV, enabling group-level consolidation.

---

## 9. End-of-Month Allocation Workflow

```
┌──────────────────────────────────────────────────┐
│              MONTH-END CLOSE                      │
├──────────────────────────────────────────────────┤
│                                                   │
│  Prerequisites:                                   │
│  1. All invoices posted                           │
│  2. All production MOs completed (BNV only)       │
│  3. All vendor bills posted                       │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  STEP A: Run EOM Accruals  ★ US ONLY ★   │   │
│  │  Marketing, Royalties, Mgmt Fees,         │   │
│  │  Sales Rep                                 │   │
│  │  (existing: kebony_accounting_hub.py)      │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  STEP B: Compute Unabsorbed Costs (BNV)   │   │
│  │  For each BU:                              │   │
│  │    Actual cost - Absorbed via WC rates     │   │
│  │    = Unabsorbed remainder                  │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  STEP C: Allocate to CM Levels (ALL)      │   │
│  │  Unabsorbed production → COGS-I (BNV)     │   │
│  │  Sales overhead → SALES                    │   │
│  │  Marketing overhead → MKT                  │   │
│  │  Corporate overhead → CORP                 │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  STEP D: Distribute Country (BNV)         │   │
│  │  Costs tagged COM (no country) →           │   │
│  │  distribute across countries               │   │
│  │  proportional to m³ sold (always m³)       │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  STEP E: Validate & Post (ALL)            │   │
│  │  Review allocation journal entries         │   │
│  │  Post when approved                        │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 10. Interaction with Existing Features

| Existing Feature | Entity | Interaction with Analytics |
|---|---|---|
| **COGS recompute** (`account_move.py`) | US | Must carry analytical distribution (Country, Sales Area, BU, CM) when writing COGS amount |
| **EOM Accruals** (`kebony_accounting_hub.py`) | US | Accrual JE lines must carry CM level: MKT for marketing, SALES for sales rep, CORP for mgmt fees, CORP for royalties |
| **Biewer PO** (consignment) | US | Vendor bill inherits analytics from customer invoice that triggered it |
| **Pack reservation** | All | No direct impact on analytics |
| **Multi-ledger (VVF)** | All | Alternative ledger adjustments should also carry full analytic distribution |
| **Production MO** (future Phase 6) | BNV | MO completion posts WIP→FG with BU=Operations, CM=COGS-D (materials) + COGS-I (conversion) |

---

## 11. GL Account → CM Level Mapping

Every GL account that appears on a journal entry line must map to exactly one CM Level. This is the core of the P&L waterfall.

### Europe (BNV / Holding) — Production + Sales Entity

| GL Account Range | Description | CM Level | Auto-post? |
|---|---|---|---|
| 700xxx | Revenue — product sales | REV | ✅ At invoice creation |
| 700xxx | Revenue — intercompany sales to INC | REV | ✅ At IC invoice |
| 600xxx | Raw wood consumption (FIFO) | COGS-D | ✅ At MO completion (BoM materials) |
| 601xxx | Chemicals (ready-mix) | COGS-D | ✅ At MO completion (BoM materials) |
| 602xxx | Packaging materials | COGS-D | ✅ At MO completion (BoM materials) |
| WC absorption (stacking, autoclave, dryer) | Conversion cost absorbed via WC rates | COGS-I | ✅ At MO completion (BoM operations) |
| 61xxxx | Freight in / outbound / 3PL | SC | Manual or journal default |
| 62xxxx | Payroll — sales teams | SALES | Via BU (50/52) → CM rule |
| 62xxxx | Payroll — marketing | MKT | Via BU (60) → CM rule |
| 62xxxx | Payroll — operations (unabsorbed) | COGS-I | EOM allocation |
| 62xxxx | Payroll — finance, IT, leadership | CORP | Via BU (10/15) → CM rule |
| 62xxxx | Payroll — R&D, quality, lab | RD | Via BU (70) → CM rule |
| 63xxxx | D&A | DA | Journal default |
| 65xxxx | Financial charges, FX | FIN | Journal default |

> **TODO**: Validate exact BNV account ranges with Belgium accounting team. The table above uses indicative European ranges.

### US (INC) — Distribution Entity

INC is a pure distribution entity. **All COGS = COGS-D** (no conversion, no BoM decomposition needed). The direct/indirect split for consolidated reporting comes from BNV's analytics.

| GL Account | Description | CM Level | Auto-post? |
|---|---|---|---|
| 400000 | Revenue — product sales | REV | ✅ At invoice creation |
| 500000 | COGS — finished goods (FIFO purchase from BNV) | COGS-D (100%) | ✅ At delivery (stock journal default) |
| 580150 | Marketing accrual expense | MKT | ✅ At EOM accrual posting |
| 580250 | Sales rep accrual expense | SALES | ✅ At EOM accrual posting |
| 580350 | Management fees accrual expense | CORP | ✅ At EOM accrual posting |
| 580450 | Royalties accrual expense | CORP | ✅ At EOM accrual posting |
| 215510-215570 | Accrual liabilities (B/S) | N/A (balance sheet) | — |
| 110200 | FIFO inventory valuation (B/S) | N/A (balance sheet) | — |
| 110410 | Landed cost clearing (B/S) | N/A (balance sheet) | — |
| Freight accounts | Outbound freight, 3PL | SC | Manual or journal default |
| Warehousing accounts | Storage, handling | SC | Manual or journal default |
| D&A accounts | Depreciation & amortisation | DA | Journal default |
| Financial accounts | Interest, FX | FIN | Journal default |

---

## 12. Auto-Posting Rules (Comprehensive)

The goal is to **maximise automatic assignment** of analytics at transaction time, minimising manual intervention and EOM reclass.

### Rule 1: Country — From Customer / Supplier Address

| Transaction | Source | Method |
|---|---|---|
| Customer invoice (revenue lines) | `partner_shipping_id.country_id` on invoice (or `partner_id.country_id` fallback) | Override `_prepare_invoice_line_values()` or `action_post()` hook |
| COGS journal entry (stock → COGS on delivery) | Inherit from linked `sale.order.partner_shipping_id.country_id` | Override stock valuation `_create_account_move_line()` or post-process |
| Vendor bill (direct purchase) | `partner_id.country_id` on vendor | Override on vendor bill post, or manual |
| IC sale BNV → INC | Country = **USA** (decided). Canada gap fine-tuned at EOM by reallocating BNV IC margin proportional to INC m³ by country | Auto from IC partner address |
| Production MO (materials, WC) | NOT assigned — country-agnostic | EOM allocation (Step D) |
| Payroll / overhead | NOT assigned at transaction time | EOM allocation or journal default |

### Rule 2: Sales Area — From Contact (US Only)

| Transaction | Source | Method |
|---|---|---|
| Sales order | `partner_id.x_kebony_sales_area` (contact field) | Auto-set on SO creation |
| Customer invoice | Inherited from SO, or from `partner_id.x_kebony_sales_area` | Propagated via SO→Invoice flow |
| Invoice lines | Inherited from invoice header | Standard Odoo behaviour if analytic set on header |
| COGS journal entry | Inherited from linked SO / invoice | Same hook as Country |
| EOM Accrual JE (US) | Inherited from invoice line's analytic distribution | Already grouped by analytic in `action_run_eom_accruals()` |

### Rule 3: BU — From Sales Team / Department

| Transaction | Source | Method |
|---|---|---|
| Revenue (customer invoice) | Sales team on SO/invoice → BU mapping | Default analytic on `crm.team` or override |
| COGS | Operations (30) — hardcoded | Default on stock journal or override |
| Payroll | Employee department → BU mapping | HR analytic rule or journal default |
| Marketing accruals (US) | Market (60) | Set in `action_run_eom_accruals()` |
| Sales rep accruals (US) | Sales team BU (50 or 52) | Set in `action_run_eom_accruals()` |
| Vendor bills (freight, services) | BU based on expense type | Manual or purchase journal default |

### Rule 4: CM Level — From GL Account / BoM

| Transaction | Source | Method |
|---|---|---|
| Revenue lines | Always REV | Automatic — any revenue account → CM=REV |
| COGS — BNV (finished goods) | BoM decomposition → COGS-D + COGS-I | ⭐ BoM-based split at COGS posting (BNV only) |
| COGS — INC (all products) | COGS-D (100% direct) | INC is distribution — no conversion costs |
| COGS — accessories / non-BoM | COGS-D (100% direct) | No conversion cost for traded goods |
| EOM Accrual — Marketing | MKT | Set in accrual engine |
| EOM Accrual — Sales Rep | SALES | Set in accrual engine |
| EOM Accrual — Mgmt Fees | CORP | Set in accrual engine |
| EOM Accrual — Royalties | CORP | Set in accrual engine |
| Freight / logistics | SC | Journal default or manual |
| Payroll (by BU) | Derived from BU → CM mapping (see below) | EOM allocation |
| D&A | DA | Journal default |
| Financial | FIN | Journal default |

### BU → CM Level Default Mapping

When overhead costs are posted to a BU but not yet tagged with a CM Level, the following default mapping applies at EOM allocation:

| BU | Default CM Level |
|---|---|
| 10 — Leadership | CORP |
| 15 — Finance / IT | CORP |
| 20 — Logistics / Warehouse | SC |
| 21 — Planning / Customer Service | SC |
| 30 — Operations | COGS-I (unabsorbed production overhead) |
| 50 — Sales Scandinavia | SALES |
| 52 — Sales International | SALES |
| 60 — Market (Marketing) | MKT |
| 70 — R&D / Quality | RD |

---

## 13. Odoo 19 Implementation Notes

### Native Capabilities

- Odoo 19 supports **multiple analytic plans** natively
- Each plan contains analytic accounts (the dimension values)
- Journal entry lines carry `analytic_distribution` (JSON dict mapping analytic account IDs to percentages)
- A single line can distribute across multiple plans simultaneously
- Native pivot reporting and budget comparison available

### Data Setup (No Custom Code)

1. Create 4 analytic plans: **Country**, **BU**, **Sales Area** (US only), **CM Level**
2. Create analytic accounts for each value in each plan
3. Configure default analytics on partners, sales teams, and journals where possible
4. Sales Area plan restricted to Kebony Inc. (or simply left unused in European entities)
5. Set up default analytic accounts on stock journals (BU=Operations, CM=COGS-D or COGS-I)
6. Add `x_kebony_sales_area` field on `res.partner` (Many2one to Sales Area analytic account)

### What Needs Custom Code

| Need | Approach | Priority |
|---|---|---|
| Auto-assign Country from customer address | Override invoice line preparation — set Country from shipping address | P1 |
| Auto-assign Sales Area (US only) | Propagate from `res.partner.x_kebony_sales_area` through SO → Invoice → Lines | P1 |
| Inherit Country + Sales Area on COGS | Override stock valuation JE creation — inherit from originating SO/invoice | P1 |
| BoM-based COGS split (COGS-D vs COGS-I) — BNV only | At COGS posting, compute direct/indirect ratio from product's BoM standard cost. INC = 100% COGS-D (no split) | P2 |
| Auto-assign BU from sales team | Default analytic on `crm.team` or journal-level defaults | P2 |
| CM Level on EOM Accruals | Update `action_run_eom_accruals()` to tag lines with MKT/SALES/CORP | P2 |
| EOM unabsorbed cost allocation wizard | New wizard on Accounting Hub (BNV) | P3 |
| EOM country distribution wizard | New wizard on Accounting Hub (BNV) | P3 |

---

## 14. Decisions & Design Still To Be Made

### ⭐ Key Decisions

- [ ] **COGS BoM decomposition (BNV only)** — Confirm BoM-based split as the approach for BNV. INC = 100% COGS-D (decided — no split needed for distribution entity). Fallback for BNV products without a BoM? Use 100% COGS-D for accessories/traded goods?
- [x] **IC transaction country** — ✅ **DECIDED: Country = USA**. When BNV sells to INC, BNV tags the IC sale as Country=USA. INC side: USA or CAN from end customer. **Canada gap**: BNV's IC margin is 100% under USA even if INC resells to Canada. Fine-tuned at EOM by reallocating BNV IC margin proportional to INC's m³ by country.
- [x] **Country distribution key** — ✅ **DECIDED: always m³ sold**. All country-based allocations (production costs, unabsorbed overhead, IC margin reallocation) use m³ as the distribution key.
- [ ] **Production MOs and country** — Should MO completion carry a Country analytic? (MOs don't know the customer.) Current design: tag COM, distribute at EOM.
- [ ] **Mgmt fees & royalties CM Level** — Currently mapped to CORP. Should they get their own CM Level codes? Or stay under CORP as sub-detail via GL account?
- [ ] **Mgmt fees intercompany reallocation** — INC pays management fees to Europe (Holding/BNV). This is an IC reinvoice that reduces INC's margin (CM Level = CORP in INC). In the **consolidated group P&L**, mgmt fees must be normatively reallocated to Europe — they are a European cost funded by INC. Mechanism TBD: (a) IC elimination at consolidation, (b) EOM reclass journal, (c) multi-ledger adjustment in VVF.

### Mapping Validation Needed

- [ ] **BNV chart of accounts** — Get exact GL account ranges from Belgium accounting team. The §11 Europe mapping uses indicative ranges — need validation.
- [ ] **BNV current allocation practice** — Document how BNV currently allocates overhead and production costs (pre-Odoo). Decide what to keep vs improve.
- [ ] **INC freight / warehousing accounts** — Confirm exact GL codes for Supply Chain costs (SC level). Currently not coded.

### Auto-Posting Completeness

- [ ] **Vendor bill analytics** — Should vendor bills auto-assign Country from supplier address? Or only for specific purchase types (freight, services)?
- [ ] **Payroll analytics** — Can HR analytic rules auto-assign BU from employee department? Or is payroll always posted manually with BU?
- [ ] **EOM accrual enhancement** — Current `action_run_eom_accruals()` groups by analytic account but does not set CM Level. Must be enhanced to tag MKT / SALES / CORP on accrual JE lines.
- [ ] **BoM ratio cache** — Should the direct/indirect ratio be pre-computed and stored on `product.template` (for speed), or computed on-the-fly at COGS posting?

---

## 15. Implementation TODO

Priority items to enable margin-per-country and P&L waterfall reporting:

| # | Task | Entity | Priority | Dependencies |
|---|---|---|---|---|
| 1 | **Data seeding**: create 4 plans + all analytic account values | All | P0 | None |
| 2 | **Add `x_kebony_sales_area`** on `res.partner` | INC | P0 | Plan 1 done |
| 3 | **Auto-post Country on revenue lines** | All | P1 | Plan 1 done |
| 4 | **Auto-post Sales Area on revenue lines (US)** | INC | P1 | Tasks 1-2 |
| 5 | **Auto-post Country + Sales Area on COGS lines** | All / INC | P1 | Tasks 3-4 |
| 6 | **Auto-post CM Level = REV on revenue** | All | P1 | Plan 1 done |
| 7 | **Auto-post CM Level on EOM accruals** (MKT, SALES, CORP) | INC | P2 | Plan 1 done |
| 8 | **BoM-based COGS decomposition** (COGS-D vs COGS-I) — BNV only | BNV | P2 | BoMs validated |
| 9 | **BU auto-assignment** from sales team + journal defaults | All | P2 | BU plan done |
| 10 | **EOM unabsorbed cost allocation wizard** | BNV | P3 | Tasks 1-9 |
| 11 | **EOM country distribution wizard** | BNV | P3 | Task 10 |
