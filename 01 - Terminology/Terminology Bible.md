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
| Manufacturing (DL, AC, PP) | BNV (Kallo production site) |
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
| **Process Pack** | A stacking output — boards grouped for autoclave | `kebony.process.pack` |
| **Finished Good Pack** | Sellable pack after exit stacking + packaging | `stock.lot` |
| **Pack selection** | The "pick this specific lot" feature on SO | `stock.lot.x_reserved_sale_order_id` |

Always qualify which "pack" you mean.

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
| **Dryer Load (DL)** | The atomic planning unit. 1 DL = 2 Autoclave Batches. Blocks one dryer for full cycle (up to ~80h). |
| **Autoclave Batch (AC)** | An intermediate feeder unit. Typically 5-8 Process Packs of the same family. |
| **Process Pack (PP)** | Smallest physical unit through production. Created during entry stacking. Homogeneous by planning family. |
| **Finished Good Pack (FG Pack)** | Sellable pack created during exit stacking. Gets a lot number. |
| **Entry Stacking** | Board-by-board sorting into Process Packs. Primary QC gate (A / B / Scrap). |
| **Exit Stacking (Destacking)** | Board-by-board restacking into FG Packs. Same QC gate. Packaging materials consumed. |
| **Kebonisation** | The full treatment process: stacking + autoclave + dryer + destacking. |
| **Ready-Mix** | Pre-mixed chemical used by autoclave. One recipe for all production. |
| **RDK** | External machining subcontractor (profiling, planing, cut-to-length). |
| **TabakNatie (TBK)** | External 3PL for reception and QC. |
| **MES** | Manufacturing Execution System — captures physical reality (cycle times, QC, quantities). |

### MO Grouping Rule

One Manufacturing Order per **product** per **Dryer Load**. Process Packs of the same product within a DL are clubbed into a single MO. An MO can consume multiple PPs.

### MES Traceability References

Each planning entity carries a reference number from MES:
- Dryer Load → `kebony_mes_drier_ref`
- Autoclave Batch → `kebony_mes_autoclave_ref`
- Process Pack → `kebony_mes_process_pack_ref`

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
