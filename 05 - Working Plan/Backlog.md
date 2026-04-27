# Backlog

> Living checklist of all open items — bugs, tech debt, feature requests, and deferred decisions.
> Module: all | Updated: 2026-04-10

---

## How to Use

- Items are grouped by category
- Priority: `P0` = blocker, `P1` = should fix soon, `P2` = next opportunity, `P3` = someday
- Status: `[ ]` open, `[x]` done, `[-]` won't do
- Each item references the module and file(s) affected

---

## Pending Push (Session 2026-04-10)

These changes are **committed locally** on the `test` branch and need a PR `test → main` to reach prod:

- [ ] **P0** — **`security_groups.xml`** — Revert root menu group_ids (fix for Ann & Bethany Sales menu outage)
  - Live-fixed in prod via API (cleared group_ids on sale.sale_menu_root / account.menu_finance / accountant.menu_accounting)
  - Source code reverted with warning comment: never touch root menu group_ids — ACLs handle visibility
- [ ] **P0** — **`pack_tag_template.xml`** — Board count shows real boards (x_kebony_boards), not Pack UoM qty
- [ ] **P1** — **`bol_us_template.xml`** — Tarps/strap protection warning block below Conditions
- [ ] **P1** — **`kebony_accounting_hub.py`** — 4 accrual fixes:
  1. Country analytic tag bug fix (ISO-2 → ISO-3 map for ~75 countries)
  2. JE line label includes invoice number + date
  3. One JE per invoice-month, back-dated to EOM
  4. (see next)
- [ ] **P1** — **`accrual_settlement_wizard.py` + view** — `booking_date` field (editable, default today, allows back-dating settlement JE)
- [ ] **P1** — **`res_company.py`** — Added `stock.move.line` to `action_rebuild_kebony_metrics` MODELS list (was missing — cause of stale pack tag board counts)
- [ ] **P1** — **`stock_move_line.py`** — Added `write()` + `create()` overrides to force `add_to_compute` on quantity/uom/product changes (Odoo stock engine bypasses `@api.depends` on Studio-chain fields)

**Action**: open PR `test → main` via GitHub, merge, Odoo.sh auto-deploys prod.

## Completed this Session (Prod changes, live)

- [x] **P0** — Ann & Bethany Sales menu outage fixed (cleared group_ids on 3 root menus)
- [x] **P0** — `2747-I-12 (CON)` and `2746-I-12 (CON)` length bug fixed
  - `x_studio_length_1` was 144 (inches) instead of 12 (feet)
  - `x_studio_length_m` was 43.89 instead of 3.66
  - Fixed both + 432 stale move lines recomputed
  - Remaining 955 "broken" move lines are `[ARCHIVED-LI]` legacy (UoM=LI) or tiny scrap leftovers — not real issues
- [x] **P0** — Classification = Wood on 2,569 non-master wood SKUs
- [x] **P0** — `master_item_code_1` populated on 111 CON variants
- [x] **P1** — `rough_sawn_parent_id_1` populated on 348 Radiata FGs (legacy char field, superseded by `kebony_parent_id` see below)

## Completed this Session (Test instance — awaiting merge for prod)

- [x] **P1** — `kebony_parent_id` (Manufacturing Parent) populated on 2,819 wood SKUs on TEST (99.6% coverage, 13 orphans left — all CON with weird imperial formats)
  - Installed `kebony_manufacturing` module
  - Created 491 missing parent SKUs (124 + 367 in 2 iterations) via template duplication
  - Created master `1003` (was completely missing) + 7 length SKUs for Scots Pine chain
  - Full 4-level chains working: imperial → metric twin → RS → WW
  - Rules implemented in `tools/populate_parent_id.py` + `populate_parent_id_cascade.py` + `create_missing_parent_skus.py`
  - See [[Product Master Data]] §5.6 for `kebony_parent_id` specification
  - **To prod**: install `kebony_manufacturing` module on prod + re-run scripts with `--env prod`

## Bugs

- [ ] **P1** — `kebony_manufacturing` missing dependency on `kebony_bol_report`
  - `product_template.py` reads `quant.x_studio_number_of_boards` and `quant.x_studio_lf_avail` — fields defined in `kebony_bol_report/models/stock_quant.py`
  - Manufacturing `__manifest__.py` does not list `kebony_bol_report` in `depends`
  - Will crash if manufacturing installed without bol_report
  - **Fix**: add `"kebony_bol_report"` to depends, or use `getattr()` fallback

