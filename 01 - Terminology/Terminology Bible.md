# Kebony Terminology Bible

> The shared language reference. When we say X, we mean exactly this.
> If something is ambiguous, it should be defined here.

---

## 0. Company Structure

Kebony operates as a **multi-company** group. Features in the codebase are company-scoped via `x_kebony_entity_type` on `res.company`.

### Entities & Short Names

| Short Name | Legal Name | Code | Country | Type | Status |
|---|---|---|---|---|---|
| **INC** | Kebony Inc. | `inc` | USA | Operating | **Active** |
| **Holding** | Kebony Holding | `holding` | Belgium | Holding | Active |
| **BNV** | Kebony BNV | `bnv` | Belgium | Operating | **Active** |
| **KAS** | Kebony KAS | `kas` | Norway | Holding | **Being dissolved** |
| **NAS** | Kebony Norge AS | `nas` | Norway | Operating | Active (limited) |

> When referring to an entity in code, documentation, or conversation, use the **short name** (INC, Holding, BNV, KAS, NAS).
> Full detail (address, VAT, registration) → see [[Entity Registry]].

### Feature Scope by Entity

**INC only:**

| Feature | Code gate |
|---|---|
| Accrual Logic (US) | `company._is_kebony_us()` |
| Margin Calculation (US) | `company._is_kebony_us()` |
| Biewer Consignment | `company._is_kebony_us()` |
| Invoice / BOL / Quotation US Reports | Report labels "(US)" |
| "Distributor" customer category | US accrual context |
| Sales Rep Commission | US accrual context |
| Contact Studio fields (US-specific) | Pending contextualisation |

**All entities:**

| Feature | Notes |
|---|---|
| Physical metrics (linear m, boards, volume m3) | Wood is wood everywhere |
| Pack reservation / Full-pack-first | Operational feature |
| Manufacturing (Process Pack: SA → AA → DA → FA) | BNV (Kallo production site) |
| Accounting Hub | Per-company — each gets its own Hub |

### Pending Actions

| Item | Status | Owner |
|---|---|---|
| Entity addresses, VAT, registration numbers | **Waiting** | Finance/legal team → [[Entity Registry]] |
| US analytical accounts list | **Waiting** | User to provide |
| US customer classification values | **Waiting** | User to provide |
| Contact screen — list of US-only Studio fields | **Waiting** | User to provide |
| Belgian accrual rules (if any) | **To define** | |
| Belgian reporting templates | **To define** | |
| Intercompany transaction model (BNV → INC) | **To define** | |
| KAS dissolution plan | **To define** | |

---

## 1. Product Hierarchy

### Profile

A **cross-section**: a unique combination of shape (T&G, shiplap, square-edge...) and nominal dimensions (thickness x width). A profile does NOT include length.

- Example: `1931` = 1" x 6" Tongue & Groove, Character
- A profile can exist in multiple lengths and measurement systems
- Odoo: not a standalone record — it is an attribute of the product template

### SKU (Stock Keeping Unit)

A **unique sellable product**: Profile + Length + Measurement System. One SKU = one `product.template` in Odoo.

- Example: `1931-I-10` = Profile 1931, Imperial (I), 10 feet
- Example: `1931-M-3` = Profile 1931, Metric (M), 3 meters
- A SKU has exactly one base UoM, one set of packaging definitions, one set of physical dimensions
- Odoo: `product.template` (NOT `product.product` — see Architecture Principle below)

### Lot / Pack

A **physical batch** of a single SKU. Created at reception (raw) or production (finished).

- Example: `LOT-2024-0453` = 48 boards of SKU 1931-I-10
- Multiple lots can exist for the same SKU
- A lot carries: cost, quantity, location, traceability chain, QC grade
- Odoo: `stock.lot`

### Pack (disambiguation)

"Pack" means different things depending on context:

