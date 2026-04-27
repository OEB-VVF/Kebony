# Chain of Custody Architecture

**Scope**: All Kebony entities (global)
**Module**: `kebony_certification` (new addon)
**Entity filter**: None — applies to all companies
**Standards**: FSC-STD-40-004 V3-1, PEFC ST 2002:2020
**Dual scheme**: FSC and PEFC both active — scheme depends on country of origin and supplier

---

## 1. Design Principle

Certification must travel with the material flow, not just live on
the product or supplier master. For any certified outbound shipment,
the system must reconstruct:

- which certified input lots/documents were received
- what claim/material category came in
- where the material moved or was transformed
- how the output claim was determined
- which sales/delivery documents carried the claim and certificate code
- supporting attachments, calculations, and logs

Both FSC and PEFC require five-year record retention.

---

## 2. Current State (as-is) — LIVE IN PRODUCTION

Three Studio fields carry FSC data today:

| Label              | Field                  | Model              | Type | Description                                    |
|--------------------|------------------------|--------------------|------|------------------------------------------------|
| FSC Code (Product) | `x_studio_fsc_`       | `product.template` | Char | Product-level FSC claim code (e.g. "FSC Mix 70%") |
| FSC Number         | `x_studio_fsc_number` | `product.template` | Char | FSC certificate number (e.g. "FSC-C123456")    |
| FSC Code (Company) | `x_studio_fsc_code`   | `res.company`      | Char | Company-level FSC code. Global fallback.       |

**Important distinction**: `x_studio_fsc_` is the **claim type** (what
appears on BOLs). `x_studio_fsc_number` is the **certificate identifier**
(what appears on invoices). These are separate compliance concepts.

### 2.1 Fallback Resolution Pattern (current — QWeb only)

The same product → company fallback is used on both BOL reports:

```
fsc_product = product.product_tmpl_id.x_studio_fsc_
fsc_company = picking.company_id.x_studio_fsc_code
display     = fsc_product OR fsc_company OR ''
```

**Priority**: Product-level takes precedence. If product has no FSC
code, the company-level code applies. If neither is set, the column
is left blank.

This allows mixed-FSC inventory (some products certified, others not)
while maintaining a company-wide default.

### 2.2 Report Usage (current)

| Report               | Field Used           | Fallback                        | File                                  |
|----------------------|----------------------|---------------------------------|---------------------------------------|
| Expedition BOL (US)  | `x_studio_fsc_`     | `x_studio_fsc_code` (company)  | `report/bol_us_template.xml`          |
| Reception BOL (US)   | `x_studio_fsc_`     | `x_studio_fsc_code` (company)  | `report/bol_reception_us_template.xml`|
| Invoice (US)         | `x_studio_fsc_number`| None (blank if missing)        | `report/invoice_us_report.xml`        |

**Note**: The Invoice uses a different field (`fsc_number`) and has
**no company fallback**. This is intentional — the certificate number
is product-specific and should not be defaulted from the company.

### 2.3 Current Design Decisions

- **No Python logic involved.** The fallback is purely in QWeb template
  conditionals. No computed field is created.
- **Product-level FSC takes precedence.** This supports mixed inventory
  where only some products carry certification.
- **Invoice uses a separate field.** The claim code (BOL) and certificate
  number (invoice) serve different regulatory purposes.

### 2.4 Current Limitations

The current implementation has **no lot-level tracking and no traceability
chain**. All units of a given product carry the same FSC claim. This
means Kebony **cannot** distinguish between FSC Mix and FSC 100% within
the same product — which is what Tom DeKeyser's April 2026 request
requires. The target architecture below resolves this by making
`stock.lot` the primary certification carrier.

---

## 3. Control Methods

The design supports three methods per product group:

| Method               | Description                                              |
|----------------------|----------------------------------------------------------|
| Physical separation  | Certified and non-certified material kept physically apart |
| Percentage method    | Output claim based on % of certified input in a period. **Kebony's current method — receiving 70% certified wood per lot, targeting 100%.** |
| Credit method        | Credits earned from certified input, spent on output claims |

Kebony today operates under the **percentage method**: inbound lots arrive
as "FSC Mix 70%" (70% certified content). The company is transitioning
toward 100% certified input. The system must support both states and
track the percentage per lot/period for audit.

---

## 4. Target Data Model

### 4.1 Master / Control Layer

#### `certificate.product.group`

