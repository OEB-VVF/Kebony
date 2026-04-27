# Stock Locations & Warehouses

**Scope**: Belgian operations (BNV) — Odoo 19
**Module**: Core Odoo Inventory (`stock`)
**Entity filter**: `x_kebony_entity_type == 'bnv'` (primary), shared for `holding`
**Version**: 2.0 (2026-04-21) — Expanded topology (Reception, Shipping, Short Length, Kallo WIP/FG), added Quality Gate & Process, added Odoo 19 Valuation Account Mapping
**Supersedes**: v1.0 (basic Stock / B-Grade / Quarantine tree)

---

## 1. Overview

Kebony's Belgian operations span three physical sites, each modelled as
an **Odoo warehouse** (`stock.warehouse`). Within each warehouse, a
standardised set of **stock locations** (`stock.location`) captures both the
**physical staging area** (reception, shipping, production) and the
**quality state** (main, 2nd choice, quarantine, short length) of the inventory.

Quality state is encoded by location — moving stock between locations
*is* the quality decision. This gives a clean audit trail: you can
reconstruct a lot's entire journey (including all QC decisions) from its
stock-move history.

Each location carries a **`valuation_account_id`** (Odoo 19 requirement —
see §6) so that moves between locations post the correct journal entries.

---

## 2. Warehouse Topology

```
BNV (Kebony BNV)
  |
  +-- Kallo Plant          (WH: KALLO)  — Production site
  |     +-- KALLO/Reception              Incoming staging, pre-QC
  |     +-- KALLO/Stock                  Main A-grade (parent)
  |     |     +-- KALLO/Stock/Raw - Prime      A-grade raw lumber
  |     |     +-- KALLO/Stock/WIP - Kebonisation  In-process packs
  |     |     +-- KALLO/Stock/WIP - Clear          Post-kebo, pre-machining
  |     |     +-- KALLO/Stock/WIP - Ready-Mix      Chemical mix batch
  |     |     +-- KALLO/Stock/FG - Character       Finished KSP products
  |     |     +-- KALLO/Stock/FG - Clear           Finished KRRS / RDK returns
  |     +-- KALLO/Shipping               Outbound staging
  |     +-- KALLO/Quarantine             QC hold
  |     +-- KALLO/2nd Choice             B-grade (downgraded, sellable)
  |     +-- KALLO/Short Length           Off-cuts
  |     +-- KALLO/Production  (virtual, usage=production)  — MO handoff
  |
  +-- RDK                  (WH: RDK)  — External machining partner
  |     +-- RDK/Reception                Rough-sawn received from Kallo
  |     +-- RDK/Stock                    Machined FG awaiting shipment
  |     +-- RDK/Shipping                 Outbound staging
  |     +-- RDK/Quarantine               QC hold
  |     +-- RDK/2nd Choice               B-grade after machining
  |     +-- RDK/Short Length             Off-cuts from machining
  |
  +-- TabakNatie            (WH: TBK)  — 3PL reception
        +-- TBK/Reception                Supplier containers arrive here
        +-- TBK/Stock                    QC-passed raw lumber
        +-- TBK/Shipping                 Staged for transfer to Kallo
        +-- TBK/Quarantine               Failed inspection / held
        +-- TBK/2nd Choice               Downgraded raw (rare — usually scrapped at source)
        +-- TBK/Short Length             Damaged short pieces
```

All locations are **`usage='internal'`** (stock stays on BNV balance sheet),
except **`KALLO/Production`** which is **`usage='production'`** (virtual,
MO handoff point).

---

## 3. Warehouses

### 3.1 Kallo Plant (`KALLO`)

| Field | Value |
|---|---|
| **Short code** | `KALLO` |
| **Full name** | Kallo Plant |
| **Type** | Production site |
| **Company** | BNV |

**Role:** Primary manufacturing facility. All kebonisation occurs here
(stacking, autoclave, dryer, destacking). Finished goods may ship
directly from Kallo or transfer to RDK for machining.

