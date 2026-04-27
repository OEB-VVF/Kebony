# Quality Gates Architecture

**Scope**: All Kebony manufacturing entities — BNV (Belgium), Norway entities, US distribution
**Module**: `kebony_quality` (new, built on Odoo native Quality app)
**Dependencies**: `quality`, `quality_mrp`, `quality_mrp_workorder`, `quality_stock`, `stock`, `mrp`, `purchase`, `sale`, `helpdesk`, `project`, `kebony_manufacturing`, `kebony_bol_report` (for lot / certification integration)
**Standards referenced**: FAVV phytosanitary inspection (EU) · ICC-ES (US) · internal lab procedures
**Status**: Architecture v1.0 — April 2026 workshop outcomes

---

## 1. Design Principle

Quality gates are **control points on existing Odoo objects** (receipts, pickings, MOs, deliveries, tickets), not a parallel shadow system. Every gate:

- Hooks into a native Odoo record via a **Quality Control Point (QCP)**
- Produces a **Quality Check** at the right moment in the flow
- Can escalate to a **Quality Alert** (nonconformance ticket) with project-management follow-up
- Writes evidence (measurements, documents, photos) against the underlying object — not a side database

**Core rule — stick to Odoo standard.** Native stages, native kanbans, native escalation. Custom code is limited to:
- A shared **reason catalogue** (controlled list maintained by QA)
- A small bridge **Quality Alert → Project** (1 Many2one + a "Create Project" button)
- The chemical **correction loop** (§6) which is not a native pattern
- The claim workflow with **co-sign threshold** at €5k (§9)

Everything else is Odoo out of the box.

---

## 2. Pack Numbering Chain (canonical)

All operational labels follow this chain. Any earlier document using different naming is superseded. The canonical source is [[Terminology Bible]] §5.

**Chain:**

```
White wood (supplier plate)  →  SA-xxxxx  →  AA-xxxxx  →  DA-xxxxx  →  FA-xxxxx
    no internal label             Stacking      Autoclave      Dryer       Finished
    (supplier ID only)            Antwerp       Antwerp        Antwerp     (FG lot)
```

| Label | Stage | Formed from | Odoo anchor |
|---|---|---|---|
| **White wood** | Raw wood received from supplier | — | `stock.lot` on supplier's own license plate. **No RA label.** |
| **SA-xxxxx** | Stacking Antwerp — pack right after stacking | N white-wood plates | `kebony.process.pack` with `stage=SA` |
| **AA-xxxxx** | Autoclave Antwerp — *same* pack after impregnation | 1 SA (1:1, state change only) | `kebony.process.pack` with `stage=AA` (same `pack_number`) |
| **DA-xxxxx** | Dryer Antwerp — *same* pack after drying | 1 AA (1:1, state change only) | `kebony.process.pack` with `stage=DA` (same `pack_number`) |
| **FA-xxxxx** | Finished Antwerp — sellable pack after destacking | 1 DA → N FA (split per SKU) | `stock.lot` on the finished good (leaves the Process Pack model) |