Certified product group definition. Both FSC and PEFC manage logic
by product group — especially for accounting methods and annual summaries.

| Field               | Type       | Description                          |
|---------------------|------------|--------------------------------------|
| `name`              | Char       | Group name                           |
| `scheme`            | Selection  | `fsc` / `pefc`                       |
| `company_id`        | Many2one   | res.company                          |
| `control_method`    | Selection  | `physical_separation` / `percentage` / `credit` |
| `description`       | Text       | Notes                                |
| `active`            | Boolean    | Archive flag                         |

> **Design decision**: `scheme` is a selection field, not a separate model.
> Two values (FSC/PEFC) do not justify a normalized table.

#### `partner.certificate`

Supplier/customer certification status. Required to evidence supplier
verification at inbound.

| Field                   | Type       | Description                       |
|-------------------------|------------|-----------------------------------|
| `partner_id`            | Many2one   | res.partner                       |
| `scheme`                | Selection  | `fsc` / `pefc`                    |
| `certificate_code`      | Char       | e.g. FSC-C123456                  |
| `scope_note`            | Text       | Scope description                 |
| `valid_from`            | Date       |                                   |
| `valid_to`              | Date       |                                   |
| `status`                | Selection  | `valid` / `expired` / `suspended` / `unknown` |
| `evidence_attachment_ids` | Many2many | ir.attachment                    |
| `verified_on`           | Date       | Last verification date            |
| `verified_by`           | Many2one   | res.users                         |
| `company_id`            | Many2one   | res.company                       |

#### Extend `product.template`

Reference fields only — not evidence.

| Field                         | Type       | Description                          |
|-------------------------------|------------|--------------------------------------|
| `x_kebony_cert_relevant`      | Boolean    | Subject to CoC tracking              |
| `x_kebony_cert_product_group_id` | Many2one | Default product group              |
| `x_kebony_cert_scheme`        | Selection  | Default scheme                       |
| `x_kebony_requires_claim_on_sale` | Boolean | Claim mandatory on outbound       |

> **Migration**: existing `x_studio_fsc_*` fields remain as-is for
> backward compatibility. New fields are additive. Report templates
> updated to prefer new fields with fallback to Studio fields.

---

### 4.2 Transactional Traceability Layer

#### Extend `purchase.order.line`

Planned inbound claim — confirmed at receipt.

| Field                        | Type       | Description                    |
|------------------------------|------------|--------------------------------|
| `x_kebony_cert_scheme`       | Selection  | fsc / pefc                     |
| `x_kebony_cert_claim_in`     | Char       | e.g. "FSC Mix 70%"            |
| `x_kebony_supplier_cert_code`| Char       | Supplier certificate code      |
| `x_kebony_cert_product_group_id` | Many2one | Product group              |

#### Extend `stock.lot`

**Primary certification carrier.** Receipt evidence anchors here.

| Field                          | Type       | Description                    |
|--------------------------------|------------|--------------------------------|
| `x_kebony_cert_scheme`         | Selection  | fsc / pefc                     |
| `x_kebony_cert_claim`          | Char       | Claim on this lot              |
| `x_kebony_supplier_cert_code`  | Char       | Supplier certificate code      |
| `x_kebony_cert_source_ref`     | Char       | Source doc reference           |
| `x_kebony_cert_source_date`    | Date       | Source doc date                |
| `x_kebony_cert_qty_received`   | Float      | Certified qty received         |
| `x_kebony_cert_product_group_id` | Many2one | Product group                |
| `x_kebony_cert_status`         | Selection  | `certified` / `non_certified` / `mixed` / `downgraded` |
| `x_kebony_cert_origin_partner_id` | Many2one | Source supplier             |
| `x_kebony_cert_attachment_ids` | Many2many  | ir.attachment — evidence      |
| `x_kebony_cert_hold`           | Boolean    | Quarantine flag               |

> **Lot tracking confirmed**: All wood products will be lot-tracked
> without exception (setup to be corrected where missing). Accessories
> are not certification-relevant. The lot is therefore the single
> authoritative certification carrier for all certified products.

#### Extend `stock.move.line`

Claim transfer at each movement — the audit chain.

| Field                          | Type       | Description                    |
|--------------------------------|------------|--------------------------------|
| `x_kebony_cert_scheme`         | Selection  | fsc / pefc                     |
| `x_kebony_cert_claim`          | Char       | Claim on this movement         |
| `x_kebony_cert_product_group_id` | Many2one | Product group                |
| `x_kebony_cert_qty`            | Float      | Certified quantity             |
| `x_kebony_cert_move_role`      | Selection  | `receipt` / `internal` / `production_consume` / `production_output` / `delivery` / `adjustment` |