### 3.2 RDK (`RDK`)

| Field | Value |
|---|---|
| **Short code** | `RDK` |
| **Full name** | RDK |
| **Type** | External machining partner |
| **Company** | BNV |

**Role:** External subcontractor for profiling, planing, and
cut-to-length operations. All Radiata Clear products route through RDK
after kebonisation. Some Scots Pine Character products may also require
cut-to-length at RDK. RDK also serves as the primary outbound shipping
point for European customers.

### 3.3 TabakNatie (`TBK`)

| Field | Value |
|---|---|
| **Short code** | `TBK` |
| **Full name** | TabakNatie |
| **Type** | External 3PL |
| **Company** | BNV |

**Role:** Third-party logistics partner handling inbound reception and
quality control. Raw materials from suppliers (New Zealand, Sweden)
arrive at TabakNatie for inspection and initial QC before transfer to
Kallo for production.

---

## 4. Location Types (Within Each Warehouse)

Each warehouse uses a standard set of location types — some mandatory for
every warehouse, some specific to the Kallo production site.

### 4.1 Standard Locations (all three warehouses)

| Location | Suffix | Usage | Purpose | Stock state |
|---|---|---|---|---|
| **Reception** | `/Reception` | internal | Inbound staging, awaiting QC | Not yet committed |
| **Main** | `/Stock` | internal | A-grade sellable / processable inventory | Available |
| **Shipping** | `/Shipping` | internal | Outbound staging, awaiting carrier | Reserved |
| **Quarantine** | `/Quarantine` | internal | Held pending quality decision | Not available for sale |
| **2nd Choice** | `/2nd Choice` | internal | Downgraded (a.k.a. B-grade) — same SKU, lower price | Available (discounted) |
| **Short Length** | `/Short Length` | internal | Off-cuts, damaged short pieces | Available (pricing per contract) |

#### 4.1.1 Reception

Goods received from a vendor or transferred in from another warehouse
land here **before** QC. They are:
- Not available for sale or production picks while in Reception
- Awaiting QC inspection (board-by-board or sample-based per product)
- Triaged to **Main** (A-grade pass), **2nd Choice** (B-grade), **Quarantine**
  (hold for further decision), or **Scrap** (reject)

#### 4.1.2 Main (`/Stock`)

Default location for goods that passed QC. Available for sale, production,
or transfer. This is Odoo's default `Stock` child of the warehouse.

#### 4.1.3 Shipping

Outbound staging. Picked goods from Main (or any other sub-location) land
here while awaiting carrier pickup. Visible in the delivery workflow.
Pre-dispatch QC happens here (final visual check).

#### 4.1.4 Quarantine

Held pending a quality or compliance decision:
- Not available for sale or production picks
- Products may return to Main (released), move to 2nd Choice (downgraded),
  Short Length (re-cut and reclassed), or Scrap (rejected)
- Covers: failed Reception QC, customer returns, production anomalies,
  regulatory hold (certifications under review)

#### 4.1.5 2nd Choice

Downgraded products — same SKU, lower commercial value. Kebony's "B-grade"
in trade parlance. Populated by:
- Board-by-board inspection at entry stacking or destacking
- QC decision out of Quarantine
- Customer returns deemed still sellable at a discount

**Accounting impact**: moving stock from Main to 2nd Choice triggers a
valuation write-down (per Odoo 19 FIFO valuation — see §6). Lot
traceability and **FSC / PEFC certification continuity** are preserved
(see [[Chain of Custody Architecture]]).

#### 4.1.6 Short Length

Off-cuts from production, cut-to-length operations, or damaged short
pieces recovered from Quarantine:
- Tracked by length-aware lot data
- Sold at negotiated prices (not standard pricelist)
- Counted separately for KPI reporting (recovery rate)

### 4.2 Kallo-Only Production Locations

The Kallo plant has additional sub-locations under `/Stock` to capture
the manufacturing state of wood. These are internal sub-locations (not
virtual) — stock is physically there, tracked by lot.