| Context | Meaning | Odoo |
|---|---|---|
| **Packaging UoM** | A unit of measure (e.g. "Pack of 48 boards x 10 lf") | `uom.uom` |
| **White wood pack** | Supplier pack at reception — stays on supplier's license plate | `stock.lot` (supplier-provided) |
| **Process Pack** | Generic WIP pack umbrella — any in-flight production pack carrying a stage label (SA / AA / DA) | `kebony.process.pack` |
| **Finished Good Pack (FA)** | Sellable pack after destacking + packaging | `stock.lot` on the FG product |
| **Pack selection** | The "pick this specific lot" feature on SO | `stock.lot.x_reserved_sale_order_id` |

Always qualify which "pack" you mean.

**Key clarification:**
- **White wood** is *not* a Process Pack — it is the supplier's pack, received as-is with the supplier's license plate. There is no "RA" label in the internal chain.
- **FA** is *not* a Process Pack either — once destacking produces a finished pack, it leaves the `kebony.process.pack` model and becomes a `stock.lot` on the finished good.
- **SA / AA / DA** are stages of the *same* Process Pack record as it evolves through production.

### Planning Family

A **group of SKUs** that share manufacturing parameters (species, impregnation profile, drying profile, dimension class). Only products in the same family can be processed together in an autoclave or dryer load.

- Example: `KSP 1"` = all 1" Scots Pine Character profiles
- 11 families currently defined
- Odoo: `kebony.planning.family`

### Product Template vs Product Variant

| Concept | Odoo model | Kebony usage |
|---|---|---|
| **Product Template** | `product.template` | = the SKU. One per sellable product. This is the operational entity. |
| **Product Variant** | `product.product` | NOT used for dimensional variants. Only 1 variant per template (the default). |

**Why?** In Odoo 19, packaging UoMs are shared across all variants of a template. Since each SKU needs its own packaging (e.g. "Pack of 48 boards of 10 lf" vs "Pack of 36 boards of 12 lf"), variants cannot be used. Each dimensional product is its own template.

---

## 2. Naming Convention

### SKU Code Structure

```
[Profile Number] - [System] - [Length]

  1931          -    I     -   10
  |                  |          |
  Profile            Imperial   10 feet
  (shape x dim)      or M
```

- `I` = Imperial (feet)
- `M` = Metric (meters)
- Profile number is assigned by Kebony product management

### Master Item vs Master Variant

| Term | Field | Meaning |
|---|---|---|
| **Master Item Code** | `x_master_item_code` | Groups all lengths and systems of the same profile (e.g. all variants of profile 1931) |
| **Master Variant Code** | `x_master_variant_code` | Groups within a dimension class (e.g. all 1931 in Imperial) |
| **Is Master Item** | `x_is_master_item` | Boolean flag — the "reference" product for this profile group |
| **Is Master Variant** | `x_is_master_variant` | Boolean flag — the "reference" for this variant group |

---

## 3. Units of Measure

### Operational vs Economic

| Dimension | Unit | Purpose |
|---|---|---|
| **Operational** | Linear meter (m) or Linear foot (lf) | Handling, sales, stock management |
| **Economic** | Cubic meter (m3) | Costing, margin, KPI, profitability |
| **Informational** | Board count | Logistics, packaging, warehouse ops |
| **Commercial** | Square meter (m2) | Coverage, architecture projects |
| **Capacity** | Dryer hours | Bottleneck economics, planning |

### Volume: Two Fields, Two Purposes

| Field | Unit | Purpose | Used in |
|---|---|---|---|
| `x_studio_volume_m3` | m3/lm (always metric) | **Normalised** volume ratio. Used for ALL economic calculations. | Metrics mixin, margin, KPIs |
| `volume` (Odoo standard) | m3/lm (metric) or ft3/lf (imperial) | **Localised** volume. Depends on product measurement system. | Transport docs, supply chain |

**Rule:** Never use `volume` for economic calculations. Always use `x_studio_volume_m3`.

### Linear: Internal Normalisation

All linear quantities in the codebase are **normalised to meters** internally via `KebonyMetricsMixin._kebony_linear_qty_in_m()`. Input can be in any UoM (feet, meters, packs) — the mixin handles conversion.

### Board Count

