# US Accounting & Margin Architecture

**Scope**: Kebony Inc. (US entity) — Odoo 19
**Module**: `kebony_bol_report`
**Entity filter**: `x_kebony_entity_type == 'inc'`

> This document covers US-specific accounting features: FIFO valuation,
> accrual engine, margin/commission calculation, landed costs, and
> month-end close. It does NOT cover wood metrics or physical units
> (see [[Metrics & Physical Units]]) or consignment
> (see [[Consignment & Biewer]]).

---

## 1. Executive Summary

End-to-end accounting architecture, valuation model, journal flows, and
Odoo configuration for Kebony Inc., a lumber distribution company
operating under US GAAP and IFRS with FIFO inventory valuation and real
landed cost capitalisation.

The architecture supports:

- Accurate FIFO-based inventory valuation
- Integrated landed cost allocation
- Revenue-based accrual accounting (marketing, sales commissions,
  management fees, royalties, rebates, returns)
- Automated perpetual inventory posting
- Audit-ready journal mappings
- Consistent treatment of inventory adjustments (NRV, downgrade,
  slow-moving)
- Robust month-end close procedures

---

## 2. Important Terminology

### "Margin" in this document

The **margin** referred to throughout this module is the **US-specific
margin for commission calculation purposes**. It is NOT the official
Kebony margin definition.

The official Kebony margin is defined by **Contribution Margin (CM)
levels** and will be implemented in a future phase using:

- 4 analytical plans: **Country**, **BU** (cost centre / department P&L),
  **Sales Area** (US only), and **CM Level**
- Automatic allocation rules on journal entries to assign costs to
  country, sales area, BU, and CM level
- BoM-based decomposition to split COGS into direct (GM I) vs indirect (GM II)
- See [[Analytical Accounting Architecture]] for the full white paper

### US Margin Formula (current implementation)

```
Net Sales    = Revenue + Down Payments
Margin       = Net Sales - COGS - Accruals - Freight - Warehousing - Other Adj.
Margin %     = Margin / Net Sales
```

> [!info] 2026-03-23 Change
> Credit notes are **no longer included** in the margin formula.
> Previously: `Net Sales = Revenue + Down Payments - Credit Notes`.
> Credit notes and debit notes now appear as **separate line items** in
> the invoice list view (see §7.2) with their own `amount_untaxed`.
> This avoids cutoff problems where a CN posted in a different period
> would distort the margin of the original invoice.

**Down Payment handling**: When a final invoice is issued after a
prepayment, Odoo adds a negative deduction line reducing `amount_untaxed`.
The margin formula adds back the down payment revenue by tracing the
invoice → SO → sibling prepayment invoices (see §7.1).

**Prepayment invoices**: No margin is computed for invoices flagged
`x_is_prepayment = True`. The margin button is hidden on these documents.

This drives commission calculations for sales representatives.

---

## 3. Chart of Accounts Architecture

The Chart of Accounts supports FIFO valuation, in-transit/impairment
accounts, landed cost clearing, GRNI, sales-based accruals, and NRV
allowances.

### Key Inventory Accounts

| Code   | Description                    |
|--------|--------------------------------|
| 110200 | FIFO Valuation                 |
| 211100 | Bills to Receive (GRNI)        |
| 110410 | Landed Cost Clearing           |
| 110101-110105 | Lumber FG & impairment  |

### Accrual Liabilities (2155xx)

| Code   | Description              |
|--------|--------------------------|
| 215510 | Marketing Accrual        |
| 215520 | Sales Rep Accrual        |
| 215530 | Management Fees Accrual  |
| 215540 | Royalties Accrual        |
| 215550 | Return Accrual           |
| 215560 | Freight Accrual          |
| 215570 | Rebates Accrual          |

### Accrual Expenses (58xxxx)

Each accrual type has paired accounts:

| Type            | Accrual Expense | Actual Expense |
|-----------------|-----------------|----------------|
| Marketing       | 580110          | 580150         |
| Sales Rep       | 580210          | 580250         |
| Management Fees | 580310          | 580350         |
| Royalties       | 580410          | 580450         |
| Returns         | 580510          | -              |
| Rebates         | 580610          | -              |

---

## 4. Inventory Valuation Method — Decision Framework

### The Goal

**Profitability by product, not by product group** — without requiring manual drill-down into individual Manufacturing Orders.

Today, Kebony uses Standard Cost with a Product Group analytic (KSP, KRRS, KR). This gives profitability at the product group level. To understand the margin on a specific product (e.g., KRRS 1" vs KRRS 2"), the controller must open each MO, reconstruct actual vs standard cost, and manually allocate variances. This is unsustainable.

### Three Options