| Location | Purpose | Content type |
|---|---|---|
| `KALLO/Stock/Raw - Prime` | Raw lumber after Reception QC pass | Raw material |
| `KALLO/Stock/WIP - Kebonisation` | Packs queued for / running through autoclave + dryer | WIP |
| `KALLO/Stock/WIP - Clear` | Kebonised rough-sawn awaiting external machining (RDK) | WIP |
| `KALLO/Stock/WIP - Ready-Mix` | Chemical mix batch stock | WIP |
| `KALLO/Stock/FG - Character` | Finished KSP (Scots Pine) products | Finished goods |
| `KALLO/Stock/FG - Clear` | Finished KRRS (Radiata) + RDK-machined returns | Finished goods |

### 4.3 Virtual Production Location (Kallo only)

| Location | Usage | Purpose |
|---|---|---|
| `KALLO/Production` | `production` | MO consumption/output virtual handoff |

Used by Odoo `mrp.production` to model material consumption and finished-
goods output. Stock values pass through this location on MO completion
— it's the anchor for WIP capitalisation JEs (per Anglo-Saxon doctrine).

---

## 5. Quality Gate & Process

Kebony's QC discipline is encoded in stock locations. **Moving stock
between locations *is* the QC decision.** This gives Quality a clean
system-of-record: no parallel spreadsheets, no "forgotten" holds, and a
full audit trail per lot.

### 5.1 The Four Quality Gates

```
Gate 1: Reception QC       (entry from vendor / 3PL transfer)
Gate 2: Production QC      (at destacking, after dryer)
Gate 3: Pre-Dispatch QC    (at Shipping, before carrier pickup)
Gate 4: Claim / Return QC  (inbound from customer)
```

### 5.2 Gate 1 — Reception QC

**Location**: `/Reception` (all three warehouses)
**Owner**: Quality Manager / Warehouse team
**Trigger**: vendor delivery or inter-warehouse transfer arrives
**Inputs**: BOL, packing list, vendor certificate (FSC, phytosanitary)

**Decision tree**:
```
Reception
  |
  +-- Pass         --> /Stock (Main)         [A-grade]
  |
  +-- Minor defect --> /2nd Choice            [B-grade]
  |
  +-- Ambiguous    --> /Quarantine            [hold for decision]
  |
  +-- Reject       --> /Scrap + Supplier      [claim]
                        claim process
```

**Documentation required**:
- Signed Reception BOL (see [[Reception BOL & Inbound Logistics]])
- **Certification verification**: FSC and/or PEFC certificate reference per lot, captured on `stock.lot`. Suppliers certify at lot/batch level (not %); Kebony operates 100%-certified-per-lot in practice
- Photos of damage if claim is opened
- QC inspection report attached to the `stock.picking` chatter

### 5.3 Gate 2 — Production QC

**Location**: at destacking, after dryer — board-by-board inspection
**Owner**: Production Supervisor + QC Inspector
**Trigger**: MO completion, outputs moving from `Production` virtual
location to the FG sub-location

**Decision tree** (applied per pack):
```
Output from dryer
  |
  +-- A-grade visible defects <= spec  --> /Stock/FG - {Character|Clear}
  |
  +-- B-grade (minor knots, colour)    --> /2nd Choice
  |
  +-- Short pieces / cut-offs          --> /Short Length
  |
  +-- Failed spec (burn, crack)        --> /Scrap + production RCA
```

**Key rule**: scrap thresholds per family are defined on
`kebony.planning.family` (`scrap_b_grade_percent`, `scrap_internal_percent`).
Exceeding threshold triggers a quality alert → RCA + supplier escalation
if the raw material was the root cause.

### 5.4 Gate 3 — Pre-Dispatch QC

**Location**: `/Shipping`
**Owner**: Shipping team
**Trigger**: delivery order confirmed, stock picked to Shipping