Board count = `linear_meters / length_per_board_m`. Uses the **0.95 fractional round-up rule**: if the fractional part > 0.95, round up to next whole board.

---

## 4. Product Classification

### Wood vs Accessory

Products carry a `x_studio_product_classification` many2many field with values:

| Classification | Examples | Metrics? | Accruals? |
|---|---|---|---|
| **wood** | Decking boards, cladding, structural timber | Yes (linear m, boards, volume m3) | Marketing 4%, Royalties 5%, Mgmt fees 14% |
| **accessory** | Screws, clips, fasteners, oils | No (0 for all physical metrics) | Marketing 1.5%, Royalties 5%, Mgmt fees 14% |

**Key rule:** Physical metrics (linear meters, boards, volume) are only meaningful for **wood** products. Accessories get 0.

### Customer Category

`x_studio_customer_catagory` (typo intentional — Studio field):
- `"Distributor"` — eligible for marketing accrual
- Other — no marketing accrual

### Consignment

Products in category `"Product in Consignment"`:
- COGS from `stock.consignment.price` table (not from stock valuation)
- NO royalties, NO management fees
- Biewer PO generation applies

---

## 5. Manufacturing Terms

| Term | Definition |
|---|---|
| **White wood** | Raw wood received from supplier, kept on supplier's license plate. Not a Process Pack. No internal "RA" label — the supplier's identifier is the reference. |
| **Process Pack (PP)** | **Generic WIP pack** umbrella. One `kebony.process.pack` record carries a stable `pack_number` and a `stage` field (SA → AA → DA) that evolves through production. Packs stay 1:1 all the way through — no merge at the pack level. |
| **Stacking Antwerp (SA)** | Stage label of a Process Pack right after stacking. N white-wood plates → 1 SA. |
| **Autoclave Antwerp (AA)** | Stage label of the *same* Process Pack after autoclave. 1 SA → 1 AA (1:1 state change — same `pack_number`). |
| **Dryer Antwerp (DA)** | Stage label of the *same* Process Pack after drying. 1 AA → 1 DA (1:1 state change — same `pack_number`). |
| **Finished Good (FA)** | Sellable pack after destacking. Leaves the Process Pack model — becomes a `stock.lot` on the FG product. 1 DA → N FA (destacking splits per SKU). |
| **Autoclave Load (Autoclave Batch)** | Physical autoclave charge grouping N packs processed together (SA → AA). Its own number. `kebony.autoclave.batch`. |
| **Dryer Run (Dryer Load)** | Physical dryer run grouping ~2 autoclave loads of packs processed together (AA → DA). Its own number. `kebony.dryer.load`. |
| **Entry Stacking** | Board-by-board sorting into Process Packs (SA stage). Primary QC gate (A / B / Scrap). |
| **Exit Stacking (Destacking)** | Board-by-board restacking of DA output into FA (FG lots). Same QC gate. Packaging materials consumed. |
| **Kebonisation** | The full treatment process: stacking + autoclave + dryer + destacking (SA → AA → DA → FA). |
| **Ready-Mix** | Pre-mixed chemical used by autoclave. One recipe for all production. |
| **RDK** | External machining subcontractor (profiling, planing, cut-to-length). |
| **TabakNatie (TBK)** | External 3PL for reception and QC. |
| **MES** | Manufacturing Execution System — captures physical reality (cycle times, QC, quantities). |

### Display Name Convention

A Process Pack has one stable internal `pack_number` and a `stage` field. Its display name is computed as `{stage}-{pack_number}` — e.g. the same pack appears as `SA-1234` at stacking, then `AA-1234` post-autoclave, then `DA-1234` post-dryer. The pack number is stable end-to-end; only the stage letter changes.

### Process Pack Data Model