| Criterion | Standard Cost | FIFO | Weighted Average |
|---|---|---|---|
| **Per-product profitability** | **NO** — only by product group. Per-product requires MO-level drill-down and manual variance allocation | **YES** — automatic, per lot | **YES** — automatic, per SKU |
| **Variance allocation needed** | Yes — monthly, by product group, proportional to m³. Complex, error-prone | No — actual cost flows through | No — actual cost flows through |
| **Cross-market fairness** | Fair — same standard cost everywhere | Unfair — lot-dependent cost means same product shows different margins depending on which batch shipped | Better — same SKU = same avg cost in a period |
| **Cost smoothness** | Perfectly smooth (it's a budget) | Volatile — reflects real batch variability | Smoothed — blends receipts into running average |
| **Balance sheet accuracy** | Drifts between standard revisions | Always reflects actual historical cost | Approximately actual (blended) |
| **Auditor / GAAP preference** | Acceptable (with variance treatment) | Preferred for batch-tracked manufacturing | Acceptable |
| **Lot cost traceability** | Lost — all FG at same standard | Preserved — each lot has its own cost | Destroyed — averaged across all on-hand |
| **EOM close complexity** | High — 4 variance accounts to allocate | Low — no permanent variance accounts (RDK settles to actual) | Low — no variance |
| **Standards to maintain** | ~200 products × 4 components, revised quarterly | WC rates + RDK only | None |
| **Odoo 19 native support** | Yes | Yes (most mature path) | Yes |

### The Key Argument

```
Standard Cost gives you:    Profitability by PRODUCT GROUP    (automatic)
                            Profitability by PRODUCT           → requires opening every MO

FIFO gives you:             Profitability by PRODUCT           (automatic, per lot)
                            BUT: lot-to-lot variability makes cross-market comparison noisy

Weighted Average gives you: Profitability by PRODUCT           (automatic, per SKU)
                            Smoother than FIFO — same product = same cost within a period
                            BUT: loses lot-level traceability
```

### Trade-off: FIFO vs Weighted Average

| | FIFO | Weighted Average |
|---|---|---|
| **Margin by product** | Yes — per lot (volatile) | Yes — per SKU (smooth) |
| **CFO / auditor happy** | Yes — real cost, traceable, GAAP/IFRS preferred | Yes — acceptable, but less precise |
| **CEO / commercial happy** | Risk of unfair comparison: "why is my margin lower?" because of batch cost, not pricing | Better: same product = same cost, fairer comparison across markets |
| **Lot traceability** | Full — each lot carries its actual cost through to COGS | Lost — receipt cost is blended into running average |
| **Large price swing impact** | Contained to specific lots | Immediately shifts average for ALL on-hand stock |

### The Three Methods — What They Really Mean

Before choosing, understand what each method gives you and what it costs:

| | Standard Cost | FIFO (Lot-Based Real Cost) | Weighted Average |
|---|---|---|---|
| **What you know per invoice** | Budget number (same for every lot) | Real cost of the specific lot shipped | Blended average across all lots on hand |
| **Per-product profitability** | **NO** — only by product group. Per-product requires opening every MO and manually allocating variances | **YES** — automatic, per lot | **YES** — automatic, per SKU |
| **Lot traceability** | Lost — all FG at same standard | **Preserved** — each lot carries its actual cost from production through to COGS | **Destroyed** — receipt cost blended into running average, can never be reconstructed |
| **Reconciliation & audit** | Requires 4 variance accounts + monthly allocation. Auditor must trust your standard is close to reality | **Self-reconciling** — GL = reality. No permanent variance accounts (RDK settles back to inventory/COGS). Auditor's preferred method | No variance accounts. But averaged values are "approximately right" — never exactly traceable |
| **Cross-market fairness** | Fair — same standard everywhere | Potentially noisy at single-invoice level — same product may show different cost depending on which batch shipped | Fair — same product = same cost within a period |
| **When cost errors hide** | Always — standard masks reality until quarterly revision | Never — every lot is individually visible. Problems surface immediately | Sometimes — a big price swing shifts the average for ALL stock, including lots that were bought cheaply |
| **What the CEO sees** | Smooth (it's a budget number) | Volatile at invoice level, but **self-corrects at monthly+ level** (see below) | Smooth |
| **EOM close effort** | High — 4 variance accounts to allocate, standards to maintain | **Low** — no variance (except RDK) | Lowest |
| **Odoo 19 readiness** | Supported | **Most mature path** (lot_valuated) | Supported |

> **The punchline:** Standard cost gives you a budget that hides reality. Weighted average gives you a smooth number that destroys traceability. FIFO gives you the truth — and from truth, you can always compute any smoothed view you want. You cannot go the other way.

### Recommendation: Option B+ — FIFO + Quarterly SKU Margin Averaging

**Core principle**: You can always smooth truth. You cannot un-smooth an average.

Option B+ is not a compromise — it's the best of both worlds:

```
THE BOOKS (Layer 1 — Statutory GL)
  → FIFO: actual lot cost flows to COGS
  → Every invoice shows the real margin for the lot shipped
  → Full traceability: lot → MO → cost breakdown
  → Auditor-grade, IAS 2 gold standard
  → CFO, auditor, and controller work here

THE VIEW (Layer 2 — Reporting Query)
  → For each SKU, for each quarter:
      Average margin = Σ(revenue − COGS) / Σ(qty sold)
  → Same product shows same average margin across all markets
  → No lot-to-lot noise
  → No journal entries — it's a SQL query / pivot report
  → CEO, sales team, commercial team work here
```

**Why this works — and why it's simple:**

The "smoothing layer" is not a separate ledger, not a set of journal entries, not an EOM process. It is a **report that averages the FIFO margins per SKU per quarter**. The data is already in the GL — you just aggregate it differently.

| Question | Answer |
|---|---|
| Does it require journal entries? | **No** — pure reporting layer |
| Does it require a management ledger? | **No** — unless the CEO wants a full smoothed P&L (Phase 3, unlikely) |
| Does it touch the statutory books? | **No** — the GL stays at FIFO |
| How hard is it to build? | **Trivial** — a computed column in the margin report or a pivot view |
| When does it become available? | **As soon as you have 1 quarter of FIFO data** |

**Why not Weighted Average in the GL instead?**

| | WA in GL | Option B+ (FIFO in GL + averaged report) |
|---|---|---|
| Statutory books | Averaged (less precise) | Actual FIFO (maximum truth) |
| Per-lot traceability | Lost forever | Preserved — always available |
| Cross-market fairness | Built-in (same avg cost) | Available via quarterly SKU averaging |
| Auditor preference | Acceptable | Preferred |
| Flexibility | Locked into one view | Both views available simultaneously |
| Reversibility | Cannot reconstruct FIFO from WA | Can always compute WA from FIFO |
| Reconciliation | Cannot trace COGS to a specific lot | Every COGS line traces back to a specific lot and its producing MO |

#### Phase 3 (On Demand): Management Ledger

Only if the CEO needs a **complete smoothed P&L and balance sheet** (not just a margin report), the VVF multi-ledger framework can produce one:

```
For each SKU sold in the period:
  FIFO COGS (actual)     = sum of actual lot costs delivered
  WA COGS (target)       = qty sold × weighted average cost of that SKU
  Delta                   = WA COGS − FIFO COGS

Management ledger JE (exists ONLY in Management ledger):
  DR/CR  600 COGS                delta
  CR/DR  399 Smoothing reserve   delta  (BS account, management only)
```

The smoothing reserve nets to zero over time — it shifts cost between periods but doesn't create or destroy cost. This is available but **probably unnecessary** — the quarterly SKU margin report gives the CEO everything they need.

#### Recommended Phasing

| Phase | What | When |
|---|---|---|
| **Go-live** | FIFO as system of record. No smoothing needed yet. | July 1, 2026 |
| **Q4 2026** | Report layer: quarterly SKU-averaged margin column in margin report. Trivial — just a GROUP BY on existing FIFO data. | After first full quarter of data |
| **On demand** | Management ledger (VVF multi-ledger): full smoothed P&L. Only if CEO explicitly needs a separate set of books. | Unlikely to be needed |

#### Clarification: "FIFO" Means Lot-Based Real Cost with FIFO Reservation

A common misconception is that "FIFO valuation" implies costs flow in strict
first-in-first-out order through COGS. In practice, Kebony operates under
**lot-based specific identification** — FIFO only governs the *default
reservation order*, not the *cost assigned to a transaction*.

**What actually happens:**

| Step | System proposes (FIFO) | Operations may override | Cost that flows |
|---|---|---|---|
| **MO consumption** | Oldest lot reserved first | Operator picks whichever lot suits the process (dimensions, drying state, proximity) | **Actual cost of the lot consumed** — not the oldest lot's cost |
| **Sales delivery** | Oldest lot reserved on pick | Warehouse ships whichever lot is operationally practical (location, customer spec, logistics) | **Actual cost of the lot shipped** — not the oldest lot's cost |

**Why this is not a problem — it's a feature:**

1. **Full traceability** — every COGS entry traces to a specific lot with a
   specific cost. No averaging, no abstraction. The GL is maximally truthful.

2. **Operational discipline** — FIFO as the default reservation strategy
   forces visibility on slow movers. When an operator overrides FIFO, they
   make a *conscious decision* to skip older stock. This creates a natural
   discipline: old stock cannot hide. The system keeps proposing it until
   someone deals with it (consumes it, downgrades it, or writes it off).

3. **Valuation integrity** — whether the operator takes the oldest or newest
   lot, the cost recorded is always the *real cost of what was actually used*.
   This is **specific identification** under IAS 2.23-25 — the gold standard
   for items that are not ordinarily interchangeable or are segregated for
   specific projects. Lumber lots with different production batches, grades,
   and landed costs qualify.

**In accounting terms:**

| Term | What it means at Kebony |
|---|---|
| **FIFO (Odoo product category setting)** | Default reservation order: propose oldest lot first |
| **Actual cost flow** | Specific identification — real lot cost flows to WIP / COGS |
| **Valuation layer** | One `stock.valuation.layer` per lot, carrying that lot's actual cost |

> **Key takeaway**: Kebony's "FIFO" is best described as **lot-based real-cost
> valuation with FIFO as the default reservation discipline**. The reservation
> order is a suggestion; the valuation is always fact. This gives both
> operational flexibility and accounting precision — the best of both worlds.

> **IAS 2 reference**: IAS 2.23 allows specific identification for items that
> are not ordinarily interchangeable. IAS 2.25 states that FIFO (or weighted
> average) is used when specific identification is not appropriate. Kebony's
> lot-tracked lumber qualifies for specific identification; FIFO is the
> *reservation heuristic*, not the *cost formula*.

---

#### Why FIFO Self-Corrects: The Natural Averaging Effect

The concern about lot-to-lot margin variability is valid for a **single transaction** — but irrelevant at any meaningful reporting level. FIFO naturally converges to weighted average as transaction volume increases:

| Reporting horizon | Transactions per SKU | FIFO vs WA margin gap | Practical impact |
|---|---|---|---|
| **Single invoice** | 1 lot | Can be significant (lot-dependent) | Visible but meaningless in isolation |
| **Weekly** | 5–10 deliveries | Noise reduces rapidly | Barely noticeable |
| **Monthly** | 20–50 deliveries per SKU | Converges to WA | Negligible |
| **Quarterly** | 60–150 deliveries | Virtually identical to WA | None |
| **Annual** | 200+ deliveries | Mathematically identical | Zero |

**Why?** Every "expensive" lot shipped to one market is balanced by a "cheap" lot shipped to another. Over any reasonable period, the FIFO COGS per product converges to the weighted average of all lots produced — because you're selling many lots, not one.

The only scenario where FIFO creates persistent distortion is if a product has **very few transactions per period** (e.g., a specialty product sold once a quarter). For Kebony's core SKUs with dozens of monthly shipments, FIFO and WA produce the same margin at monthly level.

> **Key message for CEO**: A single invoice may show lot-specific cost — but nobody makes business decisions on a single invoice. At any meaningful level (product/month, product/quarter, market/year), FIFO averages itself out naturally. You get the truth AND the smoothness — without sacrificing traceability. The smoothing layer is a safety net, but you'll probably never need it.

---

## 5. Accounting Schema Change: Napoleonic → Anglo-Saxon

### Context

The CFO is challenging the current "Napoleonic" (continental) accounting model and proposes switching to the "Anglo-Saxon" (full absorption) model. This is a **prerequisite** for the FIFO or Weighted Average valuation to deliver per-product profitability — it determines **what costs enter inventory** in the first place.

### Legal Basis (Belgian Statutory)

Belgian GAAP (KB/AR 30 January 2001, art. 3:15 KB WVV) provides an **accounting policy choice**:

- The manufacturing cost (*vervaardigingsprijs*) **may include** indirect production overheads — Anglo-Saxon / full absorption (IAS 2 compliant)
- Companies are also **free to exclude** them — Napoleonic / continental (current practice)
- **Both are legal**. The choice must be disclosed in the notes (valuation rules section)
- IFRS (IAS 2) **requires** full absorption — switching **aligns** statutory with IFRS

Sources: [CBN/CNC](https://www.cbn-cnc.be/nl/adviezen/boeking-en-waardering-van-voorraden), [KB 30/01/2001](https://www.cbn-cnc.be/nl/node/1144), [PwC BE GAAP comparison](https://www.pwc.be/en/FY21/documents/similarities-and-differences-a-comparison-of-ifrs-us-gaap-and-belgian-gaap.pdf)

### Step-by-Step Comparison: Before vs After

Using the same PO-019357 example (KRRS 50×150mm, Feb 2026) from the slide deck.

#### Step 1: Raw Material Reception

| | Napoleonic (AX today) | Anglo-Saxon (Odoo target) |
|---|---|---|
| Journal | DR 300 Matières premières (1400--R--2490) | DR 300 Matières premières |
| | CR 444 Factures à recevoir (GRNI) | CR 444 Factures à recevoir (GRNI) |
| Valuation | FIFO purchase price per lot | FIFO purchase price per lot |
| **Change** | **IDENTICAL** — no change | |

#### Step 2: MO Consumption — Raw Materials

| | Napoleonic (AX today) | Anglo-Saxon (Odoo target) |
|---|---|---|
| Journal | DR 320 En-cours WIP (1492) | DR 320 En-cours WIP |
| | CR 300 Matières premières – Bois blanc | CR 300 Matières premières – Bois blanc |
| | CR 301 Matières premières – Chimie (1400--MIX) | CR 301 Matières premières – Chimie |
| Cost basis | FIFO actual | FIFO actual |
| **Change** | **IDENTICAL** — no change | |

#### Step 3: Conversion Costs — THE KEY DIFFERENCE

| | Napoleonic (AX today) | Anglo-Saxon (Odoo target) |
|---|---|---|
| What happens | Conversion costs posted to **WIP-IC (320bis)** then flushed directly to **P&L (604)** at PO close. Costs are **expensed immediately**. | Conversion costs **absorbed into WIP (320)** via WC rates. Costs **stay on balance sheet** until goods are sold. |
| Personnel (ICP) | DR 320bis WIP-IC (1493) / CR P&L (4501--ICP--1290) → then at close: DR 604 Écart / CR 320bis | DR 320 En-cours WIP / CR **791 Production costs absorbed** |
| Other indirect (IC) | DR 320bis WIP-IC (1493) / CR P&L (4501--IC--1292) → then at close: DR 604 Écart / CR 320bis | DR 320 En-cours WIP / CR **791 Production costs absorbed** |
| Electricity (DC) | DR 320bis WIP-IC / CR P&L (4961--DC--4025) → then at close: DR 604 Écart / CR 320bis | DR 320 En-cours WIP / CR **791 Production costs absorbed** |
| **Where cost sits** | **P&L** (expensed as incurred) | **Balance Sheet** (in WIP, then FG) |
| **When it hits P&L** | **Immediately** at production | **Only when goods are sold** (via COGS) |
| New account needed | — | **791 Production costs absorbed** (WC contra-account) |

#### Step 4: MO Completion — FG Capitalisation

| | Napoleonic (AX today) | Anglo-Saxon (Odoo target) |
|---|---|---|
| Journal | DR 330 Produits finis (1440) at **STANDARD** | DR 330 Produits finis at **ACTUAL** (FIFO) or **WA** |
| | CR 714 Variation des stocks (4227) | CR 320 En-cours WIP |
| Variance | DR/CR 604 Écart de production (actual − standard) | **No variance** (FIFO: actual flows through. WA: actual updates average) |
| FG cost contains | Standard cost (budget) — conversion was already expensed to P&L | **Full actual cost**: materials (FIFO) + conversion (absorbed WC rates) |
| **Change** | FG = budget number | FG = real production cost |

#### Step 5: Sale Delivery — COGS

| | Napoleonic (AX today) | Anglo-Saxon (Odoo target) |
|---|---|---|
| Journal | DR 600 Coût des ventes (COGS) at **STANDARD** | DR 600 Coût des ventes (COGS) at **ACTUAL** |
| | CR 330 Produits finis | CR 330 Produits finis |
| COGS includes | Standard FG cost (materials + conversion at budget rates) | **Full actual cost** (materials at FIFO + conversion absorbed) |
| Conversion in COGS | **NO** — it was already expensed in Step 3 | **YES** — it flows through inventory and exits as COGS |
| **Change** | COGS = budget | COGS = reality |

### Summary: What Moves from P&L to Balance Sheet

```
NAPOLEONIC (today)                    ANGLO-SAXON (proposed)
==================                    =====================

Production month:                     Production month:
  Materials → BS (WIP/FG)               Materials → BS (WIP/FG)
  Conversion → P&L (immediately)        Conversion → BS (WIP/FG)  ← THE CHANGE
  FG = standard cost on BS              FG = full actual cost on BS

Sale month:                           Sale month:
  COGS = standard (materials only)      COGS = full actual (mat + conv)
  Conversion already in P&L             Conversion exits BS via COGS

Net P&L effect over life:             Net P&L effect over life:
  IDENTICAL                             IDENTICAL
  (same total cost hits P&L)            (same total cost hits P&L)

But TIMING is different:              Costs hit P&L LATER
  Costs hit P&L EARLIER                 (deferred until sale)
  (conversion expensed at production)
```

### Impact Assessment

#### 1. Auditor Impact

| Aspect | Impact |
|---|---|
| **IFRS alignment** | Positive — Anglo-Saxon = IAS 2 requirement. Fewer consolidation adjustments |
| **Inventory scrutiny** | Higher — auditor will verify WC rates are based on normal capacity (IAS 2.13) |
| **Abnormal costs** | Must be identified and expensed (idle plant, abnormal waste per IAS 2.16) |
| **Disclosure** | Change in accounting policy must be disclosed in notes. If material, prior year comparatives may need restatement (IAS 8) or at minimum pro forma disclosure |
| **Overall** | Auditor will **welcome** the change — it's the IFRS-preferred approach |

#### 2. Tax Impact

| Aspect | Impact |
|---|---|
| **Short-term** | Higher taxable profit — conversion costs deferred to BS instead of expensed. Inventory value increases, fewer immediate deductions |
| **Long-term** | Neutral — same total costs over the product lifecycle |
| **Magnitude** | Per [ZEW research](https://ftp.zew.de/pub/zew-docs/dp/dp0538.pdf): IFRS-style treatment broadens Belgian tax base by 3.8–14.6% depending on sector |
| **Action** | Discuss with tax advisor before implementation |

#### 3. Implementation Impact

| Aspect | Impact |
|---|---|
| **New account** | 791 Production costs absorbed (WC contra-account) — MUST be created |
| **Removed accounts** | 320bis (WIP-IC) no longer needed — absorbed into 320 |
| | 330bis (FG offset) already dropped |
| | 604 Écart de production scope reduced (RDK machining settles back to inventory/COGS — no permanent variance) |
| | 714 Variation des stocks no longer needed (no standard revaluation) |
| **WC rate setup** | Required — 3 work centres (Stacking, Autoclave, Dryer) with €/hour rates based on normal capacity budget |
| **Odoo config** | Product categories set to FIFO or WA (not Standard). Automated valuation. WC costs absorbed at MO completion |
| **Simplification** | Fewer variance accounts, no two-phase posting, no standard maintenance |

#### 4. Mid-Year Transition Impact (AX → Odoo at July 1)

| Aspect | Recommendation |
|---|---|
| **Cutoff** | July 1 = clean transition date. All MOs completed before July 1 stay under Napoleonic (in AX). All MOs completed after July 1 use Anglo-Saxon (in Odoo) |
| **Opening inventory** | FG migrated from AX at **AX standard cost** (Napoleonic basis). This is the opening balance in Odoo. No restatement of existing stock needed |
| **New production** | All MOs created in Odoo accumulate full cost (materials + WC absorption). FG from July 1 onward = full actual cost |
| **Mixed inventory** | During H2 2026, inventory contains both: old FG (at AX standard, no conversion) and new FG (at full actual, with conversion). FIFO naturally sells old stock first — the transition effect washes out as pre-July stock depletes |
| **P&L impact H2** | P&L looks **artificially better** in H2 vs H1 because conversion costs are now deferred to BS (capitalised) instead of expensed immediately. This is not real — it's a timing shift. Must be explained in management reporting |
| **Year-end disclosure** | Notes must disclose: (a) change in accounting policy, (b) transition date July 1, (c) estimated impact on inventory value and profit, (d) reason for change |
| **No H1 restatement** | Do NOT restate H1 2026 numbers. Apply prospectively from July 1. Defensible audit position: change coincides with ERP migration |

### Chart of Accounts Changes

| Account | Napoleonic (AX) | Anglo-Saxon (Odoo) | Change |
|---|---|---|---|
| **300** Matières premières – Bois | ✅ | ✅ | No change |
| **301** Matières premières – Chimie | ✅ | ✅ | No change |
| **302** Ready-Mix | ✅ | ✅ | No change |
| **320** En-cours (WIP) | Materials only | **Materials + Conversion** | Scope expanded |
| **320bis** En-cours indirect (WIP-IC) | Conversion costs transit | **REMOVED** — merged into 320 | Simplified |
| **322** En-cours machinage (WIP-Mach) | ✅ | ✅ | No change |
| **325** Semi-produits finis | Standard cost | **Actual cost** (FIFO/WA) | Valuation change |
| **330** Produits finis | Standard cost | **Actual cost** (FIFO/WA) | Valuation change |
| **330bis** PF offset | Two-phase support | **REMOVED** | Simplified |
| **360** Emballages | ✅ | ✅ | No change |
| **444** GRNI | ✅ | ✅ | No change |
| **600** COGS | Standard cost | **Actual cost** | Valuation change |
| **604** Écart de production | 4 variance types | **1 only** (RDK machining) | Simplified |
| **714** Variation des stocks | Standard revaluation | **REMOVED** | Not needed |
| **791** Production costs absorbed | Does not exist | **NEW** — WC contra-account | New account |

### Decision — Confirmed (SteerCo 23 March 2026)

> **DECIDED**: Anglo-Saxon full absorption + FIFO (Option B+) confirmed at SteerCo on 23 March 2026. Reporting layer (quarterly SKU margin averaging) to be added if needed.

This was **not optional** — per-product profitability requires Anglo-Saxon full absorption. Standard cost under Napoleonic accounting gives only product-group-level margin.

```
Napoleonic + Standard  = Product Group profitability only (legacy AX)
Anglo-Saxon + FIFO     = Per-product profitability, per lot ← DECIDED
```

---

## 6. Inventory Valuation — Current Implementation (FIFO)

FIFO valuation generates real cost layers:

1. At **goods receipt** -> Odoo creates a valuation layer based on the PO
   price
2. At **delivery** -> Odoo consumes the oldest layers and posts COGS
3. **Landed costs** enrich existing layers
4. **Adjustments** (NRV, downgrade) reduce inventory value immediately

### Why FIFO for Lumber

- Lumber batches have real cost variability
- Quality grades impact cost non-uniformly
- FIFO preserves gross margin integrity
- Price variability makes standard cost inappropriate

### Financial Statement Implications

- Balance sheet reflects real historical costs
- COGS reflects true material flow
- Gross margin is not distorted by costing estimates

---

## 7. Landed Cost Framework

Landed costs include freight, duties, handling, and inbound processing.

### Two-Step Accounting Model

**Step 1 - Vendor bill:**
```
DR 110410  Landed Cost Clearing
    CR 211000  Accounts Payable
```

**Step 2 - Allocation:**
```
DR 110200  FIFO Valuation
    CR 110410  Landed Cost Clearing
```

### Capitalisation Rules (GAAP/IFRS)

| Capitalisable              | NOT Capitalisable        |
|----------------------------|--------------------------|
| Freight-in                 | Warehousing fees         |
| Customs, duties            | Storage                  |
| Inbound handling/processing| Outbound freight         |

---

## 8. Accrual Engine

### Two-Phase Architecture

**Phase 1: Line-Level Computation** (`account_move_line.py`)

Accrual amounts are computed and stored **per invoice line** as Studio fields.
This happens either:
- Automatically when the margin button is clicked (`_kebony_apply_accrual_vals(force=True)`)
- Could be triggered at invoice posting (not currently implemented)

**Phase 2: EOM Journal Entry** (`kebony_accounting_hub.py`)

At end-of-month, a button on the Accounting Hub collects all un-accrued lines
and posts a single journal entry with debit/credit pairs grouped by analytic account.

### Accrual Types & Default Rates

| Type            | Wood  | Accessory | Condition              |
|-----------------|-------|-----------|------------------------|
| Marketing       | 4%    | 1.5%      | Distributors only (`x_studio_customer_catagory` = "Distributor") |
| Royalties       | 5%    | **0%**    | Wood only — not consignment. Accessories excluded. |
| Management Fees | 14%   | **5%**    | Not consignment        |
| Sales Rep       | variable | variable | From `x_studio_sales_rep_commission` on the invoice header (prefilled from rep's `x_studio_sales_rep_rate` — see Sales Rep section below) |

> **Change log (Feb 2026):** Royalties reduced from 5% → 0% for
> accessories. Management fees reduced from 14% → 5% for accessories.
> Wood rates unchanged.

### Per-Transaction Rate Overrides (Mar 2026)

Default rates are stored as fields on the invoice header (`account.move`).
Users can adjust them per invoice before clicking "Recompute Margin":

**Current rates (defaults)** — every rate below is a *field* on the invoice.
The first time the invoice is saved, these defaults are applied; the user can
then override any of them per transaction before the "Run EoM Accruals" step.

| Component | Default rate | Base | Scope | Override field (`account.move`) |
|---|---|---|---|---|
| Marketing — Wood | **4.0%** | `price_subtotal` × volume-dependent base | Distributors only | `x_kebony_rate_marketing_wood` |
| Marketing — Accessory | **1.5%** | `price_subtotal` × volume-dependent base | Distributors only | `x_kebony_rate_marketing_accessory` |
| Royalties (wood only) | **5.0%** | `price_subtotal` | Wood products, all customers | `x_kebony_rate_royalty` |
| Management Fees — Wood | **14.0%** | `price_subtotal` | All customers (non-consignment) | `x_kebony_rate_mgmt_fees_wood` |
| Management Fees — Accessory | **5.0%** | `price_subtotal` | All customers (non-consignment) | `x_kebony_rate_mgmt_fees_accessory` |
| Sales Rep Commission | *variable per rep* | `price_subtotal` | Rep-assigned invoices | `x_studio_sales_rep_commission` (header) — prefilled from rep's default, editable per invoice |
| Freight | manual amount | — | Header level | `x_studio_freight_cost` |
| Warehousing | manual amount | — | Header level | `x_studio_warehousing_cost` |
| Other Costs | manual amount | — | Header level | `x_studio_other_costs` |

These fields are visible in the **Other Info** tab under "Accrual Overrides →
Rate Overrides" (US-only, invoices and credit notes). Displayed as percentages.

### Rate source of truth — Accounting Hub (Apr 2026)

All accrual rate **defaults** live on `kebony.accounting.hub` (Accounting Hub → **Accrual Rates** tab):

| Field on Hub | Default | Used for |
|---|---|---|
| `rate_marketing_wood` | 4.0% | Marketing accrual on wood products (Distributor customers) |
| `rate_marketing_accessory` | 1.5% | Marketing accrual on accessories (Distributor customers) |
| `rate_marketing_central` | **2.5%** | Central portion of marketing, split off before the remainder goes to the distributor fund |
| `rate_royalty_wood` | 5.0% | Royalty on wood products (all customers, excluded for consignment) |
| `rate_mgmt_fees_wood` | 14.0% | Management fees on wood products |
| `rate_mgmt_fees_accessory` | 5.0% | Management fees on accessories |

**Resolution cascade** (highest precedence wins):
1. Per-invoice override on the invoice header (`x_kebony_rate_*`) — for exceptional deals
2. Accounting Hub value — day-to-day default, CFO-editable
3. Hard-coded fallback — only hit if the hub record doesn't exist (fresh install)

**Why this matters** — before Apr 2026, rates were hardcoded in Python. Every rate change required a developer push. Now the CFO changes rates in the UI (Accrual Rates tab), new accruals pick them up immediately, no deployment needed. Existing already-accrued invoices are not retroactively recomputed — the change applies forward.

### Sales Rep & Commission Rate — Prefill and Override (Apr 2026)

The sales representative and the commission rate both live on the
**invoice header**, not hidden in fallbacks. Behaviour:

1. **On partner change** — `_onchange_partner_sales_area_and_rep` populates:
   - `x_studio_sales_representative` ← partner.commercial_partner_id.x_studio_sale_representative
   - `x_studio_sales_rep_commission` ← that rep's `x_studio_sales_rep_rate`
2. **On rep change (manual override)** — `_onchange_sales_representative_rate`
   refreshes the commission rate from the newly-selected rep's default.
3. **Explicit user overrides are respected**:
   - Clear the rep on the header → no sales-rep accrual is computed.
   - Type `0` in the rate field → `0` sales-rep accrual (explicit zero, honoured).
   - Type any non-zero rate → that value is used.

The accrual engine (`account_move_line._kebony_compute_accrual_vals`) reads
**only** the header fields. There is NO silent fallback to the partner or to
the rep's stored rate at compute time — prefill happens once, visibly, at
data-entry. *What you see on the invoice is what gets accrued.*

**Why this matters** — previously the engine silently fell back to
`partner.x_studio_sale_representative` when the header was empty, and to
`rep.x_studio_sales_rep_rate` when the header rate was 0. That produced
"ghost reps" on credit notes with zero commission (rate=0 on rep) and
made it impossible to set an explicit `0%` rate (Python truthy check
treated `0.0` as "not set" and fell through).

### Marketing split — Central vs Distributor Bucket

Marketing accruals are **automatically split into two sub-buckets** at EOM
posting time:

| Sub-bucket | Rate | GL Accounts | Analytics |
|---|---|---|---|
| **Marketing — Central (Kebony common pool)** | **2.5%** of base (default, configurable on Accounting Hub → `rate_marketing_central`) | DR **581000** / CR **215510** | Country + BU 60, **NO sales area**, **NO distributor** |
| **Marketing — Distributor (named partner fund)** | Total marketing − central | DR **581001** / CR **215511** | Country + BU 60 + Sales Area + **Distributor** |

**Apr 2026 change:** The two buckets now hit **separate GL accounts** (not just different analytics). The CFO can read the distributor-fund balance on 215511 independently of the Kebony central pool on 215510 without having to aggregate by analytic tag. Central rate also raised from 1% → 2.5% at the same release.

**Examples:**

| Invoice marketing rate | Central portion | Distributor portion |
|---|---|---|
| 4% (wood default) | 1% | 3% |
| 1.5% (accessory default) | 1% | 0.5% |
| 6% (user override) | 1% | 5% |
| 1% (user lowered) | 1% | 0% |
| 0% (marketing disabled) | 0% | 0% |

> **Why the split?** The Central bucket funds corporate/common marketing
> initiatives (brand, trade shows, catalogues) — not tied to a named
> distributor. The Distributor bucket is a **per-partner fund** that
> individual distributors draw from for co-op marketing. The 1% is the
> portion Kebony keeps regardless of rate overrides.

> **The Central rate (1%) is hardcoded** — it does NOT move when the user
> overrides the total marketing rate on the invoice. Only the Distributor
> portion flexes.

### Three-Step Lifecycle of an Accrual

Every accrual line moves through **three distinct states**. Understanding
this sequence is critical for users (CFO, accountant, controller):

```
┌──────────────────────┐    EOM button    ┌─────────────────────┐    Vendor bill     ┌─────────────────────┐
│ STEP 1               │ ───────────────> │ STEP 2              │ ────────────────>  │ STEP 3              │
│ Invoice-level FIELDS │                  │ Accrued (BS + P&L)  │                    │ Settled (reversed)  │
│ (informational only) │                  │ One JE per month    │                    │ Against vendor bill │
└──────────────────────┘                  └─────────────────────┘                    └─────────────────────┘
```

**Step 1 — Values live as fields on the invoice, NOT yet accruals**

When an invoice is saved (or "Recompute Margin" is clicked), the accrual
amounts are written to the invoice **as fields only**:

- Line-level: `x_studio_marketing_accrual_line_item`, `x_studio_royalities_1`,
  `x_studio_royalties_mngmt_fees_charge`, `x_studio_sales_rep_charge`
- Header-level: `x_studio_freight_cost`, `x_studio_warehousing_cost`,
  `x_studio_other_costs`

**No journal entry exists yet.** These fields feed the margin calculation
and are visible on the invoice, but the General Ledger has no provision.
Users can freely edit the rates, toggle accruals on/off, or change header
costs — nothing is committed to the GL.

> The margin button uses these fields to compute a preview margin. That
> margin is informational and can change until EOM runs.

**Step 2 — "Run EoM Accruals" moves values into real accruals**

Only when the user clicks **Accounting Hub → US Accounting → "Run EoM
Accruals (US)"** does the accrual engine:

1. Scan all posted invoice lines with `x_studio_is_accrued = False`
2. Group by `(year, month)` of invoice date
3. Post **one JE per invoice-month**, back-dated to the last day of that
   month, with paired DR/CR lines for every accrual type
4. Mark the lines as `x_studio_is_accrued = True` so they are not picked
   up again next run
5. Apply the 1% Central vs Distributor split on marketing
6. Attach analytics (Country, BU, Sales Area, Rep, Distributor) per type

**After Step 2**, the BS carries the provision (2155xx) and the P&L
carries the period cost (5xxxxx). The invoice fields are now immutable
for accrual purposes — editing them has no GL effect until a reset.

**Step 3 — Vendor bill must reverse the accrual**

When the actual vendor bill arrives (from the distributor for marketing
reimbursement, from the sales rep for commission, from a royalty payee,
etc.), the accountant must **reverse the provision** against the real bill:

1. Open **Accounting Hub → "Settle Accruals"**
2. Select accrual type (royalties / mngmtfees / marketing) and date range
3. Enter the vendor bill amount — the wizard computes weighted allocation
   across sales areas and caps reversals at the accrued amount
4. Post — DR 2155xx (release provision) / CR 5xxxxx (recognize actual expense).
   Excess (bill > accrued) goes straight to P&L; shortfall stays as residual provision.

The **Accrual Status Report** (next section) exposes every JE line so the
accountant can see:

- What was accrued (Step 2 entries, credit side)
- What has been settled so far (reversal entries, debit side)
- The residual open balance
- A direct link (`reversal_move_id`) from each accrual to the reversing JE

> **In short:** the fields at invoice level are a *forecast*; Step 2 makes
> them *real*; Step 3 is how they exit the balance sheet via the real invoice.

### Credit Note & Debit Note Behaviour (Mar 2026)

Credit notes (`out_refund`) receive special treatment to ensure accruals
are always computed, even when the line has no product or an unclassified
product:

1. **Lines without a product** — allowed on credit notes (invoices still
   require a product). A generic correction line like "Credit for order X"
   will still get accruals.
2. **Unclassified products** — when a credit note line has no wood/accessory
   classification, the system defaults to **wood rates** (royalty 5%, mgmt
   fees 14%, marketing 4% if distributor). This is safe because the vast
   majority of Kebony revenue is wood.
3. **Sign** — all accrual amounts are multiplied by -1, producing negative
   accruals that reverse the original invoice's provisions.

### Base Amount

`price_subtotal` (or `quantity * price_unit` as fallback). Always absolute value.

### Sign Convention

- `out_invoice`: positive accruals
- `out_refund`: negative accruals (sign = -1)

### GAAP/IFRS Justification (ASC 606 / IFRS 15)

Accruals are created **at the time of sale** because GAAP/IFRS requires
recognition of variable consideration when revenue is recognised. Companies must:

1. Estimate variable consideration (rebates, marketing contributions,
   returns, royalties)
2. Recognise it when revenue is recognised
3. Not wait for supplier invoices or actual events

This justifies booking provisions at sale time for: marketing contributions,
volume rebates, royalty costs, sales commissions, and returns reserve.

### Accrual Posting at Sale

```
DR 58xxxx  Accrual Expense        (analytic: sales area)
    CR 2155xx  Accrual Liability   (partner: customer or sales rep)
```

The liability line carries the **partner** (distributor or sales rep) to
enable fund tracking without creating a GL account per partner. The
expense line carries the **analytic distribution** (sales area) for P&L
per area reporting.

### Partner-Based Fund Tracking (Mar 2026)

#### Problem

Marketing accruals create a "fund" per distributor — the distributor earns
4% of their purchases as a marketing contribution they can claim by
submitting expense invoices. The US team needs to know how much each
distributor has available. Same logic applies to sales rep commissions.

Without per-partner tracking, the liability accounts (215510, 215520) show
a single aggregate balance — impossible to know Rex's balance vs Synergy's.

#### Solution: Partner on Accrual Journal Items

Every accrual liability line (`CR 2155xx`) is posted with the **partner**
field set to the specific distributor or sales rep:

| Accrual Type | Liability Account | Partner Set To |
|---|---|---|
| Marketing | 215510 | Invoice customer (the distributor) |
| Sales Rep | 215520 | The sales rep (`x_studio_sales_representative`) |
| Royalties | 215540 | Kebony Norway (intercompany — single partner) |
| Management Fees | 215530 | Kebony Holding (intercompany — single partner) |

#### Lifecycle of a Marketing Fund

**Step 1 — Accrual at sale** (automatic, EOM posting):
```
DR 580150  Marketing Expense      (analytic: sales area)
    CR 215510  Marketing Accrual  (partner: Rex Lumber)    $4,000
```
Rex now has $4,000 available in their fund.

**Step 2 — Distributor claims fund** (vendor bill from Rex):
```
DR 215510  Marketing Accrual      (partner: Rex Lumber)    $3,500
    CR 211000  Accounts Payable   (partner: Rex Lumber)
```
Rex's fund balance is now $500.

**Step 3a — Unused fund release** (US team decides to expire):
```
DR 215510  Marketing Accrual      (partner: Rex Lumber)    $500
    CR 780000  Provision Release
```
Rex's fund is now $0.

**Step 3b — Overspend** (Rex claims more than accrued):
```
DR 215510  Marketing Accrual      (partner: Rex Lumber)    $500
DR 580150  Marketing Expense      (additional)             $200
    CR 211000  Accounts Payable   (partner: Rex Lumber)    $700
```

#### How to Check a Distributor's Balance

**Partner Ledger** → filter on account 215510 + partner = Rex Lumber.
The balance shows exactly how much fund Rex has remaining.

No analytic tags needed. No GL accounts per customer. The standard Odoo
partner ledger report gives full visibility.

#### Sales Rep Commission — Same Pattern

```
DR 580250  Commission Expense     (analytic: sales area)
    CR 215520  Commission Accrual (partner: John Smith [sales rep])
```

When the rep's commission invoice arrives:
```
DR 215520  Commission Accrual     (partner: John Smith)
    CR 211000  Accounts Payable   (partner: John Smith)
```

Partner ledger on 215520 + partner = John Smith shows outstanding
commission balance.

#### Implementation Status (Mar 2026 — DONE)

- ✅ EOM accrual posting sets `partner_id` on each liability line
- ✅ Marketing accrual partner = invoice `partner_id` (the distributor)
- ✅ Sales rep accrual partner = invoice `x_studio_sales_representative`
- ✅ Freight accrual included in EOM engine (from `x_studio_freight_cost`)
- ✅ Sales area analytic on expense lines (from invoice header)
- ✅ Reset button for initial setup / re-run
- ✅ Per-transaction rate overrides (5 rate fields on invoice header)
- ✅ Credit note support (defaults to wood rates if no classification)
- ⏳ Royalties / mgmt fees partner currently = invoice customer. Future:
  set to intercompany partner (Kebony Norway / Kebony Holding).
- Fund balances do NOT expire automatically. The US team manually
  reverses expired funds via a journal entry.

### When the actual invoice arrives (legacy section — see above for partner-tracked version)

**If actual = provision:**
```
DR 2155xx  Accrual Liability    (partner: distributor/rep)
    CR 211000  Accounts Payable
```

**If actual > provision:**
```
DR 2155xx  Accrual Liability    (partner: distributor/rep)
DR 58xxxx  Additional Expense
    CR 211000  Accounts Payable
```

**If actual < provision (release unused):**
```
DR 2155xx  Accrual Liability    (partner: distributor/rep)
    CR 780000  Provision Release (Income)
```

### EOM GL Mapping — Balance Sheet & P&L Account Map

The accrual engine pairs each accrual type with one **Balance Sheet liability
account (2155xx)** and one **P&L expense account (5xxxxx)**. Both sides are
required on every JE — the BS side is the provision, the P&L side is the
period cost.

| Type | P&L Expense (DR) | Balance Sheet Liability (CR) | Partner on CR line |
|------|-------------|----------------|-------------------|
| Marketing | **581000** Marketing Expense | **215510** Marketing Accrual (BS) | Invoice customer (distributor) |
| Sales Rep | **588000** Sales Rep Expense | **215520** Sales Rep Accrual (BS) | Sales representative |
| Royalties | **584000** Royalties Expense | **215540** Royalties Accrual (BS) | Invoice customer |
| Mgmt Fees | **586000** Mgmt Fees Expense | **215530** Mgmt Fees Accrual (BS) | Invoice customer |
| Freight | **591000** Freight & Tariffs | **215560** Freight Accrual (BS) | Invoice customer |
| Warehousing | **592000** Warehousing Expense | **215590** Warehousing Accrual (BS) | Invoice customer |
| Other Costs | **599000** Other Management Costs | **215595** Other Costs Accrual (BS) | Invoice customer |

**Posting direction** (per JE line):

```
DR  5xxxxx  (P&L Expense)      — recognizes cost in the period
CR  2155xx  (BS Liability)     — books the provision
```

On settlement (actual vendor bill arrives), the direction reverses:

```
DR  2155xx  (BS Liability)     — releases the provision
CR  2110xx  (AP) / Bank        — pays / accrues the real invoice
```

> **Important:** The expense (DR) line carries the **sales area analytic**
> (from the invoice header `x_studio_area_of_sales`). The liability (CR)
> line carries the **partner** for fund tracking. This gives both P&L by
> territory AND per-partner fund balances.

> **Warehousing accrual** follows the same rate-based model as the other
> accruals once the rate is configured. Until the rate is set it remains
> manual (`x_studio_warehousing_cost` on invoice header, included in the
> margin formula but no JE generated).

> **Other Costs (215595)** covers miscellaneous management-driven accruals
> that do not fit the standard categories (royalties, mgmt fees, marketing).
> Typical usage: one-off management charges, group-level allocations, and
> other items the controller wants provisioned without a dedicated rate.

### Line-Level Fields (Studio)

| Field | Description |
|---|---|
| `x_studio_marketing_accrual_line_item` | Marketing accrual amount |
| `x_studio_royalities_1` | Royalties amount (typo intentional — Studio field) |
| `x_studio_royalties_mngmt_fees_charge` | Management fees amount |
| `x_studio_sales_rep_charge` | Sales rep commission amount |
| `x_studio_accrual_base_snapshot` | Base amount used for computation |
| `x_studio_is_accrued` | Boolean — True once EOM JE posted |

> **Note:** The "Recompute Margin" button computes accrual amounts on
> lines but does **NOT** set `x_studio_is_accrued`. Only the EOM engine
> sets this flag after posting the journal entry.

### Header-Level Fields

| Field | Description |
|---|---|
| `x_studio_freight_cost` | Freight cost (manual entry — carrier estimate) |
| `x_kebony_freight_accrued` | Boolean — True once freight accrual JE posted |

### EOM Posting Logic — Step by Step

**Location:** Accounting Hub → US Accounting → "Run EoM Accruals (US)"

The EOM engine performs these steps:

1. **Search** all posted invoice/credit note lines where
   `x_studio_is_accrued = False`
2. **For each line**, read the computed accrual amounts (marketing,
   royalties, mgmt fees, sales rep commission)
3. **Group** accrual amounts by type × sales area × partner:
   - Sales area = from invoice header (`x_studio_area_of_sales`)
   - Partner = invoice customer (marketing, royalties, mgmt fees) or
     sales rep (commissions)
4. **Collect freight** from invoice headers where
   `x_kebony_freight_accrued = False` and `x_studio_freight_cost > 0`
5. **Create one journal entry** with paired debit/credit lines per
   group (expense + liability)
6. **Post** the journal entry
7. **Mark** all processed lines as `x_studio_is_accrued = True` and
   freight invoices as `x_kebony_freight_accrued = True`

### Reset & Re-Run (Initial Setup / Correction)

If accrual flags need to be reset (e.g., after fixing rates or during
initial setup):

**Location:** Accounting Hub → US Accounting → "Reset Accrual Flags"

This button:
- Sets `x_studio_is_accrued = False` on all posted invoice lines
- Sets `x_kebony_freight_accrued = False` on all posted invoices
- Does NOT delete any previously posted accrual journal entries

After resetting, run "Run EoM Accruals (US)" again. The engine will
create a **new** accrual JE covering all invoices. If a previous accrual
JE was already posted, the accountant should **reverse it first** to
avoid double-posting.

> **Warning:** Only use Reset for initial setup or after fixing accrual
> logic. In normal operations, the EOM engine is incremental — it only
> picks up new, un-accrued invoices each month.

### Backfill of Historical Invoices (Jan 2026 → Go-Live)

All invoices posted since January 1, 2026 need accrual amounts computed
before the EOM engine can pick them up.

**Procedure:**

1. **Recompute margins** on all historical invoices — this populates the
   accrual amount fields on each line. Use the "Recompute Margin (US)"
   button on each invoice, or batch via a server action.
2. **Reset accrual flags** (Accounting Hub → "Reset Accrual Flags") —
   ensures all lines are marked as not-yet-accrued.
3. **Run EOM Accruals** (Accounting Hub → "Run EoM Accruals (US)") —
   creates a single catch-up JE covering all historical invoices.

### Monthly Grouping (2026-04-10)

**Update**: The EOM engine was rewritten to produce **one journal entry per invoice-month**, back-dated to the last day of that month. This replaces the previous "single catch-up JE" behavior.

**Behavior:**
- Pass 1: walk all un-accrued invoice lines and bucket them by `(invoice_date.year, invoice_date.month)`
- Pass 2: create one JE per month, with `date = last day of that month`, containing all accrual types (marketing, royalties, mgmt fees, salesrep, freight, warehousing)
- JE `ref` = `"EOM Accruals — YYYY-MM"` (e.g., `"EOM Accruals — 2026-03"`)
- Each JE line `name` includes the triggering invoice number and date:
  - Example: `"Marketing Accrual | INV/2026/0001 2026-04-05"`
  - When multiple invoices contribute: `"Marketing Accrual | INV/2026/0001 2026-04-05 [+3 more]"`

**Result**: Running EOM mid-month for 3 months of backlog produces **3 separate JEs**, each back-dated to its correct period end. No more manual splitting required.

### Country Analytic Tag (Bug Fix 2026-04-10)

Previously, the Country analytic plan was never being tagged on accrual JE lines. Root cause: `_find_country_analytic` searched the Country plan by `code = country.code` (ISO-2), but the Country analytic accounts use `name = ISO-3` and `code = full country name` (e.g., `name='USA'`, `code='United States of America (the)'`).

**Fix**: added a hardcoded **ISO-2 → ISO-3 map** (~75 countries covering Kebony's markets) in `kebony_accounting_hub.py`, and changed the lookup to `name = iso3`. Country tag is now correctly populated on all accrual JE lines.

Odoo 19 removed `res.country.code_alpha3` so the map must live in code. If Kebony adds a new country, the map must be extended.

### Invoice-Level Accrual Overrides

The invoice header (`account.move`) provides two layers of override, visible
in the **Other Info** tab under "Accrual Overrides" (US-only, invoices and
credit notes):

**Layer 1 — Enable/Disable toggles** (force individual accruals to zero):

| Field | Default | Effect when unchecked |
|---|---|---|
| `x_kebony_compute_marketing` | `True` | Marketing accrual forced to 0 on all lines |
| `x_kebony_compute_royalties` | `True` | Royalties forced to 0 on all lines |
| `x_kebony_compute_mgmt_fees` | `True` | Management fees forced to 0 on all lines |

**Layer 2 — Rate overrides** (adjust percentages per transaction):

| Field | Default | Description |
|---|---|---|
| `x_kebony_rate_marketing_wood` | 4% | Marketing rate for wood |
| `x_kebony_rate_marketing_accessory` | 1.5% | Marketing rate for accessories |
| `x_kebony_rate_royalty` | 5% | Royalty rate (wood only) |
| `x_kebony_rate_mgmt_fees_wood` | 14% | Mgmt fees for wood |
| `x_kebony_rate_mgmt_fees_accessory` | 5% | Mgmt fees for accessories |

Both layers are applied during `_kebony_apply_accrual_vals()`. The
enable/disable toggle takes precedence — if disabled, the rate is
irrelevant (accrual = 0).

> **Note:** Sales rep commission rate was already overridable via
> `x_studio_sales_rep_commission` on the invoice header.

**Typical use cases:**
- Disable royalties for a promotional shipment
- Adjust marketing rate for a specific deal (e.g., 6% instead of 4%)
- Credit note with a different rate than the original invoice

### Consignment Exception

Products in category `"Product in Consignment"`:
- **No royalties** (set to 0)
- **No management fees** (set to 0)
- Marketing and sales rep still apply if conditions met

### Accrual Status Report (2026-04-15)

**Location:** Accounting Hub → US Accounting → "Accrual Status Report"

SQL-view model `kebony.report.accrual.status` exposes every 2155xx line
(BS liability side) with its **expense account pairing inferred from the
liability code**. One row per JE line, drillable to the originating invoice.

**Columns exposed:**

| Column | Source | Purpose |
|---|---|---|
| `date` | `aml.date` | Posting date of the accrual JE line |
| `month` | `to_char(date, 'YYYY-MM')` | Period grouping key |
| `accrual_type` | CASE on `aa.code` (215510/520/530/540/560/590/**595**) | Seven types including Other Costs |
| `partner_id` | `aml.partner_id` | Customer / sales rep / distributor |
| `analytic_distribution` | `aml.analytic_distribution` | Country / BU / Sales Area / Rep / Distributor tags |
| `move_id` | `aml.move_id` | JE Reference — click to open the original entry |
| `label` | `aml.name` | Invoice-level detail (e.g. "Marketing Accrual \| INV/2026/0001 2026-04-05") |
| `reversal_move_id` | LATERAL JOIN on `account_move.reversed_entry_id` | Link to the settlement/reversal JE if one exists |
| `accrued` | `aml.credit` | Amount provisioned (CR on liability account) |
| `settled` | `aml.debit` | Amount released (DR on liability account) |
| `open_balance` | `credit − debit` | What's still accrued (pending settlement) |

**Views:**

- **Pivot** (primary): drills **Accrual Type → Partner → JE → Detail**,
  with `accrued`, `settled`, `open_balance` as measures. Period splits via
  the **Period** group-by in the search bar (grouped by `month`).
- **List** (drill-down): full column set including `month`, JE reference,
  analytic distribution, reversal JE.

**Search filters:**

- Per accrual type (Marketing, Sales Rep, Royalties, Mgmt Fees, Freight,
  Warehousing, **Other Costs**)
- **Open Balance** (default on) — hides fully settled rows
- Group by Accrual Type / Partner / Period

**ACL (Odoo 19 gotcha — fixed 2026-04-15):**

The `ir.actions.act_window` record for this report had been narrowed to
`base.group_system` (Administrator only) on the prod DB — likely via
Studio or Dev Mode — which blocked the CFO with an "Access Error". Fix:
`group_ids` now declared explicitly in XML as:

```xml
<field name="group_ids" eval="[
  (5, 0, 0),                              <!-- clear stale DB state -->
  (4, ref('group_bu_15_finance')),        <!-- CFO / finance team -->
  (4, ref('group_bu_10_management')),     <!-- exec read-only -->
  (4, ref('group_bu_admin')),
]"/>
```

**Lesson learned:** always declare `group_ids` explicitly on every
`ir.actions.act_window` record. DB-side edits (Studio / Dev Mode) persist
silently unless the XML enforces the canonical state on module upgrade.

### Settlement Wizard

**Location:** Accounting Hub → US Accounting → "Settle Accruals"

Transient wizard `kebony.accrual.settlement.wizard` — weighted reversal of
Royalties, Mgmt Fees, or Marketing accruals against an incoming vendor bill.

**Flow:**

1. Select `accrual_type` (royalties / mngmtfees / marketing)
2. Select date range — wizard queries the matching BS liability account
3. Enter the vendor bill amount (what the supplier actually invoiced)
4. Click **Load Balances** — wizard groups accrued amounts by sales area
   and computes proportional weights
5. Review / tweak the per-area allocation (optional)
6. Click **Create Settlement JE** — posts the reversal(s)

**Settlement JE logic:**

| Scenario | Per-area entry | Notes |
|---|---|---|
| Invoice = accrual | `DR 215540 / CR 584000` (royalties example) | Clean 1:1 release |
| Invoice < accrual | Reverse only up to actual | Remainder stays as provision (or released if period closed) |
| Invoice > accrual | Cap reversal at accrued; excess `DR 584000 / CR AP` direct to P&L | Excess booked as current-period expense |

**Account map** (same P&L/BS mapping as EOM posting, direction reversed):

| Accrual Type | BS (DR on settle) | P&L (CR on settle) |
|---|---|---|
| Royalties | 215540 | 584000 |
| Mgmt Fees | 215530 | 586000 |
| Marketing | 215510 | 581000 |

**Post-settlement traceability:**

- The new JE's `reversed_entry_id` (on the reversing header) points back
  to the original EOM accrual JE
- The Accrual Status Report's `reversal_move_id` column surfaces this link
- Drill: report row → original JE → reversal JE → vendor bill

---

## 9. Margin Recompute Button

### Purpose

Approximate margin stored directly on the invoice document. Informational
only - does not create journal entries. Can be changed after the invoice is
posted. Gives the sales/finance team a quick profitability view per invoice.

### Button Flow: `action_recompute_management_margin()`

```
1. _kebony_apply_accrual_vals(force=True)
   |-- For each invoice line: compute and write accrual fields

2. _recompute_total_accruals_from_lines()
   |-- Sum: marketing + royalties + mgmt fees + sales rep -> write header total

3. _compute_management_cogs_amount()
   |-- Per line, in priority order:
      a) Consignment -> stock.consignment.price table
      b) Dropship -> vendor bill allocation (pro-rata by PO qty)
      c) Stock -> lot cost (wood) or standard_price (accessories)

4. Compute margin = net_sales - cogs - accruals - freight - warehousing - other_adj

5. Write to header: x_studio_cogs, x_studio_margin, x_studio_margin_in_pourcentage, x_studio_credit_note
```

### COGS Sources (3 paths)

**Path 1: Consignment**
- Product category = `"Product in Consignment"`
- Cost from `stock.consignment.price` (active, matching product_id)
- Unit price x qty in product UoM

**Path 2: Dropship**
- Detected via `sale_line_ids.purchase_line_ids` (auto-generated PO lines)
- Cost from **posted vendor bills** linked to the PO line
- Total bill `amount_untaxed` (includes freight/services) allocated pro-rata by PO qty
- Currency conversion if vendor bill in different currency

**Path 3: Stock (default)**
- From done stock moves linked via `sale_line_ids.move_ids.move_line_ids`
- **Lot-tracked products (wood):** `lot.x_studio_unit_cost` (or `x_studio_cost` or `cost`) x `move_line.quantity`
- **Non-lot products (accessories):** fallback to `product.standard_price` x qty in product UoM
- Lot cost field priority: `x_studio_unit_cost` > `x_studio_cost` > `cost` > `product.standard_price`

### Credit Notes & Down Payments

> [!info] 2026-03-23 Change — Credit Notes Removed from Margin
> Credit notes are **no longer collected** during margin computation.
> They appear as separate rows in the invoice list view instead.
> The field `x_studio_credit_note` now contains **Down Payments only**
> and is relabelled "Pre-payment".

**Credit notes**: Displayed as **separate line items** in the invoice
list view (type `out_refund`). They show their own `amount_untaxed`
(negative) and are not aggregated into the parent invoice's margin.
Debit notes (`in_invoice` reversals) are also shown as separate rows.

**Down payments**: Detected by tracing back to the SO and finding
sibling invoices flagged `x_is_prepayment = True`. The method
`_compute_down_payment_amount()` sums `amount_untaxed` of all posted
prepayment invoices linked to the same sale order.

The value is stored in `x_studio_credit_note` (relabelled to
**"Pre-payment"**):
- Positive value = down payment revenue restored

**Prepayment skip**: Invoices with `x_is_prepayment = True` are
skipped entirely by the margin button — no COGS, no accruals, no
margin computed.

### Header Fields Written

| Field | Description |
|---|---|
| `x_studio_cogs` | Total COGS |
| `x_studio_total_accruals_cost` | Total accruals (sum from lines) |
| `x_studio_freight_cost` | Freight (user input, not overwritten) |
| `x_studio_warehousing_cost` | Warehousing (user input, not overwritten) |
| `x_studio_other_adjustment` | Other adjustments (user input, not overwritten) |
| `x_studio_margin` | Calculated margin |
| `x_studio_margin_in_pourcentage` | Margin % |
| `x_studio_credit_note` | Pre-payment (DP amount only; CN no longer included — see §7.2) |

### Known Constraints

- Margin is an **approximation** - it depends on available cost data at compute time
- Dropship COGS requires vendor bills to be posted; if pending, COGS = 0 for those lines
- Stock COGS depends on lot cost being populated; if missing, falls back to standard price
- The button can be clicked multiple times - it overwrites previous values

---

## 10. Journal Entry Map

| Transaction               | Debit          | Credit         |
|---------------------------|----------------|----------------|
| Goods Receipt             | 110200 FIFO    | 211100 GRNI    |
| Supplier Invoice          | 211100 GRNI    | 211000 AP      |
| Landed Cost Vendor Bill   | 110410 LC Clr  | 211000 AP      |
| Landed Cost Allocation    | 110200 FIFO    | 110410 LC Clr  |
| Sales Invoice             | 121000 AR      | 400000 Revenue + 253000 Tax |
| Delivery / COGS           | 500000 COGS    | 110200 FIFO    |
| Accrual at Sale           | 58xxxx Exp     | 2155xx Liab    |
| Accrual Utilisation       | 2155xx Liab    | 211000 AP      |
| Over-accrual Release      | 2155xx Liab    | 780000 Release |

---

## 11. Inventory Adjustments

| Adjustment         | Debit                      | Credit       |
|--------------------|----------------------------|--------------|
| NRV Adjustment     | 110105 NRV Adjustment      | 110200 FIFO  |
| Downgrade / Quality| 110104 Lumber Downgrade    | 110200 FIFO  |
| Slow-moving Allow. | 110103 Slow-moving Deprec. | 110200 FIFO  |

---

## 12. Accounts Payable & GRNI Flow

GRNI (Bills to Receive) ensures accurate cutoff when deliveries occur
before invoices.

**Month 1 (goods delivered, no invoice yet):**
```
DR 110200  Inventory
    CR 211100  GRNI
```

**Month 2 (invoice arrives):**
```
DR 211100  GRNI
    CR 211000  AP
```

This ensures inventory is correct, AP is correct, and there is no timing
distortion.

---

## 13. Odoo Configuration Blueprint

### Product Category

| Setting              | Value                |
|----------------------|----------------------|
| Cost Method          | FIFO                 |
| Inventory Valuation  | Automated            |
| Stock Input Account  | 211100 GRNI          |
| Stock Output Account | 500000 COGS          |
| Valuation Account    | 110200 FIFO Valuation|

### Landed Cost Product

| Setting        | Value            |
|----------------|------------------|
| Product Type   | Service          |
| Is Landed Cost | Yes              |
| Expense Account| 110410 LC Clearing|

### Stock Journal

| Setting | Value                          |
|---------|--------------------------------|
| Debit   | 110200 Inventory               |
| Credit  | 211100 GRNI or 500000 COGS     |

---

### Odoo 19 Implementation Parameters (Kebony BNV)

Validated 2026-04-20 on `kebonyprod-test-31051334` by running a full vertical slice: PO receipt → MO → FG capitalisation at actual FIFO cost → sale → customer invoice. Posts the doctrine-compliant JEs (SteerCo 23 March 2026 Option B — FIFO + Anglo-Saxon).

**Three critical Odoo 19 changes** — each one silently breaks valuation JEs if missed, with no error in the log. Document them so nobody re-discovers the hard way.

#### 1. Valuation accounts moved from `product.category` to `stock.location`

Pre-Odoo-19: valuation account was on product category (`property_stock_valuation_account_id`).
Odoo 19: the gate on `stock.move._should_create_account_move` requires:

```python
location_dest_id.valuation_account_id or location_id.valuation_account_id
```

Without an account on the location, **no JE posts** regardless of category config or the `anglo_saxon_accounting` flag. Category fields still exist and are consulted in some paths (still must be set for BNV context), but location is the primary gate.

**Required per-location mapping (Kebony BNV):**

| Location type | Account |
|---|---|
| Stock parent, Raw - Prime, Raw - B-Grade | 300 Raw Materials - Acquisition |
| WIP - Kebonisation, WIP - Clear, WIP - Ready-Mix | 320 Work in Progress - Acquisition |
| FG - Character, FG - Clear | 330 Finished Goods - Acquisition |
| Production (virtual, usage=production) | 320 WIP |

#### 2. Company-dependent property fields need BNV context on write

Fields stored per-company in Odoo 19:
- `property_cost_method`
- `property_valuation`
- `property_stock_valuation_account_id`
- `property_stock_account_production_cost_id`

Writing without `context={'company_id': <BNV>, 'allowed_company_ids': [<BNV>]}` lands on the default company and silently misses BNV. **Always verify by reading back in BNV context** — the read without context may return the default/US value, not the BNV value.

#### 3. `stock.valuation.layer` model removed

Odoo ≤18 tracked value via `stock.valuation.layer` records. In Odoo 19 that model **no longer exists**. Value is stored directly on `stock.move`:

| Field | Purpose |
|---|---|
| `value` | Monetary, FIFO-computed cost of the move |
| `is_valued` | Boolean — valuation complete |
| `remaining_value` | FIFO remaining value on the move |
| `value_computed_justification` | Text — human-readable calc explanation |
| `account_move_id` | Link to posted JE — `False` = no JE posted |

Reporting is surfaced via `stock_account.stock.valuation.report` (view-only, no JE impact).

#### Config checklist (applied to BNV on test)

| Where | Setting | Value |
|---|---|---|
| `res.company` (BNV) | `anglo_saxon_accounting` | `True` |
| `res.company` (BNV) | `account_stock_journal_id` | STJ Inventory Valuation journal |
| `stock.location` (each internal + production) | `valuation_account_id` | Per mapping above |
| `product.category` (in BNV context) | `property_cost_method` | `'fifo'` |
| `product.category` (in BNV context) | `property_valuation` | `'real_time'` |
| `product.category` (in BNV context) | `property_stock_valuation_account_id` | 300 / 320 / 330 per category |
| `product.category` (in BNV context) | `property_stock_account_production_cost_id` | 320 WIP (required for MO JEs) |

#### Validated JE output (after full config)

MO completion — full Anglo-Saxon absorption into FG balance sheet:

```
DR 330 Finished Goods - Acquisition Value   4020.03
CR 320 Work in Progress - Acquisition Value 4020.03
```

Customer invoice posting (SO S00105 → INV/2026/00001):

```
DR Customers AR                                1200.00
CR Sales of Goods in Belgium (revenue)         1200.00
```

#### Known polish items (non-blocking)

- **Raw-consumption JE self-offsets** (DR + CR on same account). Cause: `stock.move._get_account_move_line_vals` in Odoo 19 — under investigation. Doesn't affect the FG capitalisation JE, which is correct.
- **Delivery JE at 0 EUR when FIFO consumes pre-fix quant layers.** Old stock valued at 0 from before the config fix gets picked first. Self-clears as pre-fix stock depletes.
- **PO receipt JE self-offsets** — Vendor Partners virtual location has no `valuation_account_id`. Native Odoo 19 behaviour for virtual counterparties without a dedicated interim account.

---

## 14. Month-End Close Procedures

### Inventory
- Validate all receipts have invoices
- Validate landed cost clearing is zero
- Review NRV, downgrade, and slow-moving accounts
- Ensure LIFO reserve (if unused) is unchanged

### Accruals
- Reconcile each 2155xx liability
- Apply actual invoices
- Release over-accruals
- Book additional accruals if needed

### COGS
- Review negative stock
- Validate FIFO cost layers integrity

### AP
- GRNI review (old receipts without invoices)

### AR
- Review unapplied payments and credit notes

---

## 15. Future: CM-Level Margin (Not Yet Implemented)

The real Kebony margin definition is by **Contribution Margin levels**.
Full design: **[[Analytical Accounting Architecture]]**

Summary:

1. Add **4 analytical plans** in Odoo:
   - **Country** → margin by geography (75 values for Europe, USA + CAN for INC)
   - **BU** (Business Unit / cost centre) → P&L by department (9 shared values)
   - **Sales Area** → US/Canada sub-regional detail (9 regions, INC only)
   - **CM Level** → contribution margin tier in the P&L waterfall (GM I → GM II → EBITDA → EBIT → Net Income)

2. **Auto-post analytics** at transaction time: Country from customer address, Sales Area from contact field (US), BU from sales team, CM Level from GL account / BoM decomposition

3. **BoM-based COGS decomposition** (preferred): split COGS into direct (COGS-D → GM I) and indirect (COGS-I → GM II) using the product's BoM cost structure

4. **EOM allocation**: unabsorbed production overhead (BNV), country distribution of costs tagged COM, CM-level tagging on accrual JE lines (US)

5. CM Level applies to **both** BNV and INC — enables group-level consolidated P&L

---

## Appendix A - Flow Diagrams

### FIFO Flow
```
Goods Receipt              Vendor Invoice           Delivery (COGS)
  DR 110200                  DR 211100                DR 500000
  CR 211100                  CR 211000                CR 110200
      |                          |                        |
      +-------------------------+------------------------+
```

### Landed Cost Flow
```
LC Vendor Bill             LC Allocation
  DR 110410                  DR 110200
  CR 211000                  CR 110410
      |                          |
      +--------------------------+
```

### Sales Accrual Flow
```
Accrual at Sale            Vendor Invoice Arrives
  DR 58xxxx                  DR 2155xx
  CR 2155xx                  CR 211000
      |                          |
      |                   +------+------+
      |                   |             |
      |            Actual > Accrual  Actual < Accrual
      |              DR 58xxxx        CR 780000
      +------------------------------------------
```

---

## Appendix B - Odoo Module Reference

| Feature                    | File(s)                        | US-only? |
|----------------------------|--------------------------------|----------|
| Margin recompute button    | `account_move.py`              | Yes      |
| Prepayment flag & cross-links | `account_move_prepayment.py` | Yes      |
| Accrual engine             | `account_move_line.py`         | Yes      |
| EOM accrual journal entry  | `kebony_accounting_hub.py`     | Yes      |
| Biewer PO generation       | `account_move_biewer_po.py`    | Yes      |
| US reports (BOL, Quote...) | `report/*.xml`                 | Yes      |
| Consignment pricing        | `stock_consignment_price.py`   | Yes      |
| Wood metrics layer         | `kebony_metrics_layer.py`      | No       |
| Pack reservation           | `stock_lot.py`, `sale_order.py`| No       |
| Logistics date             | `stock_picking.py`             | No       |
| Landed cost automation     | `stock_picking.py`, `account_move.py`, `purchase_order.py`, `stock_landed_cost.py` | Yes |
| Sales dashboard report     | `report_sales_dashboard.py`    | Yes      |