#### `cert.trace.link` (new model)

Explicit input-to-output link. Critical for manufacturing and repacking.

| Field                | Type       | Description                         |
|----------------------|------------|-------------------------------------|
| `company_id`         | Many2one   | res.company                         |
| `scheme`             | Selection  | fsc / pefc                          |
| `product_group_id`   | Many2one   | certificate.product.group           |
| `input_move_line_id` | Many2one   | stock.move.line                     |
| `input_lot_id`       | Many2one   | stock.lot                           |
| `output_move_line_id`| Many2one   | stock.move.line                     |
| `output_lot_id`      | Many2one   | stock.lot                           |
| `qty_input`          | Float      | Input quantity                      |
| `qty_output`         | Float      | Output quantity                     |
| `mo_id`              | Many2one   | mrp.production (optional)           |
| `picking_id`         | Many2one   | stock.picking (optional)            |
| `note`               | Text       |                                     |

#### Extend `mrp.production`

Manufacturing claim validation. Must integrate with `kebony_manufacturing`
dryer-centric flow (Dryer Loads, Process Packs).

| Field                           | Type       | Description                   |
|---------------------------------|------------|-------------------------------|
| `x_kebony_cert_scheme`          | Selection  | fsc / pefc                    |
| `x_kebony_cert_product_group_id`| Many2one   | Product group                 |
| `x_kebony_cert_planned_claim`   | Char       | Expected output claim         |
| `x_kebony_cert_actual_claim`    | Char       | Validated output claim        |
| `x_kebony_cert_validation`      | Selection  | `pending` / `valid` / `invalid` |

> **Integration point**: Dryer Load (`kebony.dryer.load`) triggers MO
> creation. Cert validation hooks into `action_done` on MO, inspecting
> consumed lots and writing `cert.trace.link` records.

#### Extend `stock.picking` (outbound)

| Field                           | Type       | Description                   |
|---------------------------------|------------|-------------------------------|
| `x_kebony_cert_scheme`          | Selection  | fsc / pefc                    |
| `x_kebony_cert_claim_out`       | Char       | Validated output claim        |
| `x_kebony_cert_code_printed`    | Char       | Certificate code for docs     |
| `x_kebony_cert_validation`      | Selection  | `pending` / `valid` / `invalid` |
| `x_kebony_cert_product_group_id`| Many2one   | Product group                 |

#### Extend `sale.order.line` and `account.move.line`

| Field                           | Type       | Description                   |
|---------------------------------|------------|-------------------------------|
| `x_kebony_cert_scheme`          | Selection  | fsc / pefc                    |
| `x_kebony_cert_claim_out`       | Char       | Output claim                  |
| `x_kebony_cert_code_printed`    | Char       | Certificate code for printing |
| `x_kebony_cert_lot_ids`         | Many2many  | Supporting lots               |

---

### 4.3 Compliance / Audit Layer (Phase 2+)

#### `cert.nonconformity`

Nonconforming product log — required by both standards.

| Field              | Type       | Description                          |
|--------------------|------------|--------------------------------------|
| `name`             | Char       | Auto-sequence                        |
| `company_id`       | Many2one   | res.company                          |
| `scheme`           | Selection  | fsc / pefc                           |
| `date_detected`    | Date       |                                      |
| `detected_by`      | Many2one   | res.users                            |
| `issue_type`       | Selection  | `missing_claim` / `invalid_supplier` / `mixing` / `unsupported_claim` / `missing_doc` / `other` |
| `related_lot_id`   | Many2one   | stock.lot                            |
| `description`      | Text       |                                      |
| `immediate_action` | Text       |                                      |
| `corrective_action`| Text       |                                      |
| `state`            | Selection  | `open` / `contained` / `resolved` / `closed` |

#### `cert.claim.period`

Period-based accounting for percentage method. **Required for MVP** since
Kebony operates under FSC Mix 70%.

| Field              | Type       | Description                          |
|--------------------|------------|--------------------------------------|
| `name`             | Char       | e.g. "2026-Q1"                       |
| `company_id`       | Many2one   | res.company                          |
| `scheme`           | Selection  | fsc / pefc                           |
| `product_group_id` | Many2one   | certificate.product.group            |
| `date_start`       | Date       | Period start                         |
| `date_end`         | Date       | Period end                           |
| `state`            | Selection  | `open` / `closed`                    |

