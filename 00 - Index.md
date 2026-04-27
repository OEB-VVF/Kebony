# Kebony — Documentation Index

> Single entry point for all Kebony Odoo 19 documentation.
> Updated: 2026-03-13

---

## Quick Reference

- [[00 - Quick Reference]] — Current test URL, useful links for day-to-day work

## Change Log

**Start here** — every vault change is tracked in a single table.

- [[00 - Change Log]] — Who changed what, when, and why

---

## Architecture Principle

**`product.template` is the operational entity** in Odoo 19.
Packaging UoMs are shared across variants, and since each packaging is unique per SKU (profile + length + unit system), dimensional variants are structurally impossible. Each unique sellable product = its own `product.template`.

---

## 01 - Terminology

The shared language reference for Kebony — precise definitions that eliminate ambiguity across teams.

- [[Terminology Bible]] — Definitions, naming conventions, company scope
- [[Entity Registry]] — Legal entities: INC, Holding, BNV, KAS, NAS (address, VAT, registration — pending)

---

## 02 - General Topics

Product architecture, physical metrics, and cross-entity operational features.

| Document | Scope | Status |
|---|---|---|
| [[Product Master Data]] | Core product architecture & field definitions | Active |
| [[Metrics & Physical Units]] | Linear m, boards, volume m3, mixin architecture | Active |
| [[Pack Reservation]] | Pack selection, full-pack-first, lot lifecycle | Active |
| [[Stock Locations & Warehouses]] | Belgian warehouse topology (Kallo, RDK, TabakNatie), location types, stock flows | Active |
| [[Analytical Accounting Architecture]] | 3 analytic plans (Country, BU, CM Level), allocation rules, P&L waterfall | White Paper |
| [[Budget & Performance Architecture]] | Budget framework, performance reporting | Active |
| [[Electronic Signatures]] | Odoo Sign integration, approval workflows | Active |
| [[Knowledge Architecture]] | Obsidian → Odoo Knowledge sync, article structure | Active |
| [[Spec Approvals]] | Specification approval workflows | Active |
| [[FSC Certification & Compliance]] | FSC chain-of-custody, certification tracking | Active |
| [[Project Management (EXCO & Hypercare)]] | VVF PM module installed at Kebony — CEO dashboard + hypercare tickets | Pointer |
| [[Localized Send Framework]] | Entity-specific document sending (email templates, attachments) | Active |

---

## 03 - Manufacturing

End-to-end manufacturing documentation, from conceptual landscape to Odoo implementation.

| Document | Scope | Status |
|---|---|---|
| [[Manufacturing Landscape]] | Physical reality — species, flows, QC gates, capacity | Frozen |
| [[Implementation White Paper]] | Odoo 19 translation — BoM, WC, costing, accounting | Frozen |
| [[Dryer-Centric Architecture]] | DL -> AC -> PP object hierarchy | Frozen |
| [[Planning Considerations]] | Planning primitives, capacity model, families | Frozen |
| [[Workflow Diagrams]] | Mermaid diagrams (A4 portrait), MES traceability | Active |
| [[Stock & Lot Enrichment]] | Inventory enrichment — cubic, capacity, traceability | Frozen |
| [[Costing Architecture & COGS Decomposition]] | Standard vs FIFO, COGS decomposition, RDK settlement, Belgian PCMN | Decision Pending |
| [[RAP MPS - Current Replenishment Logic]] | Current replenishment/MPS logic analysis | Active |

---

## 04 - US Specific

US-only features for Kebony Inc. — accounting, accruals, margin, consignment.
**Company scope**: `x_kebony_entity_type == 'inc'`

| Document | Scope | Status |
|---|---|---|
| [[Accounting & Margin Architecture]] | FIFO, chart of accounts, accruals, margin, COGS, landed costs, journal map, month-end close | Active |
| [[Consignment & Biewer]] | Consignment stock, blank valuation, Biewer PO generation, pricing table | Active |
| [[Landed Cost Automation]] | Automated landed cost allocation for US imports | Active |
| [[Sales & Cash Dashboard]] | Sales & cash collection dashboard | Active |
| [[Prepayment Flag]] | Prepayment invoice detection and handling | Active |
| [[Reception BOL & Inbound Logistics]] | Inbound BOL processing, reception workflows | Active |

---

## 05 - Working Plan

Implementation phasing and step-by-step delivery plan.

- [[Working Plan]] — Step-by-step phase delivery (Phases 1-9)
- [[Backlog]] — Living checklist: bugs, tech debt, feature requests, deferred decisions

---

## 06 - Slide Decks

Auto-generated HTML presentations derived from vault documents. **Never edit directly** — regenerate from source.

| Deck | Source | Audience |
|------|--------|----------|
| `costing_architecture.html` | [[Costing Architecture & COGS Decomposition]] | CFO / Finance |
| `vvf_budget.html` | Budget data (standalone) | Board / Management |
| `vvf_it_opex.html` | IT run rate data (standalone) | Board / Management |

See [[06 - Slide Decks/README]] for conventions and workflow.

---

## 07 - Validation

Test plans, validation reports, and proposed change documents.

| Document | Scope | Status |
|---|---|---|
| Accrual Engine - Proposed Changes v1.html | Accrual engine redesign validation | Active |

---

## Cross-Reference: Key Odoo Models

| Model | Module | Purpose |
|---|---|---|
| `product.template` | core | Operational product entity (NOT product.product) |
| `sale.order` / `.line` | bol_report | Pack reservation, aggregate metrics |
| `account.move` / `.line` | bol_report | Margin, accruals, COGS, metrics |
| `stock.move` / `.line` | bol_report | Full-pack-first, pack-wish enforcement |
| `stock.lot` | bol_report | Lot reservation, cost, MES refs |
| `kebony.planning.family` | manufacturing | Planning families (11) |
| `kebony.dryer.load` | manufacturing | DL -> AC -> PP hierarchy |
| `kebony.accounting.hub` | bol_report | EOM accruals, consignment PO |
| `kebony.metrics.mixin` | bol_report | Shared calculation layer |
