# Backlog

> Living checklist of all open items — bugs, tech debt, feature requests, and deferred decisions.
> Module: all | Updated: 2026-02-26

---

## How to Use

- Items are grouped by category
- Priority: `P0` = blocker, `P1` = should fix soon, `P2` = next opportunity, `P3` = someday
- Status: `[ ]` open, `[x]` done, `[-]` won't do
- Each item references the module and file(s) affected

---

## Bugs

- [ ] **P1** — `kebony_manufacturing` missing dependency on `kebony_bol_report`
  - `product_template.py` reads `quant.x_studio_number_of_boards` and `quant.x_studio_lf_avail` — fields defined in `kebony_bol_report/models/stock_quant.py`
  - Manufacturing `__manifest__.py` does not list `kebony_bol_report` in `depends`
  - Will crash if manufacturing installed without bol_report
  - **Fix**: add `"kebony_bol_report"` to depends, or use `getattr()` fallback

---

## Tech Debt

- [ ] **P2** — Fragile BoM XML reference (`kebony_manufacturing`)
  - `data/mrp_bom_data.xml` uses `search="[('name','=','Kebony Chemical Mix')]"` instead of XML ID `ref="product_chemical_mix"`
  - Will break if product is renamed

- [ ] **P2** — DL state machine has no server-side guards (`kebony_manufacturing`)
  - State transitions (`action_plan`, `action_lock`, `action_done`) don't validate current state
  - View buttons hide invalid transitions, but nothing prevents API-level misuse
  - **Fix**: add `if self.state != 'expected_state': raise UserError(...)` in each action

- [ ] **P3** — Empty `mrp_production.py` placeholder (`kebony_manufacturing`)
  - Phase 6 placeholder — document intent or remove file

- [ ] **P3** — Unused `note` field on `account.ledger.account` (`vvf_multi_ledger`)
  - Defined in model but not displayed in form view
  - Either add to form or remove field

---

## Feature Requests

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

## Manufacturing Phases (Remaining)

- [ ] **P1** — Phase 6: MO generation from DL (button)
- [ ] **P2** — Phase 7: DL <-> MO sync + state machine
- [ ] **P2** — Phase 8: DL Proposal Wizard (demand -> DL)
- [ ] **P3** — Phase 9: MES feedback layer