#### `cert.account.ledger`

Certified volume accounting by period and product group. Tracks
certified vs. non-certified input quantities and resulting output claim.

| Field                   | Type       | Description                    |
|-------------------------|------------|--------------------------------|
| `company_id`            | Many2one   | res.company                    |
| `scheme`                | Selection  | fsc / pefc                     |
| `product_group_id`      | Many2one   | certificate.product.group      |
| `claim_period_id`       | Many2one   | cert.claim.period              |
| `input_certified_qty`   | Float      | Certified input volume (m3)    |
| `input_total_qty`       | Float      | Total input volume (m3)        |
| `certified_percentage`  | Float      | Computed: certified / total    |
| `output_certified_qty`  | Float      | Output claimed as certified    |
| `uom_id`                | Many2one   | uom.uom (default: m3)         |
| `state`                 | Selection  | `draft` / `confirmed`          |

> **Kebony reality**: Today input is ~70% FSC certified per lot.
> The ledger tracks this ratio per period to support the "FSC Mix X%"
> output claim. When Kebony reaches 100% certified input, the system
> naturally transitions to physical separation (all output = FSC 100%).

---

## 5. Business Rules

### Rule 1: Receipt gating

At receipt, if a line's product is `x_kebony_cert_relevant`:
- Require: scheme, claim, supplier cert code, lot creation
- If missing: **soft warning** by default (configurable to hard block)
- Option: validate into quarantine (`x_kebony_cert_hold = True`)
- Bulk receipt (containers): allow partial claim with per-lot override

### Rule 2: Claim propagation

Certification data auto-propagates from receipt lot → internal moves →
MO consumption/output → delivery lines. Users never retype downstream.

All wood products are lot-tracked — the lot is always the certification carrier.

### Rule 3: Mixing control

If a production order or stock operation mixes lots with incompatible
claims under physical separation:
- **Warn** (default) or **block** (configurable per product group)
- Downgrade claim with justification field
- Log as `cert.nonconformity` if override used

### Rule 4: Outbound claim validation

Before delivery validation with a certified claim, verify:
- Source material exists and supports claim
- Quantities sufficient
- Supplier/source evidence attached
- Certificate code available for printing

Configurable: soft (warning banner) or hard (block validation).

### Rule 5: Audit packet

From any lot, MO, picking, or invoice, the user can open a traceability
view showing:
- Source receipt documents
- Linked lots and movements
- Trace links (input → output)
- Output documents
- Nonconformities (if any)

---

## 6. Document Flow

```
INBOUND
  Vendor doc / attachment
    → PO line (planned claim)
      → Receipt picking
        → Lot created (claim + supplier cert + evidence)
          → stock.move.line (cert data stored)

INTERNAL
  Internal transfer / MO consumption / MO output
    → move lines inherit cert data from lot
    → cert.trace.link written for MO input→output
    → Dryer Load → MO → cert validation at action_done

OUTBOUND
  Delivery picking
    → Claim validated against source lots
    → Delivery slip prints: scheme + claim + certificate code
    → Invoice line mirrors claim
    → Sales register updated
```

---

## 7. Reports

| # | Report                          | Purpose                                    | Phase |
|---|---------------------------------|--------------------------------------------|-------|
| 1 | Certified inbound register      | Prove certified sourcing and receipt        | MVP   |
| 2 | Certified stock by lot/location | Prove segregation / stock control           | MVP   |
| 3 | Input-to-output traceability    | Reconstruct chain for any shipment/lot      | MVP   |
| 4 | Certified sales register        | Prove outbound claims correctly issued      | MVP   |
| 5 | Supplier certification register | Show supplier status is controlled          | Ph 2  |
| 6 | Claim ledger / annual summary   | Volume accounting by scheme + group + period| Ph 3  |
| 7 | Nonconformity / corrective action | Show governance and issue handling        | Ph 2  |

---

## 8. UI Design

### Receipt — Certification tab

On `stock.picking` (incoming) and `stock.move.line`:
- Scheme, claim, supplier cert code, product group
- Source document ref/date
- Attachment widget
- "Create quarantine if incomplete" toggle

### Lot — Chain of Custody smart button

Opens traceability view:
- Inbound docs
- Movement history
- Consumed-by / delivered-in
- Linked claims
- Nonconformities