**Checks**:
- Physical count vs. delivery order quantity
- Lot number / FSC certificate match per line
- Pack integrity (no broken strapping, no damage)
- Customer-specific requirements (labelling, orientation)

**Decision**:
- Pass → carrier loads, delivery validated
- Fail (damage discovered) → back to `/Quarantine` for RCA + re-pick
- Fail (wrong lot) → return to `/Stock` and correct the pick

### 5.5 Gate 4 — Claim / Return QC

**Location**: `/Quarantine` at the warehouse receiving the return
**Owner**: Commercial + Quality Manager
**Trigger**: customer return authorised (RMA)

**Decision tree**:
```
Return received at /Quarantine
  |
  +-- Fit for re-sale as A-grade  --> /Stock          [rare]
  |
  +-- Fit for re-sale as B-grade  --> /2nd Choice     [typical for cosmetic claims]
  |
  +-- Off-cut salvageable         --> /Short Length
  |
  +-- Scrap                       --> /Scrap + claim analytics
```

**Documentation required**:
- RMA reference
- Photos of returned material
- Root cause classification (cosmetic, structural, wrong product, transport damage)
- Link to the original delivery picking (full traceability)

### 5.6 Quality KPIs (feeds Accounting Hub / BI)

| KPI | Source | Cadence |
|---|---|---|
| Reception pass rate (A-grade %) | Gate 1 moves | Daily |
| Production B-grade % per family | Gate 2 moves | Per MO |
| Short-length recovery % | Gate 2 / Gate 4 moves | Weekly |
| Quarantine aging > 14 days | `stock.quant` on `/Quarantine` | Daily alert |
| Claims per 1000 m³ shipped | Gate 4 RMAs vs shipped volume | Monthly |
| Supplier quality index | Gate 1 fail rate per vendor | Quarterly |

### 5.7 Quality Manager Workflow (daily / weekly)

- **Daily**: review Reception QC log, clear any Quarantine blocking production
- **Weekly**: review B-grade % per family + RCA reports, supplier claim status
- **Monthly**: quality KPI review with Production + Commercial
- **Quarterly**: supplier quality index review, FSC audit prep

Document templates for QC inspection, RCA, and supplier claim live in
the Knowledge module under Quality.

---

## 6. Valuation Account Mapping (Odoo 19)

Each stock location carries a `valuation_account_id` that Odoo uses to
post stock-move journal entries. See [[Accounting & Margin Architecture]]
§13 "Odoo 19 Implementation Parameters" for the architectural background
(this is a breaking change from Odoo 18 where valuation was set on
`product.category`; now the location is the primary source).

### 6.1 Per-Location Mapping (BNV Chart of Accounts)

| Location | BNV Account | Code |
|---|---|---|
| `KALLO/Reception`, `KALLO/Stock`, `KALLO/Stock/Raw - Prime` | Raw Materials - Acquisition Value | 300 |
| `KALLO/Stock/WIP - Kebonisation`, `/WIP - Clear`, `/WIP - Ready-Mix` | Work in Progress - Acquisition Value | 320 |
| `KALLO/Stock/FG - Character`, `/FG - Clear` | Finished Goods - Acquisition Value | 330 |
| `KALLO/Production` (virtual) | Work in Progress - Acquisition Value | 320 |
| `KALLO/Shipping` (outbound FG) | Finished Goods - Acquisition Value | 330 |
| `KALLO/Quarantine`, `/2nd Choice`, `/Short Length` | Raw Materials - Acquisition Value | 300 |
| `RDK/Reception`, `/Stock`, `/Shipping`, `/Quarantine`, `/2nd Choice`, `/Short Length` | Finished Goods - Acquisition Value | 330 |
| `TBK/Reception`, `/Stock`, `/Shipping`, `/Quarantine`, `/2nd Choice`, `/Short Length` | Raw Materials - Acquisition Value | 300 |

