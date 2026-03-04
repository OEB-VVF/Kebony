# Kebony — Documentation Index

> Single entry point for all Kebony Odoo 19 documentation.
> Updated: 2026-02-27

---

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
| [[Analytical Accounting Architecture]] | 3 analytic plans (Country, BU, CM Level), allocation rules, P&L waterfall | White Paper |

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

---

## 04 - US Specific

US-only features for Kebony Inc. — accounting, accruals, margin, consignment.
**Company scope**: `x_kebony_entity_type == 'inc'`

| Document | Scope | Status |
|---|---|---|
| [[Accounting & Margin Architecture]] | FIFO, chart of accounts, accruals, margin, COGS, landed costs, journal map, month-end close | Active |
| [[Consignment & Biewer]] | Consignment stock, blank valuation, Biewer PO generation, pricing table | Active |

---

## 05 - Working Plan

Implementation phasing and step-by-step delivery plan.

- [[Working Plan]] — Step-by-step phase delivery (Phases 1-9)
- [[Backlog]] — Living checklist: bugs, tech debt, feature requests, deferred decisions

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