### MO — Certification Validation section

- Consumed certified qty (auto-computed from consumed lots)
- Supported output claim
- Conflicts / warnings

### Delivery — Claim Validation block

- Supported / unsupported indicator
- Output claim to print
- Certificate code
- Link to audit packet

---

## 9. Implementation Phases

### MVP (Phase 1) — Audit-proof baseline

- Inbound claim capture (PO line + receipt + lot) with % tracking
- Lot-level traceability fields (claim, source, evidence)
- Move-line propagation (auto, no retyping)
- Claim period + ledger (percentage method — 70% → 100% transition)
- Outbound claim validation (delivery + invoice)
- Certified inbound / sales / stock reports
- Supplier certificate register (partner.certificate)
- Migration: coexist with `x_studio_fsc_*` Studio fields

### Phase 2 — Manufacturing chain + governance

- MO trace links (`cert.trace.link`) with Dryer Load integration
- Nonconformity workflow
- Annual volume summary report
- Audit packet generator (one-click traceability PDF)

### Phase 3 — Advanced

- Credit method support (if ever needed)
- Complaint / internal audit workflow models
- FSC public database verification (info.fsc.org API)
- Dashboard: certification health by entity

---

## 10. Entity Scoping

Certificate codes differ by company (INC, BNV, Holding).
The existing `x_studio_fsc_code` on `res.company` already handles
the company-level certificate code. The new `partner.certificate`
model is for **suppliers and customers**, not the company itself.

Multi-company access rules: all cert models carry `company_id` and
follow standard Odoo multi-company security.

---

## 11. Open Questions

1. **PEFC scope confirmed**: Kebony operates under both FSC and PEFC,
   depending on country of origin and supplier. Both schemes must be
   supported from MVP. The `scheme` selection field on all models
   handles this natively — no extra logic needed beyond ensuring
   PEFC-specific claim labels (e.g. "PEFC Certified", "PEFC 70%")
   are supported alongside FSC equivalents.

2. **Lot tracking confirmed**: All wood products will be lot-tracked — no
   exceptions. Missing setup to be corrected. Accessories are not cert-relevant.

3. **DDP imports (US)**: Vendor bill claim vs. physical receipt claim —
   are these always identical, or can they diverge?

4. **Soft vs. hard blocks**: Per-entity or global? Who can override?

5. **Hardcoded BOL text**: The reception BOL has hardcoded Radiata/Maple
   FSC origin text — should this become data-driven?

---

## 12. Workshop Follow-Up (April 2026)

Outcomes from the certification workshop. These refine / harden earlier rules and add a new certification axis (ICC-ES) that sits alongside FSC / PEFC but at product level, not lot level.

### 12.1 Hard mixing block at MO level — Kebonisation and RDK

Rule 3 (mixing control) is **hardened** for the two MO types that produce certified output:

| MO type | Policy | Enforcement |
|---|---|---|
| Kebonisation (in-house autoclave) | **Block** — inputs must share the same scheme + claim | Python constraint on `mrp.production.action_confirm` and `action_done`; reads `stock.lot.x_kebony_cert_claim` across all consumed move lines |
| RDK (subcontract) | **Block** — contractual obligation + technical check on inputs sent to subcontractor; reconciled against the claim returned by the subcontractor on output | Same constraint at `action_confirm` for inputs; validation at `action_done` that the claim declared by the subcontractor matches the input claim |

The default "warn or block" toggle from Rule 3 still applies to other MO types (e.g. repacks, grade-downs). For Kebonisation and RDK it is hard-coded to block — no override.

### 12.2 Sales Order certification toggle

Mirror the existing **minimum quantity guarantee** toggle on `sale.order.line` with a new **certification guarantee** toggle.

| Field | Type | Description |
|---|---|---|
| `x_kebony_cert_required` | Boolean | Customer contractually requires a certified supply on this line |
| `x_kebony_cert_scheme_required` | Selection (fsc / pefc) | Scheme required |
| `x_kebony_cert_claim_required` | Char | Claim required (e.g. "FSC Mix 70%", "PEFC Certified", "FSC 100%") |

**Downstream effects:**