| Model | Purpose |
|---|---|
| `kebony.process.pack` | One row per individual WIP pack. Fields: `pack_number` (stable across SA/AA/DA), `stage` (SA / AA / DA), `autoclave_batch_id` (M2o → autoclave load), `dryer_load_id` (M2o → dryer run), `mes_ref`. |
| `kebony.autoclave.batch` | One row per physical autoclave load. Groups N packs that went through together. Its own sequence number. Fields: `name`, `packs` (O2m to process.pack), `dryer_load_id` (the dryer run it was routed to). |
| `kebony.dryer.load` | One row per physical dryer run. Groups ~2 autoclave loads (so ~2N packs). Its own sequence number. Fields: `name`, `autoclave_batch_ids` (O2m), `packs` (through autoclave_batch_ids). |
| `kebony.process.pack.event` | Child of process.pack — one row per stage transition. Fields: `pack_id`, `stage`, `event_type` (stacked / autoclave_in / autoclave_out / dryer_in / dryer_out / destacked), `timestamp`, `operator_id`, `equipment_id` (specific autoclave #, dryer #), `mes_ref`. Enables residence-time and equipment-utilisation reporting. |

**No pack-level merge.** Packs are 1:1 from SA to DA. The "2 → 1" that happens at the dryer is a **container-level grouping**: 2 autoclave batches are assigned to 1 dryer run; the packs inside simply carry `dryer_load_id` pointing to that run.

**Split (1 DA → N FA):** the DA pack closes (event `destacked`), N `stock.lot` records are created on the FG product. Traceability runs via MO consumption links.

### Planning Direction — Backward from FA

Planning is **backward from the finished pack** (FA), using scrap yield:

1. Start with the FG demand (number of boards per SKU)
2. Compute target SA board count: `SA = ceil(FA × scrap_yield_factor)` — always round **up**, never down
3. Planner requests white-wood plates closest to but ≥ the target
4. **Stacking machine stops at the exact board count**; excess boards return to the raw-material warehouse

SA is therefore always equal to or higher than the strict yield-derived minimum — the physical constraint is the supplier plate granularity.

### MO Grouping Rule

One Manufacturing Order per **product** per **Dryer Run** (`kebony.dryer.load`). Process Packs of the same product within a dryer run are clubbed into a single MO. An MO can consume multiple packs.

### MES Traceability References

Each pack carries a reference number from MES:
- Process Pack (SA / AA / DA stages) → `kebony_mes_process_pack_ref` (renamed on MES side too to reflect the stage)
- Historical legacy names: `kebony_mes_drier_ref`, `kebony_mes_autoclave_ref` — retained on the model for backward compatibility, deprecated in favour of the unified reference

### MES Interface Contract (source: SIS_MES_Axapta_Summary v0.1)

The shared `MES_ERP_Mailbox` database has two schemas: `ERP.*` (ERP → MES) and `MES.*` (MES → ERP).

**Operation codes** emitted by MES on `MES_ProducedPackage`:

| Code | Step | Odoo event_type |
|---|---|---|
| **10** | Stacking | `stacked` |
| **23** | Charging (Autoclave) | `autoclave_in` / `autoclave_out` |
| **26** | Drying | `dryer_in` / `dryer_out` |
| **30** | De-stacking | `destacked` |

**Quality codes** (produced packages only — NOT used on raw material consumption):
- `Quality = 3` → scrap (explicit in spec)
- `Quality = 1 / 2` → presumably prime / secondary (confirm with SIS)

**Package identifiers:**
- Raw material / white wood: `RawMaterialPackageIdent` (supplier plate, e.g. `TS749697`)
- Per-step MES output: `ProducedPackageIdent` (MES-assigned, one per operation step)

**Deactivation flags** (ERP-side, block the record in MES):
- Article: `ClosedInAx = 1`
- Raw package: `Blocked = 1`
- Inventory: `InventStatus = 1` or `Amount = 0`

**Mandatory product field for MES:**
- `LengthUnit` in `ERP_Konf_DataDefinition` — required for running-meter computation from PLC board counters. Maps to `x_studio_length_m` on `product.template`. All other custom fields in `ERP_Konf_DataDefinition` are reporting-only.

**Partial package mechanics:** MES can report "part loaded, part returned to raw storage" — validates the "stacking machine stops at exact count, excess to RM warehouse" rule.

**NOT in the interface contract:**
- Defect reason codes — live **inside MES only**. Aggregated to `Quality 1/2/3` when reported to ERP. The full reason catalogue (when shared by SIS) is seed data for the Odoo `quality.reason` table, not payload.

### Post-Kebonisation Machining Facility

- Kebony owns **1 autoclave** and **3 dryers** (Dryer 1 / 2 / 3) at Kallo. The 3 dryers must be planned separately (each has its own calendar / capacity) — see `kebony.dryer.load.dryer_id`.

---

## 6. Commercial / Accounting Terms

| Term | Definition |
|---|---|
| **Margin** | Net Sales - COGS - Accruals - Freight - Warehousing - Other Adjustments. Approximate, stored on invoice, no journal entry. |
| **COGS** | Cost of Goods Sold. Source depends on route: Stock (lot cost), Dropship (vendor bill), Consignment (price table). |
| **Accrual** | Provision for future cost. Computed per invoice line based on classification and rates. |
| **Marketing Accrual** | 4% wood / 1.5% accessory. Distributors only. |
| **Royalties** | 5% (wood or accessory). Not for consignment. |
| **Management Fees** | 14% (wood or accessory). Not for consignment. |
| **Sales Rep Commission** | Variable rate from `x_studio_sales_rep_rate` or `x_studio_sales_rep_commission`. |
| **EOM (End of Month)** | When accruals are posted as journal entries to GL. |
| **Freight** | Transport cost — user-entered on invoice header (`x_studio_freight_cost`). |
| **Warehousing** | Storage cost — user-entered on invoice header (`x_studio_warehousing_cost`). |
| **Credit Note** | Posted `out_refund` reversing original invoice. Deducted from net sales in margin. |
| **Dropship** | SO creates PO automatically. Goods ship directly from vendor to customer. |
| **Consignment** | Goods held by Biewer Lumber, LLC. Sold from their inventory, replenished via PO. |

---

## 7. Odoo Field Naming Convention

| Prefix | Origin | Governance |
|---|---|---|
| `x_studio_*` | Created via Odoo Studio | Treat as external/read-only definitions. Do not rename. |
| `x_kebony_*` | Native Python fields in `kebony_bol_report` | Maintained by development team. |
| `kebony_*` (no x_) | Fields in `kebony_manufacturing` | Newer naming standard. |
| (no prefix) | Standard Odoo fields | Do not modify. |

---

## 8. Species & Product Lines

| Species | Product Line | State at Reception | Post-Kebonisation |
|---|---|---|---|
| **Scots Pine** | Character | Pre-machined (planed, profiled). Ready for impregnation. | FG directly. Some may route to RDK for cut-to-length. |
| **Radiata Pine** | Clear | Rough-sawn lumber. | Routes to RDK for profiling and planing. |

---

*This document is a living reference. Update it when new terms are introduced or existing definitions need refinement.*

---

## Document History

| Date | Change |
|---|---|
| 2026-04-23 | Pack chain terminology clarified: RA removed (white wood stays on supplier plate); PA → AA (Autoclave Antwerp); SA / AA / DA are stages of the *same* Process Pack record with stable `pack_number`; FA is a FG `stock.lot`, not a Process Pack. Added display-name convention, data-model spec (Process Pack + autoclave batch + dryer load + stage-event log), backward-from-FA planning rule with stacking-machine exact-count + RM-warehouse return. |
| 2026-04-23 (same day, correction) | No pack-level merge between AA and DA — packs stay 1:1 from SA to DA. The 2-to-1 step is a container-level grouping on `kebony.dryer.load` (2 autoclave batches per dryer run), not a pack merge. |
| 2026-04-23 (same day, MES add) | Added MES interface contract section based on SIS_MES_Axapta_Summary v0.1: operation codes (10/23/26/30), Quality codes (1/2/3), package-identifier conventions, deactivation flags, `LengthUnit` as the one MES-mandatory product field, partial-package mechanics (validates backward-from-FA rule), and clarification that defect reasons are MES-internal (seed data for `quality.reason`, not interface payload). Also noted 1 autoclave + 3 dryers at Kallo — capacity planning per dryer. |