- [ ] **P3** — 13 orphan SKUs with non-standard imperial formats
  - Examples: `2216-I-13'10"`, `2216-I-9.512' (CON)`, `2779-I-11.48' (CON)`
  - Trailing apostrophe/quote and CON suffix
  - Cannot be auto-linked to metric twins — need manual rename or link

---

## Tech Debt

- [ ] **P2** — Fragile BoM XML reference (`kebony_manufacturing`)
  - `data/mrp_bom_data.xml` uses `search="[('name','=','Kebony Chemical Mix')]"` instead of XML ID `ref="product_chemical_mix"`
  - Will break if product is renamed

- [ ] **P2** — DL state machine has no server-side guards (`kebony_manufacturing`)
  - State transitions (`action_plan`, `action_lock`, `action_done`) don't validate current state
  - View buttons hide invalid transitions, but nothing prevents API-level misuse
  - **Fix**: add `if self.state != 'expected_state': raise UserError(...)` in each action

- [x] **P3** — `mrp_production.py` (`kebony_manufacturing`)
  - Phase 6 implemented: MO creation from DL, reverse link via `mrp_production_id` ✅

- [x] **P3** — `note` field on `account.ledger.account` (`vvf_multi_ledger`)
  - Added to form view ✅

---

## Feature Requests

### Pack Tags — Belgium Version
- [ ] **P3** — Extend Pack Tags report to Belgium entity (`kebony_bol_report`)
  - **Current state**: Pack Tags report implemented for US (US Letter, feet, `pack_tag_template.xml`)
  - **Needed for BE**: A4 paper format, metric units (meters instead of feet), possibly different label layout
  - **Options**: entity-gated single template (if/else on entity type) or separate `pack_tag_be_template.xml`
  - **Action**: confirm with BE warehouse whether they need the same report, then adapt

### Business Status Model
- [ ] **P2** — Replace hardcoded business status field with proper model (`kebony_bol_report`)
  - **Current state**: hardcoded selection list on a Studio field — quick fix, not sustainable
  - **Blocked by**: waiting for Belgium sales back-office team to provide their requirements alongside US team — need a generic solution that works for both entities
  - **Target design**: new model `kebony.business.status` (or similar) with:
    - `name`, `code`, `active`, `company_ids` (multi-company aware)
    - Replace current hardcoded selection with Many2one to new model
    - Configurable per entity (US may have different statuses than Belgium)
  - **Action**: wait for Belgium feedback, then design + implement

### Supply Chain Rule Assignment
- [ ] **P1** — Receive per-product supply chain rule mapping from COO
  - **Blocked by**: COO to provide the complete assignment list
  - **What we need**: which products are MTO, ATO-White Wood, ATO-Brown Wood, or Make to Stock
  - **Also needed**: buffer product references and min stock levels for ATO/MTS products, min process batch trigger for MTO
  - **Placeholder ready**: [[Product Master Data]] §5.6.3 — table structure prepared, awaiting data
  - **Once received**: populate §5.6.3 table, create `x_kebony_supply_chain_rule` Selection field on `product.template`, configure replenishment routes per rule
  - **Action**: follow up with COO