- **Planning / reservation**: lot candidates filtered to those matching the required scheme + claim (and ICC-ES requirement if the product is US-bound — see §12.5)
- **Delivery control**: `stock.picking` validation blocks confirmation if any reserved lot fails the match; error is explicit ("lot X is FSC Mix 70%, order requires FSC 100%")
- **RDK flow on SO**: when the SO is fulfilled through an RDK subcontract, the certification requirement propagates into the subcontract PO and is checked both at input send and at output receipt

### 12.3 RDK subcontract validation

RDK is primarily a contractual control, reinforced by technical checks in Odoo:

- **Inputs** (materials sent to subcontractor): same mixing block as Kebonisation MO (§12.1)
- **Output** (goods received from subcontractor): subcontractor declares the claim on their delivery document; system reconciles declared claim against what the inputs supported. Mismatch → quarantine + `cert.nonconformity` record (Rule 3 + §4.3)
- **Contractual layer**: the RDK subcontract must include explicit no-mixing clauses and evidence requirements (supplier certificate, origin docs). Tracked in `partner.certificate` for the subcontractor.

### 12.4 Invoice as proof of certification

**The invoice is the customer-facing certification proof.** Every certified line on an invoice carries:

- Scheme (FSC / PEFC)
- Claim class (e.g. "FSC Mix 70%", "FSC 100%", "PEFC Certified")
- Certificate number (company-level or per-lot, depending on scheme requirements)
- Where applicable: ICC-ES evaluation report number (§12.5)

Reconstruction chain: invoice line → delivery → lot(s) → claim + supplier evidence. Must remain intact for the 5-year FSC / PEFC retention horizon.

### 12.5 ICC — a second certification axis (US market)

**ICC = International Code Council.** The relevant certification is **ICC-ES** (Evaluation Service), which issues **ESRs** (Evaluation Service Reports) approving a product for use under US building codes — IBC, IRC, IFC — for structural use, fire rating, decking load, cladding attachment, etc.

ICC-ES is **fundamentally different** from FSC / PEFC:

| Axis | FSC / PEFC | ICC-ES |
|---|---|---|
| Purpose | Chain of custody, sustainable forestry | Building-code compliance / product performance |
| Granularity | **Per lot** (`stock.lot`) | **Per product template** (`product.template`) |
| Mixing concept | Mixing contaminates the claim → MO-level block | No mixing concept — attribute of the SKU |
| Renewal | Annual CoC audit | Annual fee + retained testing evidence |
| Market relevance | Global (customer-driven) | US only (code-driven) |
| Customer value | "Responsibly managed forest" | "Code-legal for US buildings" |
| Where it appears | Invoice line — scheme + claim + cert code | Product spec sheet; submittal to architect / GC / inspector; invoice footer |

**Data model additions (product.template):**

| Field | Type | Description |
|---|---|---|
| `x_kebony_icc_esr_number` | Char | ESR report number (e.g. "ESR-3144") |
| `x_kebony_icc_esr_valid_to` | Date | Expiry date (trigger renewal alert 90 days out) |
| `x_kebony_icc_esr_scope` | Selection / m2m | Covered use categories: structural, decking, cladding, fire-rated, etc. |
| `x_kebony_icc_attachment_ids` | Many2many | ir.attachment — ESR PDF, test reports |
| `x_kebony_icc_us_relevant` | Boolean | Only gate ICC checks for US-market products |

**Where it surfaces:**

- Product form — dedicated "US Code Compliance" tab
- Sales order — if `x_kebony_cert_required` + customer is US: validate the product's ESR is present and not expired
- Invoice — ESR number printed on invoice footer or per-line note
- Submittal PDF — generate on demand for architect / GC (not part of invoice flow)

**Governance**: expiry alert 90 days before `x_kebony_icc_esr_valid_to`. Missing ESR on a US-bound SO line is a hard block (configurable to warn for non-regulated use categories).

---

## See Also

- [[Product Master Data]] — Product field registry (FSC fields in Compliance section)
- [[Implementation White Paper]] — Manufacturing architecture
- [[Dryer-Centric Architecture]] — Dryer Load → MO flow
- [[Entity Registry]] — Entity types and feature gating
- User guide: `06 - Slide Decks/certifications_user_guide.html`

> **Document history**: This file merges the former `FSC Certification &
> Compliance.md` (current-state only) into Section 2. That file has been
> removed to avoid dual-source drift. This document is the single source
> of truth for all certification and chain of custody matters.
> April 2026: Section 12 added following the certification workshop — MO mixing block for Kebonisation / RDK, SO certification toggle, invoice-as-proof, and ICC-ES product-level axis.