**Rationale**:
- **TabakNatie** = 100% raw material (3PL for inbound only).
- **RDK** = 100% finished/semi-finished wood (everything that arrives has already been kebonised).
- **Kallo** = mixed — the sub-locations distinguish Raw / WIP / FG.
- **2nd Choice and Short Length** valued at Raw Materials account: write-down flows through `account_stock_variation_id` (609000 Decrease/Increase in Stocks of Raw Materials) — simplest treatment that preserves balance-sheet integrity.

### 6.2 Why Quarantine posts to Raw Materials

Stock entering Quarantine hasn't yet been reclassified — it's awaiting a
decision. Keeping it at the **raw materials** account avoids premature
reclassification to FG or write-down. When released, it moves to the
target location and valuation follows.

### 6.3 Prerequisites on the Company + Categories

Besides location mapping, three other Odoo 19 parameters must be set on
Kebony BNV (company 3). See [[Accounting & Margin Architecture]] §13:

- `res.company.anglo_saxon_accounting = True`
- `res.company.account_stock_journal_id` set (Inventory Valuation journal)
- `product.category` properties written **in BNV context**:
  `property_cost_method = 'fifo'`, `property_valuation = 'real_time'`,
  `property_stock_valuation_account_id`, `property_stock_account_production_cost_id`.

---

## 7. System Locations

In addition to the warehouse-specific locations above, Odoo provides
virtual/system locations shared across the company:

| Location | Type | Purpose |
|---|---|---|
| **Customers** | `customer` | Virtual destination for outbound deliveries |
| **Vendors** | `supplier` | Virtual source for inbound receipts |
| **Production** | `production` | Virtual location for manufacturing consumption/output |
| **Scrap** | `inventory` | Destination for scrapped/rejected goods |
| **Inventory Adjustment** | `inventory` | Source/destination for physical count adjustments |
| **Transit** | `transit` | Inter-warehouse transfers in progress |

These are standard Odoo locations and do not require custom
configuration. They are listed here for completeness and to clarify the
full location tree.

---

## 8. Common Stock Flows

All inbound goes through `/Reception` first (Gate 1 QC). All outbound
stages in `/Shipping` (Gate 3 QC). The `/Stock` main is the default rest
state for A-grade material.

### 8.1 Inbound Reception (via Reception QC)

```
Vendors  -->  TBK/Reception  -->  [QC]  -->  TBK/Stock         (pass)
                                    |
                                    +---->  TBK/Quarantine     (hold)
                                    |
                                    +---->  TBK/2nd Choice     (minor defect)
                                    |
                                    +---->  Scrap + claim      (reject)
```

Transfer TBK → Kallo:
```
TBK/Shipping  -->  KALLO/Reception  -->  [QC]  -->  KALLO/Stock/Raw - Prime
```

### 8.2 Production Flow (Kallo)

```
KALLO/Stock/Raw - Prime      -->  Production  (raw consumed)
KALLO/Stock/WIP - Ready-Mix  -->  Production  (chemical mix consumed)

Production  -->  KALLO/Stock/WIP - Kebonisation  (during AC + dryer)
Production  -->  KALLO/Stock/WIP - Clear         (post-kebonisation, pre-machining, for RDK-bound products)
Production  -->  KALLO/Stock/FG - Character      (A-grade KSP, direct to FG)
Production  -->  KALLO/2nd Choice                (B-grade at destacking)
Production  -->  KALLO/Short Length              (off-cuts at destacking)
Production  -->  Scrap                           (rejected boards)
```

### 8.3 External Machining (RDK subcontract)

```
KALLO/Stock/WIP - Clear  -->  RDK/Reception  -->  [RDK process]  -->  RDK/Stock
                                                                        |
                                                                        +-->  RDK/2nd Choice
                                                                        +-->  RDK/Short Length
                                                                        +-->  Scrap

RDK/Stock  -->  KALLO/Stock/FG - Clear  (return for central despatch)
       or -->  RDK/Shipping  -->  Customers  (direct ship from RDK)
```

### 8.4 Quality Downgrade / Re-class (any warehouse)