### Chain of Custody — FSC Certification Traceability
- [ ] **P1** — New module `kebony_certification`: lot-level FSC traceability, % accounting, audit-proof document chain
  - **Current state**: 3 Studio fields (`x_studio_fsc_*`) with QWeb-only fallback on BOL/invoice. No lot tracking, no claim propagation, no evidence linkage. Cannot prove chain to auditor.
  - **Kebony reality**: percentage method — inbound lots arrive as "FSC Mix 70%", transitioning to 100%
  - **Architecture**: [[Chain of Custody Architecture]] — full design document
  - **Slide deck (legacy pre-workshop)**: `06 - Slide Decks/chain_of_custody.html`
  - **User guide (post-workshop, April 2026)**: `06 - Slide Decks/certifications_user_guide.html`
  - **MVP scope**:
    - New models: `certificate.product.group`, `partner.certificate`, `cert.claim.period`, `cert.account.ledger`, `cert.trace.link`, `cert.nonconformity`
    - Extend: `stock.lot`, `stock.move.line`, `purchase.order.line`, `stock.picking`, `mrp.production`, `sale.order.line`, `account.move.line`
    - Inbound claim capture (PO → receipt → lot) with % tracking
    - Auto-propagation through stock moves and manufacturing
    - Outbound claim validation (delivery + invoice)
    - Supplier certificate register
    - 6 audit reports (inbound register, stock by lot, traceability, sales register, supplier certs, claim ledger)
    - Coexist with existing `x_studio_fsc_*` fields (migration, not replacement)
  - **Phase 2**: MO trace links + Dryer Load integration + nonconformity workflow + audit packet PDF
  - **Phase 3**: Credit method (if needed), FSC database API, certification dashboard
  - **Confirmed**: dual scheme (FSC + PEFC) — depends on country of origin and supplier
  - **Confirmed**: all wood products lot-tracked (no exceptions, missing setup to be corrected)
  - **Open questions**: exact PEFC claim labels + supplier/origin mapping, soft vs. hard enforcement, DDP claim split, claim period length
  - **Blocked by**: answers to open questions (Quality / CEO / COO / US Finance)

#### Workshop follow-up items (April 2026) — see [[Chain of Custody Architecture]] §12
- [ ] **P1** — **Hard mixing block for Kebonisation and RDK MOs** (`mrp.production`)
  - Override `action_confirm` + `action_done`: read `stock.lot.x_kebony_cert_claim` on all consumed move lines; raise `UserError` if any differ
  - Hard-coded block for these two MO types — no override toggle
  - Other MO types (repacks, grade-downs) keep existing Rule 3 warn/block per product group
- [ ] **P1** — **Sales order certification toggle** (`sale.order.line`, mirror of min-qty-guarantee toggle)
  - Fields: `x_kebony_cert_required` (bool) + `x_kebony_cert_scheme_required` (fsc/pefc) + `x_kebony_cert_claim_required` (char)
  - Reservation logic: filter lot candidates to matching scheme + claim
  - Picking validation: block confirm if reserved lots don't match; explicit error message
  - Propagate into RDK subcontract PO when line is fulfilled via RDK
- [ ] **P1** — **RDK subcontract certification validation** (`purchase.order` + `stock.picking`)
  - Input-side: same mixing block as Kebonisation MO
  - Output-side: on receipt, reconcile subcontractor-declared claim against what inputs supported; mismatch → auto-quarantine + `cert.nonconformity`
  - Contract clause is contractual (not system) — add to subcontract template
- [ ] **P1** — **Invoice as certification proof** — print scheme + claim + cert code on every certified line; include ESR number for US-bound lines
  - Update `invoice_us_report.xml` footer + line details
  - Add BE/EU invoice template if separate
- [ ] **P1** — **ICC-ES — product-level certification axis (US only)** — new axis alongside FSC/PEFC
  - Extend `product.template` with: `x_kebony_icc_esr_number`, `x_kebony_icc_esr_valid_to`, `x_kebony_icc_esr_scope`, `x_kebony_icc_attachment_ids`, `x_kebony_icc_us_relevant`
  - Dedicated "US Code Compliance" tab on product form
  - SO validation: US-bound customer + certification required → ESR present + not expired (hard block, configurable per scope for non-regulated use)
  - Invoice footer / per-line note: ESR number
  - Activity / alert 90 days before ESR expiry (scheduled action + user notification)
  - On-demand "Submittal PDF" generator for architect / GC / inspector
  - **Open**: scope field type (selection vs m2m); non-regulated-use behaviour (hard block vs warn); subcontractor cert verification frequency

### Sales Area — Hierarchical Territory Model
- [ ] **P1** — Replace flat US-only sales area with hierarchical, geography-flexible model
  - **Current state**: `x_studio_area_of_sales` — flat Many2one, 9 US/CAN values, no hierarchy, no manager, no geography link
  - **Architecture**: [[Sales Area Architecture]] — full design document
  - **New models**: `kebony.sales.area` (hierarchical territory with manager), `kebony.geo.zone` (flexible geography: region/country/country group)
  - **Phase 1**: models + US migration + analytic account auto-creation + partner field swap
  - **Phase 2**: European territories (hierarchy defined with Sales VP) + customer assignment + dashboard rollup
  - **Phase 3**: "Split Area" wizard + territory maps + budget/reforecast targets by area
  - **Key design**: sales area sits **on top of** country in analytics, not replaces it. Reorganizing territories doesn't break country reporting.
  - **Open questions**: exact European hierarchy (TBD with Sales VP), OEM as area vs. channel, geo zone granularity (text vs. formal codes)