Display name = `{stage}-{pack_number}`. **The pack number is stable end-to-end from SA to DA** — only the stage letter changes. Each stage transition is recorded as an event row in `kebony.process.pack.event` (timestamp, operator, equipment — autoclave #, dryer #).

**No pack-level merge.** The "2-to-1" step at the dryer is a **container-level grouping**: 2 autoclave loads (`kebony.autoclave.batch`) are assigned to 1 dryer run (`kebony.dryer.load`). Packs inside carry `autoclave_batch_id` + `dryer_load_id` — they don't merge.

| Grouping model | Purpose | Scale |
|---|---|---|
| `kebony.autoclave.batch` | Physical autoclave load. Its own number. | Groups N packs that transition SA → AA together |
| `kebony.dryer.load` | Physical dryer run. Its own number. | Groups ~2 autoclave batches (so ~2N packs) transitioning AA → DA together |

**"Charge"** is retained as the industry term for an autoclave load — used interchangeably with "AA" in conversation; `AA-xxxxx` is the system identifier.

*Note:* "FA" as a stage label is distinct from the product code **Furfuryl Alcohol** (`CHEM-FA`). Different domains — no model collision.

---

## 3. Flow Diagram — Reception to Expedition

```
══════════════════════════════════════════════════════════════════════════
                     EXTERNAL  ─►  ODOO OBJECT  ─►  QUALITY GATE
══════════════════════════════════════════════════════════════════════════

CHEMICAL SUPPLY CHAIN
─────────────────────
Vendor (FA / MA / CA / NaC)
    │
    ▼
[stock.picking — incoming]  ◄──┤ GATE 1: Chemical Reception
    │                          │   QCP on receipt; product categ = Chemical
    │                          │   Required: COA attach + lab measurement
    │                          │   Block until released
    ▼
Inventory — chemical tanks
    │
    ▼
[mrp.production — Ready-Mix]  ◄──┤ GATE 6: In-house Batch Quality
    │                            │   QCP on MO "Kebony Chemical Mix"
    │                            │   Lab measures → if fail, correction loop
    │                            │   (Production + Lab joint sign-off)
    │                            │   Autoclave blocked until fixed
    ▼
Kebony Chemical Mix tank  ─────►  consumed by autoclave MOs downstream


WHITE WOOD SUPPLY CHAIN
───────────────────────
Vendor (NZ, other)
    │
    ▼
[stock.picking — receipt at TBK]  ◄──┤ GATE 2a: Tabaknatie Reception
    │                                │   QCP on receipt; location = TBK
    │                                │   FAVV biohazard inspection (NZ)
    │                                │   Aspect/damage check by TBK
    │                                │   Reason + free text + claim to Purchasing
    ▼
Inventory at TBK (full packs)
    │
    ▼
[stock.picking — internal TBK→Kallo]  (full pack, no sort)
    │
    ▼
[stock.picking — arrival Kallo]  ◄──┤ GATE 2b: Kallo Visual Inspection
    │                                │   QCP on internal arrival
    │                                │   Visual check, quarantine if NOK
    │                                │   Lot split here (defects separated)
    ▼
White wood packs at Kallo (supplier license plate)


STACKING → AUTOCLAVE → DRYER → FINISHED
───────────────────────────────────────
White wood (supplier plate)
    │
    ▼
[mrp.production — stacking]  ◄──┤ GATE 3: Stacking QC #1
    │                            │   QCP on MO operation = stacking
    │                            │   MES feeds moisture + length
    │                            │   Sampling: fixed norm (e.g. X/100)
    │                            │   Bad boards → WASTE (sorted per species)
    │                            │   SA always formed with good boards;
    │                            │   flagged + quarantined if overall fails
    │                            │   Stacking machine stops at exact count;
    │                            │   excess boards return to raw-material WH
    ▼
SA-xxxxx (Process Pack, stage=SA)
    │
    ▼
[mrp.production — Kebonisation]  ◄──┤ Certification hard block
    │                                │   (see Chain of Custody §12)
    │                                │   Inputs must share scheme+claim
    │                                │   Consumes Kebony Chemical Mix
    │                                │   1 SA → 1 AA (same pack_number, state change)
    ▼
AA-xxxxx (same Process Pack, stage=AA)
    │
    ▼
[2 autoclave batches → 1 dryer run — container grouping, not pack merge]
    │
    ▼
[mrp.production — drying]  ◄──┤ GATE 4: Stacking QC #2 (post-autoclave)
    │                          │   QCP on MO operation = de-stacking
    │                          │   Cracking, twisting, moisture
    │                          │   + ASYNC lab check per autoclave load
    │                          │   Released by default; blocked retroactively
    │                          │   on lab fail → full autoclave load quarantine
    ▼
DA-xxxxx (same Process Pack, stage=DA — pack_number unchanged)
    │
    ▼
FA-xxxxx (stock.lot on FG, N per DA split per SKU) → Inventory FG


RDK — SUBCONTRACT MANUFACTURING
───────────────────────────────
[purchase.order — RDK]  ◄──┤ Certification hard block on inputs
    │                       │   (Chain of Custody §12)
    │
    ├──► Multiple MOs at subcontractor (one PO, several charges)
    │
    ▼
[stock.picking — receipt from subcontractor]  ◄──┤ GATE 5: RDK Quality
    │                                              │   QCP on subcontract receipt
    │                                              │   One quality report per PO
    │                                              │   Three grades as distinct products:
    │                                              │     A (prime) / B (short) / C (waste)
    ▼
Inventory at Kallo


EXPEDITION
──────────
FG inventory
    │
    ▼
[stock.picking — delivery]  ◄──┤ GATE 7: Expedition
    │                           │   QCP on outgoing picking
    │                           │   Mandatory photo per pack
    │                           │   Spontaneous transfer/picking checks
    │                           │   Damage report → auto credit note
    ▼
Customer

POST-DELIVERY
─────────────
External claim (customer, rep, …)
    │
    ▼
Customer portal OR public web form
    │
    ▼
[helpdesk.ticket]  ◄──┤ GATE 8: Claims workflow
    │                 │   Reason (controlled list) → auto-assign to owner
    │                 │   Watcher = Sales Manager
    │                 │   Sign-off: ≤€5k Sales Manager alone
    │                 │            >€5k Sales + QA Manager co-sign
    │                 │   Sales Manager communicates outcome
    │
    ├──► [account.move.refund] (auto credit note on damage)
    │
    └──► [project.project + project.task] (mini PM if serious)
            └── standard Odoo stages
            └── links back to ticket / alert / lot
```

---

## 4. Gate Catalogue

### Gate 1 — Chemical Reception

| Property | Value |
|---|---|
| **Odoo anchor** | `stock.picking` (incoming), filtered by product category = Chemical |
| **Trigger** | QCP on receipt |
| **Scope** | 4 chemicals: Furfuryl Alcohol (FA), Maleic Anhydride (MA), Citric Acid (CA), Sodium Carbonate (NaC). Water excluded (no supplier COA) |
| **Checks** | COA document attached (mandatory) + lab measurement (single test — see open questions on Furchem) |
| **Fail path** | Block receipt; lot held in quarantine; claim initiated to supplier |
| **Owner** | Lab + QA |
| **Evidence** | COA PDF attached to lot; lab measurement stored on quality.check |

### Gate 2a — Tabaknatie (TBK) Reception

| Property | Value |
|---|---|
| **Odoo anchor** | `stock.picking` (incoming), location = TBK |
| **Trigger** | QCP on receipt; additional flag for non-EU origin (NZ → biohazard inspection) |
| **Checks** | FAVV phytosanitary inspection (if non-EU); aspect/damage check by TBK |
| **Fail path** | Full pack moves to Kallo regardless — sorting happens at Kallo (Gate 2b). Claim initiated to Purchasing; reason (controlled list) + free text |
| **Owner** | Purchasing + TBK ops |
| **Evidence** | Inspection certificate (FAVV) + aspect notes + photos on picking |

### Gate 2b — Kallo Visual Inspection

| Property | Value |
|---|---|
| **Odoo anchor** | `stock.picking` (internal transfer arrival at Kallo) |
| **Trigger** | QCP on arrival |
| **Checks** | Visual inspection |
| **Fail path** | Quarantine at Kallo defect location; **lot split** here (defective boards pulled out; rest proceeds) |
| **Owner** | Kallo QA |
| **Evidence** | Reason (controlled list) + free text on quality.check |

### Gate 3 — Stacking QC #1

| Property | Value |
|---|---|
| **Odoo anchor** | `mrp.production` + `mrp.workorder`, operation = stacking |
| **Trigger** | QCP on MO operation; MES integration feeds measurements. MES `MES_ProducedPackage` emits on **operation code 10 (Stacking)**. |
| **Checks** | Moisture, length — sampled at fixed production norm (e.g. X/100) |
| **Fail path (boards)** | Rejected boards → **waste**, sorted by wood species (plant manager requirement) |
| **Fail path (pack)** | SA **always formed** with remaining good boards; flagged + quarantined if overall below threshold. MES `Quality = 3` on the produced package = scrap. |
| **Owner** | Stacking operator + Kallo QA |
| **Evidence** | Measurements on quality.check; defect reason entered **in Odoo by the operator** (MES does not emit reasons to ERP — see §14). Controlled list seeded from MES error-code catalogue. |

### Gate 4 — Stacking QC #2 (post-autoclave, de-stacking)

| Property | Value |
|---|---|
| **Odoo anchor** | `mrp.production` + `mrp.workorder`, operation = de-stacking |
| **Trigger** | QCP on MO operation; asynchronous lab check per autoclave charge. MES `MES_ProducedPackage` emits on **operation code 23 (Charging / Autoclave out)**, **26 (Drying out)**, and **30 (De-stacking)**. |
| **Checks** | Cracking, twisting, moisture; lab random check per autoclave charge |
| **Fail path (lab, async)** | Released by default after destacking. On lab fail → **full autoclave charge retroactively quarantined** (block by exception). If any product already shipped → high-priority alert to Sales Manager + ExCo (no auto-recall) |
| **Owner** | Lab + QA |
| **Evidence** | Lab report + measurements on quality.alert |

### Gate 5 — RDK Subcontract

| Property | Value |
|---|---|
| **Odoo anchor** | `stock.picking` (subcontract receipt), linked to `purchase.order` |
| **Trigger** | QCP on subcontract receipt; one report **per PO** (not per delivery) |
| **Checks** | A-grade (prime) / B-grade (short length, recoverable by cutting) / C-grade (waste) — three distinct products |
| **Fail path** | A-grade variance → claim to subcontractor; B-grade routed to re-cut workflow; C-grade → waste (species-sorted) |
| **Owner** | Procurement + QA |
| **Evidence** | Subcontractor quality report attached to PO; per-grade receipt quantities |

### Gate 6 — In-house Chemical Batch (Ready-Mix)

| Property | Value |
|---|---|
| **Odoo anchor** | `mrp.production` for Kebony Chemical Mix |
| **Trigger** | QCP on mix MO |
| **Checks** | Lab measurement of the batch (per internal spec) |
| **Fail path** | **Correction loop** — adjust composition (add / dilute), re-measure; autoclave blocked until in-spec. See §6. |
| **Owner** | Production + Lab (joint sign-off) |
| **Evidence** | Each measurement + each adjustment on quality.check / alert |

### Gate 7 — Expedition

| Property | Value |
|---|---|
| **Odoo anchor** | `stock.picking` (delivery) |
| **Trigger** | QCP on delivery validation |
| **Checks** | **Mandatory photo per pack** during loading (stored on picking); spontaneous transfer/picking checks |
| **Damage path** | Damage report with photo + CRM docs → customer notified → **auto-generated credit note** |
| **Owner** | Logistics + Sales (comms) |
| **Evidence** | Photos on picking; damage report on quality.alert |

### Gate 8 — External Claims (see §9 full detail)

Covered in a dedicated section because it crosses Helpdesk, Quality, Project and Accounting.

---

## 5. Supporting Models

### 5.1 Shared Reason Catalogue — `quality.reason`

Controlled list maintained by QA. Used on every check, alert and claim.

| Field | Type | Notes |
|---|---|---|
| `name` | Char | Label (e.g. "Transport damage", "Moisture out of range", "Dimensional defect — twist") |
| `category` | Selection | Transport / Chemical / Wood / Process / Packaging / Logistics / Other |
| `gate_applicability` | Many2many | Which gates this reason applies to (some are multi-gate, e.g. transport damage) |
| `owner_user_id` | Many2one (res.users) | Default owner for auto-routing on claims (§9) |
| `active` | Boolean | Archive flag |

All `quality.check`, `quality.alert` and `helpdesk.ticket` records carry:
- `reason_id` (Many2one to `quality.reason`) — controlled
- `note` (Text) — free-text override / additional detail

Rationale: a single defect (e.g. transport damage) can originate at multiple gates. A shared catalogue makes root-cause reporting possible across the whole flow.

### 5.2 Quarantine Locations

One quarantine stock location per physical site. Pack identity (white wood / SA / AA / DA / FA) carries the stage; location carries the status.

| Site | Quarantine location |
|---|---|
| Tabaknatie | `WH/TBK/QUARANTINE` |
| Kallo | `WH/KALLO/QUARANTINE` |
| US (INC) | `WH/INC/QUARANTINE` |
| Subcontractor receipts (RDK) | `WH/KALLO/QUARANTINE/RDK` |

Defect sub-location per species (plant manager's request for waste sorting at Gate 3).

### 5.3 Quarantine Release

Two paths:

| Path | Trigger | Sign-off |
|---|---|---|
| **Direct to defect / waste** | Common case — failed QC boards / packs that will never be shipped | No sign-off; operator moves to defect location |
| **Heavy inspection + QA release** | Lab-triggered full-charge quarantine at Gate 4 | **QA Manager** sign-off required to release; otherwise stays quarantined or scrapped |

### 5.4 Escalation on Quality Alert

Standard `quality.alert` stages used; QA configures them on install:

```
New  →  In Progress  →  Containment  →  Root Cause  →  CAPA  →  Closed
                             │
                             └──► (from 3rd failed re-test) Escalated → QA Manager
```

No custom counter. Escalation is a stage with auto-assignment rule to QA Manager.

---

## 6. Chemical Correction Loop (Gate 6)

Not a native Odoo pattern — small custom workflow on the Ready-Mix MO.

```
Ready-Mix MO starts
    │
    ▼
Batch produced
    │
    ▼
Lab measurement  ◄──┐
    │               │
    ├─ In spec ──► Release; MO done; sign-off Production + Lab
    │               │
    └─ Out of spec  │
          │         │
          ▼         │
      Adjust composition (add X / dilute Y)
          │         │
          └─────────┘  (loop)
```

**Consumption accounting**: each adjustment adds material. Approach — **lump-sum at batch close**: a single consumption event captures total material consumed (initial formula + all corrections). FIFO cost of the final batch reflects everything consumed. No per-correction JE overhead.

**Escalation**: no numeric hard limit. After ~2–3 failed re-tests, the alert moves to the **Escalated** stage (auto-assigned to QA Manager). QA Manager decides — continue correcting, scrap the tank (exceptional), or rework with a different recipe.

**Autoclave block**: while a Ready-Mix batch is out of spec, any autoclave MO requesting that tank is blocked. Enforced by a Python constraint on `mrp.production.action_confirm` when the consumed chemical mix has an open alert.

---

## 7. Mini Project Management — Link to Projects

Standard Odoo **Project** app. No parallel PM.

**Native features used:**
- `project.project` + `project.task` with standard stages (To Do / In Progress / Done / Cancelled — QA configures on install)
- Kanban + Gantt + deadlines + sub-tasks + followers + activities + mentions
- Dashboards filtered per role

**Native bridges that already exist:**
- `helpdesk.ticket → project.project` (Enterprise)

**Custom bridge needed** (small):
- `quality.alert → project.project` — one Many2one field + a "Create Project" button
- The button spawns a project pre-filled with the alert context and 3–5 template sub-tasks (Investigate / Contain / CAPA / Verify / Close)

**Use cases:**
- Serious quality alert (e.g. recall-risk) → Create Project → cross-functional follow-up
- HSE incident → Create Project → investigation + corrective action
- Large claim (>€5k) → already linked from ticket, Project spun up if multi-party

**Primary consumer**: QA Manager (Kanban view of all quality+HSE tasks), Plant Manager (filter = ops), ExCo (pre-filtered card in the existing ExCo deck).

---

## 8. Claims Workflow — Gate 8 detail

### 8.1 Entry channels

| Channel | Use | Odoo component |
|---|---|---|
| **Customer portal** | Known account-holders (primary — no user licence cost) | `helpdesk.ticket` via portal |
| **Public web form** | Walk-ins / unknown parties | `website_helpdesk_form` |
| **Email-to-ticket** | Fallback | `helpdesk.alias` |

All three land in the **Helpdesk** module as tickets assigned to Customer Service.

### 8.2 Ticket routing

```
Ticket created
    │
    ▼
Set `reason_id` (controlled list — §5.1)
    │
    ▼
Auto-assign to `reason.owner_user_id`
    │
    ▼
Auto-add watcher: Sales Manager (always)
    │
    ▼
Classification: damage? cert issue? dimensional? …
    │
    ▼
Sign-off determination
    │
    ├─ Credit amount ≤ €5 000 → Sales Manager alone
    └─ Credit amount > €5 000 → Sales Manager + QA Manager co-sign
    │
    ▼
Sales Manager communicates outcome to customer
    │
    ▼
If damage: auto-generate credit note (draft) → validated per sign-off rule
```

### 8.3 Reason → Owner mapping

Does not exist today. Build together with the new QA Manager at project kick-off. Table form:

| Reason | Owner |
|---|---|
| Transport damage | Logistics Manager |
| Dimensional defect | Plant Manager (Kallo) |
| Cert/claim mismatch | QA Manager |
| Chemical quality issue | QA Manager |
| Packaging damage | Logistics Manager |
| … | … |

Stored on `quality.reason` as `owner_user_id`.

---

## 9. Reporting & Dashboards

Reporting is a first-class requirement, not a Phase-4 afterthought. Two levels:

### 9.1 Operational dashboards (live, per role)

Implemented as native Odoo views (Kanban / List / Graph / Pivot) filtered per user. No custom code.

| Dashboard | Audience | Source | Key measures |
|---|---|---|---|
| **Open quality alerts** | QA Manager · Plant Manager | `quality.alert` | By stage, by reason category, by age, by owner |
| **Open claims** | Sales Manager · Customer Service · QA | `helpdesk.ticket` (claim type) | By reason, by customer, by value, by age |
| **Quality project board** | QA Manager · ExCo | `project.task` filtered by quality project | Kanban by stage; overdue tasks flagged |
| **Quarantine inventory** | QA · Plant Manager · Finance | `stock.quant` filtered on quarantine locations | Qty + value per site, per species, per reason |
| **Gate pass rate (live)** | Plant Manager | `quality.check` | Pass / fail % per gate per shift |

### 9.2 Periodic reports (monthly / quarterly)

Produced via scheduled cron; delivered as PDF and/or pushed into the Odoo Spreadsheet module (same surface as the finance dashboards).

| Report | Frequency | Audience | Content |
|---|---|---|---|
| **Gate performance** | Monthly | QA + ExCo | Pass rate per gate, trend vs prior 12 months, top 5 reasons |
| **Waste report** | Monthly | Plant Manager · Finance | Waste volume + value, per species, per source gate |
| **Credit-note volume** | Monthly | Finance · Sales Manager | Count + € by reason, by customer segment, trend |
| **Supplier quality performance** | Monthly (and on-demand) | Procurement · QA | See §10 — dedicated section |
| **Quality KPI pack** | Quarterly | ExCo · CEO | Aggregate: pass rate, claim cost, DPPM, corrective-action SLA, supplier scorecard top 10 |

### 9.3 Dashboard in Odoo Spreadsheet

The quarterly KPI pack lives in **Odoo Spreadsheet**, next to the existing finance dashboards (analytical accounting, accruals, margin). Single pivot surface for the business — no external BI at this stage.

### 9.4 Alerting

- Every failed QCP → Odoo activity on the owner (native behaviour)
- Every quality alert in "Escalated" stage → email to QA Manager + project task
- Every supplier tolerance breach (§10) → auto-create helpdesk ticket type = supplier claim, routed to Procurement Manager
- Full-charge retroactive quarantine (Gate 4) with already-shipped product → high-priority email to Sales Manager + ExCo (no auto-recall)

---

## 10. Supplier Quality Performance & Contract Tolerance

Recurring measurement of each supplier's delivered quality against their contractual tolerance, with automatic claim generation on breach. This is what turns per-delivery quality data into an actionable supplier-management cycle.

### 10.1 Model — `supplier.quality.tolerance`

Per supplier, per product (or category), per metric.

| Field | Type | Notes |
|---|---|---|
| `partner_id` | Many2one (res.partner) | Supplier |
| `product_id` / `product_category_id` | Many2one | Scope: specific product or whole category |
| `metric` | Selection | Moisture-out-of-spec % / Dimensional defect % / Cert-match failure % / On-time delivery % / Other |
| `tolerance_value` | Float | Contractual threshold (e.g. 2% max moisture deviation) |
| `unit` | Selection | percent / count / days / m³ |
| `period` | Selection | monthly / quarterly |
| `contract_reference` | Char | PO terms / master contract reference |
| `valid_from` | Date | Tolerance effective date |
| `valid_to` | Date | If fixed-term |
| `claim_template_id` | Many2one (helpdesk.ticket.template) | Template used if breach triggers auto-claim |

### 10.2 Monthly computation (cron)

Scheduled action per entity. For each active supplier × metric × period:

1. Aggregate relevant quality checks / alerts / receipts over the period
2. Compute actual value (e.g. % of lots failing moisture check)
3. Compare to `tolerance_value`
4. Write a `supplier.quality.performance` record with: period, actual, tolerance, variance, breach boolean
5. If breach → auto-create a helpdesk ticket of type **Supplier Claim**, routed to Procurement Manager, pre-filled from template with:
   - Supplier + metric + period
   - Actual vs tolerance
   - List of failing lots / PO lines
   - Suggested claim amount (computed from affected lot value × breach %)

### 10.3 Supplier performance report

Monthly PDF + live dashboard. Per supplier:

- Volume received (m³, €)
- Gate failures (count, %, €)
- Breakdown per reason
- Actual vs tolerance per metric — colour-coded (green / amber / red)
- 12-month trend
- Active claims + closed claims
- Suggested action (warn / formal claim / supplier review)

### 10.4 Link to existing architecture

- Supplier identity + certificate history: `partner.certificate` (Chain of Custody §5)
- Failing lots: `stock.lot` + `quality.check` / `quality.alert`
- Contract tolerance: new `supplier.quality.tolerance` model
- Claim generated: `helpdesk.ticket` (type = supplier_claim) — same workflow engine as customer claims (§8), routed to Procurement instead of Customer Service

### 10.5 Sign-off

- Report reviewed by **Procurement Manager** monthly
- Formal claim (helpdesk ticket) approved by Procurement Manager before sending to supplier
- Material breaches (> €X threshold — TBD) escalated to COO + Finance
- Supplier performance scorecard summarised in the quarterly KPI pack (§9.2)

---

## 11. Standards Compliance — What This Covers

| Obligation | Mechanism |
|---|---|
| Phytosanitary (EU wood imports) | FAVV inspection at Gate 2a, certificate on receipt |
| Chain of custody (FSC / PEFC) | Separate architecture — [[Chain of Custody Architecture]] §12 |
| Building code (US) | ICC-ES — [[Chain of Custody Architecture]] §12.5 |
| ISO 9001 traceability | Lot-level traceability + reason catalogue + audit trail |
| Nonconformity log | `quality.alert` stages + project follow-up (§7) |
| CAPA | Project task templates on quality.alert (§7) |
| 5-year record retention | Standard Odoo retention + attachment archival |

---

## 12. Implementation Phases

### MVP (Phase 1) — audit-proof baseline

- Install Odoo Quality modules (`quality`, `quality_mrp`, `quality_mrp_workorder`, `quality_stock`)
- Configure QCPs for Gates 1, 2a, 2b, 7 (reception + expedition — pure-config gates)
- Seed `quality.reason` catalogue (co-designed with QA Manager)
- Quarantine locations per site
- Mandatory loading photo on delivery picking
- Customer portal + email-to-ticket claim entry; helpdesk routing
- Reason → owner mapping
- Sign-off threshold logic (≤€5k / >€5k)
- Auto credit note from damage report

### Phase 2 — production gates

- QCPs for Gates 3 and 4 (stacking QC #1 and #2)
- MES integration: read defect reasons + measurements into quality.check
- Gate 4 asynchronous block-by-exception logic
- Gate 5 (RDK) — one report per PO, A/B/C grade receipts
- Three RDK grade products + routing to re-cut / waste

### Phase 3 — advanced

- Gate 6 (chemical batch correction loop) — custom workflow
- Autoclave block while chemical alert open
- Quality Alert → Project bridge (`project_id` + "Create Project" button)
- Species-sorted defect sub-locations at Kallo
- ExCo card with filtered quality KPIs
- Quality KPI dashboard in Odoo Spreadsheet
- IoT integration (calipers, scales) — opportunistic

### Phase 4 — nice to have

- Packaging quality gate (Gate 7 extension)
- Self-service credit note approval for small amounts
- FSC / PEFC / ICC-ES expiry dashboard integration
- Training records (HR Learning)

---

## 13. Decisions Made (April 2026 workshop)

- ✅ Stick to Odoo standard — minimal custom code
- ✅ Shared `quality.reason` catalogue maintained by QA, controlled list + free text
- ✅ One quarantine location per site; pack-label chain (white wood → SA → AA → DA → FA) carries identity
- ✅ Default quarantine → defect; **QA sign-off** required only on lab-triggered full-charge quarantine
- ✅ Gate 3: SA always formed with good boards; bad boards become waste sorted per species
- ✅ Gate 4: block by exception (asynchronous)
- ✅ No auto-recall on shipped product when full charge retroactively quarantined — high-priority alert to Sales Manager + ExCo instead
- ✅ Gate 5 RDK: one quality report per PO; A / B / C grades as three distinct products
- ✅ Gate 6 chemical correction: lump-sum consumption at batch close; Production + Lab joint sign-off; autoclave blocked until fixed
- ✅ Gate 7 expedition: mandatory photo **per pack**; auto-generated credit note for damage
- ✅ Gate 8 claims: customer portal + web form + email-to-ticket → Helpdesk; €5k threshold for co-sign (Sales alone ≤ / Sales + QA >); Sales Manager communicates
- ✅ Project management: standard Odoo Project, standard stages; quality.alert → project bridge as the only custom piece
- ✅ Reason → owner mapping: build with QA Manager as project deliverable

## 14. Open Questions

- **Furchem** — supplier name, lab name, or test method? And is the Gate 1 lab measurement one test per delivery, or one per chemical received?
- **MES error-code list** — clarified 2026-04-23: the reason catalogue lives **inside MES only**; the ERP↔MES interface (SIS_MES_Axapta_Summary v0.1) only carries `Quality 1/2/3` on produced packages. The list is therefore **reference data** to seed the Odoo `quality.reason` catalogue (same codes, same wording as MES config), *not* interface payload. Still needed from SIS to populate the catalogue.
- **Gate 6 — hard escalation limit**: no numeric hard stop; "Escalated" stage introduced after ~2–3 failed re-tests. Confirm threshold with QA Manager at kick-off.
- **Gate 3 sampling norm X/100** — define exact X with QA Manager (fixed for whole production, per his answer).
- **Gate 5 RDK — legal-claim mechanism** on A-grade variance (to be shaped with Procurement / Legal).
- **HSE scope** — Quality Alert `category` field will carry HSE as a value; but who owns HSE alerts as a team? (Likely same QA Manager at this stage.)
- **Supplier tolerance matrix** — exact metrics and thresholds per supplier / category — to be populated jointly with Procurement and QA Manager from existing contracts
- **Material breach escalation threshold** (§10.5) — amount above which a supplier claim escalates to COO + Finance — TBD

---

## See Also

- [[Terminology Bible]] — canonical source for the pack chain and Process Pack data model
- [[Chain of Custody Architecture]] — FSC / PEFC / ICC-ES (certification side of quality)
- [[Dryer-Centric Architecture]] — MO flow white wood → SA → AA → DA → FA
- [[Implementation White Paper]] — Manufacturing architecture
- [[Product Master Data]] — Chemical products (FA, MA, CA, NaC, Water)
- User guide: `06 - Slide Decks/quality_support_proposal.html` (pre-workshop positioning for QA Manager)
- User guide: `06 - Slide Decks/quality_gates_user_guide.html` (to be created — post-workshop, derived from this doc)

> **Document history**:
> - v1.0 — 2026-04-22 — Created after the April 2026 quality workshop with the new QA Manager. Incorporates the 8-gate catalogue, pack numbering chain, quarantine + escalation model, chemical correction loop, claims workflow with €5k co-sign, and project-management link.
> - v1.1 — 2026-04-23 — Pack chain terminology aligned with Terminology Bible: no RA (white wood stays on supplier plate); PA → AA (Autoclave Antwerp); SA / AA / DA are the *same* Process Pack with a stable `pack_number`, only the stage letter changes; FA is a FG `stock.lot` (leaves the Process Pack model). Added display-name convention and stage-event logging.
> - v1.1.1 — 2026-04-23 — Correction: no pack-level merge at the dryer. The 2-to-1 is a container-level grouping (2 `autoclave.batch` per `dryer.load`), not a pack merge. Packs stay 1:1 from SA to DA.
> - v1.2 — 2026-04-23 — MES interface codes landed in Gate 3 / 4: stacking (op 10), charging (op 23), drying (op 26), de-stacking (op 30); Quality 1/2/3 on produced packages only; defect reason list re-scoped from "interface artefact" to "reference data seeding Odoo `quality.reason`". Based on SIS_MES_Axapta_Summary v0.1.