```
*/Stock          -->  */Quarantine       (QC hold pending decision)
*/Quarantine     -->  */Stock             (released)
*/Quarantine     -->  */2nd Choice        (downgraded)
*/Quarantine     -->  */Short Length      (re-cut to salvage)
*/Quarantine     -->  Scrap               (rejected)

*/Stock          -->  */2nd Choice        (direct downgrade, no hold)
```

### 8.5 Outbound Delivery (via Pre-Dispatch QC)

```
*/Stock  -->  */Shipping  -->  [QC Gate 3]  -->  Customers  (carrier pickup)
                                 |
                                 +----> */Quarantine  (defect found, return to hold)
```

### 8.6 Customer Return / Claim

```
Customers  -->  */Reception OR */Quarantine  -->  [QC Gate 4]  -->  */Stock        (A-grade re-sale — rare)
                                                     |
                                                     +------------>  */2nd Choice  (B-grade re-sale — typical)
                                                     +------------>  */Short Length (re-cut)
                                                     +------------>  Scrap + claim
```

---

## 9. Naming Conventions

### Warehouse short codes

Use uppercase abbreviations that match physical site identity:

| Site | Short code |
|---|---|
| Kallo Plant | `KALLO` |
| RDK | `RDK` |
| TabakNatie | `TBK` |

### Location naming

Child locations follow the pattern: `{WH_CODE}/{Location Type}`

Examples: `KALLO/Stock`, `RDK/B-Grade`, `TBK/Quarantine`

---

## 10. Relationship to Other Documents

- **Odoo 19 implementation parameters**: [[Accounting & Margin Architecture]] §13 — the accounting/tooling detail that makes per-location valuation JEs post correctly
- **Physical reality**: [[Manufacturing Landscape]] §7 (Inventory & Location Topology)
- **Quality grading**: [[Manufacturing Landscape]] §8 (B-Grade Conceptual Model)
- **Metrics**: [[Metrics & Physical Units]] — all locations carry the same metric fields
- **US warehouses**: Separate topology under INC entity (Pasadena, consignment)
- **Costing**: [[Costing Architecture & COGS Decomposition]] — valuation per location
- **Reception BOL**: [[Reception BOL & Inbound Logistics]] — Gate 1 documentation requirements

---

## 11. Implementation Checklist

When creating or updating this tree on any Odoo instance (test or prod):

- [ ] 3 `stock.warehouse` records: KALLO, RDK, TBK (company = Kebony BNV)
- [ ] Per warehouse: create standard sub-locations (Reception, Stock, Shipping, Quarantine, 2nd Choice, Short Length) as children of the warehouse view location
- [ ] Kallo only: create WIP and FG sub-locations under `KALLO/Stock`; ensure `Production` virtual location exists with `usage='production'`
- [ ] Set `valuation_account_id` on every location per §6.1 (Odoo 19 gate — without this, no valuation JEs post)
- [ ] Configure product categories in BNV context (see [[Accounting & Margin Architecture]] §13)
- [ ] Verify by running a PO receipt and a stock-move between sub-locations; check that `STJ` journal entries post

---

## 12. Open Items

- **Kallo Reception sub-type split** — decide whether Reception needs Raw / FG splits (for cases where RDK returns machined FG to Kallo for central shipment). Current decision: single Reception, QC decision moves to the right sub-location.
- **FSC / PEFC certification per lot** — certification attributes live on `stock.lot`, not on the location (wood is certified, regardless of where it sits). Current: 100%-certified-per-lot in practice; % mixed-content mode supported by the CoC spec but not used today (see [[Chain of Custody Architecture]]).
- **Transit location between warehouses** — Odoo's default transit works for BNV → BNV internal moves. For RDK subcontract, the `subcontract` route handles it. Confirm no gap.

---

*This document defines the target Odoo configuration. Actual warehouse
creation and location setup is performed in Odoo Inventory > Configuration,
or by the idempotent `tools/apply_bnv_accounting_config.py` script for
production deployment.*