### Accrual Rate Configuration Model
- [ ] **P2** — Move accrual rates from hardcoded constants to a configurable model (`kebony_bol_report`)
  - **Current state**: rates hardcoded in `account_move_line.py` `_kebony_prepare_accrual_vals()`:
    - Marketing: 4% wood / 1.5% accessory
    - Royalties: 5%
    - Management Fees: 14%
  - **Target design**: new model `kebony.accrual.rate` (or add to `kebony.accounting.hub`):
    - Accrual type (marketing_wood, marketing_accessory, royalties, mgmt_fees)
    - Rate (percentage)
    - Effective date (for historical tracking / future changes)
    - Company-scoped
  - **UI**: accessible from Kebony Accounting Hub — finance team can update rates autonomously without code changes
  - **Migration**: seed initial records with current hardcoded values, then remove constants from Python

---

## Deferred Decisions

- [x] **P3** — Block reception/picking on Biewer consignment POs
  - Biewer POs are financial-only (goods already in warehouse)
  - **Done**: `purchase_order.py` overrides `_create_picking()` to skip consignment POs
  - Flag: `x_kebony_is_consignment_po` (Boolean on purchase.order, set at PO creation)
  - Blue banner on PO form: "Financial Only — No Receipt"
  - Ref: [[Consignment & Biewer]] §5

- [ ] **P3** — RDK machining variance allocation rule (INV-1)
  - Standard-then-adjust costing for subcontracting MOs
  - Variance = actual vendor bill - standard cost absorbed
  - Allocation method TBD: prorate to inventory + COGS, or post to variance account
  - Ref: [[Implementation White Paper]] §3.6

- [ ] **P2** — Analytical Accounting (4 plans: Country, BU, Sales Area, CM Level)
  - White paper done: [[Analytical Accounting Architecture]] — includes GL→CM mapping, auto-posting rules, entity scope, decisions
  - 4 plans: Country (75+2 values), BU (9 values), Sales Area (9 US/CAN regions), CM Level (11 values)
  - Sales Area = contact-level field (`x_kebony_sales_area` on `res.partner`), inherited to SO/invoice/lines
  - COGS split: BoM-based decomposition preferred — **BNV only** (INC = 100% COGS-D, no conversion)
  - Phase 1 (P0): data seeding — plans + analytic accounts + `x_kebony_sales_area` on partner
  - Phase 2 (P1): auto-post Country + Sales Area + CM Level on revenue and COGS lines
  - Phase 3 (P2): BoM decomposition, BU auto-assignment, CM Level on EOM accruals
  - Phase 4 (P3): EOM allocation wizards (unabsorbed costs, country distribution) — BNV only
  - **Decided**: IC country = USA (Canada gap via EOM realloc), distribution key = always m³
  - **Key decisions pending**: COGS fallback for non-BoM products, BNV GL validation, mgmt fees IC reallocation mechanism
  - Ref: [[Analytical Accounting Architecture]] §13–§15

---

## Documentation

- [x] **P1** — Product Master Data v2.0
  - Complete rewrite: [[Product Master Data]] — 16 sections, Big 4 quality
  - Full field registry with exact Studio technical names (81 import columns mapped)
  - Model values for all selection/many2one fields
  - Governance framework: RACI matrix, Master Data Guardian role, change control process
  - Reconciled field names between Excel import, Studio, and codebase
  - Planning Family model documented with seed data inventory
  - Downstream impact map (13 functional domains)
  - Ref: `/Users/oeb/Documents/Product Masterdata_FINAL_v7.xlsx`

---

## Manufacturing Phases

- [x] **P1** — Phase 6: MO generation from DL (`action_create_mo` button) ✅
- [x] **P2** — Phase 7: DL ↔ MO loose coupling + navigation (`mrp_production_id` + computed link on MO) ✅
- [x] **P2** — Phase 8: DL Proposal Wizard (demand → DL) ✅
- [ ] **P3** — Phase 9: MES feedback layer (fields reserved: `actual_start_date`, `actual_finish_date`, `actual_duration_hours`; `actual_m3` still needed)
