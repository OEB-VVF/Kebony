# Product Master Data

> Version 2.0 — Strategic Architecture & Governance Reference
> Module: All | Updated: 2026-02-26

---

## 1. Executive Summary

The Product Master is the **single most critical data entity** in Kebony's Odoo 19 platform. Every business process — from sales quotation to manufacturing execution, from margin analysis to customs declaration — is anchored to the product record. A single field error on a product propagates across inventory valuation, costing, invoicing, logistics, and compliance.

This document is the **definitive reference** for:

- **What** a Kebony product is (identity, dimensions, classification)
- **What it drives** (the downstream impact on every functional domain)
- **How it is structured** in Odoo 19 (technical field names, types, values)
- **Who owns it** (governance, RACI, change control)

**Design principle**: Product Master Data is infrastructure. It must be treated with the same rigour as financial chart of accounts or manufacturing Bill of Materials. No field should be added, renamed, or repurposed without formal validation.

---

## 2. Why Product Matters — Downstream Impact Map

Every product record in Kebony's system feeds — directly or indirectly — into **13 functional domains**. A change to a single product attribute can cascade through all of them.

| # | Domain | What Product Drives |
|---|--------|-------------------|
| 1 | **Sales** | Quotation, pricing, packaging UoM |
| 2 | **Pricing** | Pricelist rules, price per lm / m² / m³ |
| 3 | **Inventory** | FIFO valuation, lot tracking, quant metrics |
| 4 | **Manufacturing** | BoM generation, dryer load planning, chemical mix |
| 5 | **Capacity Planning** | Dryer / autoclave scheduling, bottleneck analysis |
| 6 | **Costing & Margin** | Standard cost, COGS split, margin per m³ |
| 7 | **Accounting** | GL routing, analytic distribution, accruals |
| 8 | **Logistics** | Weight, pallet dims, transport planning |
| 9 | **Packaging** | Pack / Board UoMs, picking, shipping labels |
| 10 | **Compliance** | HS codes, intrastat, customs declarations |
| 11 | **Website** | Catalogue, filtering, search, display |
| 12 | **Purchasing** | Vendor bills, consignment, raw material linkage |
| 13 | **Samples** | Sample workflows, services available |

**The implication is clear**: a product record is not just a "catalogue entry" — it is a **load-bearing data structure** that underpins the financial, operational, and regulatory integrity of the entire platform.

---

## 3. Architecture Principle

### 3.1 No Dimensional Variants

Odoo 19 merged packaging and UoM into a single concept. A product sold as "Pack of 162 × 3.2 lm" and "Board of 3.2 lm" requires packaging-level UoMs that depend on the product's length. This makes dimensional variants structurally impossible.

**Rule**: Each dimensional product = its own `product.template`. No variant axes for length, width, or thickness.

### 3.2 Metric / Imperial Structural Separation

Metric and imperial products are **separate templates** linked by a shared Master Item Code and a Metric-Imperial Master Code. The metric product is the engineering source of truth; imperial equivalents derive from it.

| Concept | Metric Example | Imperial Equivalent |
|---------|---------------|-------------------|
| Name | `1127-M-3.2` | `1127-I-10.5` |
| Master Item Code | `1127` | `1127` |
| Master Variant Code | `1127-3.2` | `1127-2.74` |
| Metric-Imperial Master | `1127-M` | `1127-I` |
| UoM | m (meter) | LF (linear foot) |
| Company | Kebony Holding (BE) | Kebony Holding (BE) |

### 3.3 Treatment ≠ Variant

Treatment (fire retardant, colour finish, brushing) is applied post-production and tracked at **lot level only**. Product identity remains purely dimensional. This prevents combinatorial SKU explosion: each cross-section exists in ~20 length variants across metric and imperial, and each could carry up to 4 treatments — meaning ~70 cross-sections × ~20 lengths × 4 treatments × 2 measurement systems = **~11,200 potential SKUs** reduced to the current ~490 by keeping treatment at lot level and length as a structural product axis rather than a variant.

### 3.4 Three-Level Hierarchy

```
Master Item (e.g. 1127)
  └── Master Variant (e.g. 1127-3.2)
        ├── Metric Product (1127-M-3.2)  ← sellable, stockable
        └── Imperial Product (1127-I-10.5) ← sellable, stockable
```

- **Master Item** (`x_studio_is_master_item = True`): non-sellable, non-purchasable grouping record representing the cross-section (e.g., "Kebony Character Decking 28×120")
- **Master Variant** (`x_studio_is_master_variant = True`): non-sellable grouping by dimension (e.g., "1127-3.2" = 28×120 at 3.2m length)
- **Metric-Imperial Master** (`x_studio_product_family_1 = True`): links metric and imperial twins under one code (e.g., `1127-M`)
- **Sellable Product**: the actual stockable, sellable `product.template` (e.g., `1127-M-3.2`)

### 3.5 Product Population

| Segment | Metric | Imperial | Total |
|---------|--------|----------|-------|
| Character (Scots Pine) | 30 | ~30 | ~60 |
| Clear (Radiata) | 117 | 117 | ~234 |
| Master Items | ~70 | — | ~70 |
| Master Variants | ~80 | — | ~80 |
| Accessories | — | — | ~27 |
| Services / Other | — | — | ~20 |
| **Estimated Total** | | | **~490** |

---

## 4. Measurement Doctrine

### 4.1 Three Dimensions of Quantity

| Dimension | Unit | Display | Role |
|-----------|------|---------|------|
| **Linear** | meters (m) | m, lm, LF | Operational — normalised to meters |
| **Board count** | integer | boards | Informational — ROUND_UP at 0.95 |
| **Volume** | m³ | m³, ft³ | **Economic truth** — all KPIs in m³ |

### 4.2 Two Volume Fields — Critical Distinction

| Field | Technical Name | Unit | Usage |
|-------|---------------|------|-------|
| Normalised | `x_studio_volume_m3` | Always m³/lm | **Canonical.** All economic calcs. |
| Localised | `volume` (Odoo) | m³/lm or ft³/lf | Transport docs only. **Never for metrics.** |

**Formula**: `Total volume = linear_meters × x_studio_volume_m3`

### 4.3 Conversion Constants

```
FT_PER_M   = 3.280839895
M_PER_FT   = 1 / FT_PER_M
FT3_PER_M3 = 35.3146667
```

---

## 5. Complete Field Registry

### 5.1 Core Identity Fields

| # | Label | Technical Field | Type | Notes |
|---|-------|----------------|------|-------|
| 1 | Name | `name` | Char | `{Item}-{System}-{Length}` e.g. `1127-M-3.2` |
| 2 | Description | `x_studio_description` | Char | Full commercial name |
| 3 | Sales Description | `description_sale` | Text | Shown on quotations |
| 4 | Purchase Description | `description_purchase` | Text | Shown on POs |
| 5 | Master Item Code | `x_studio_master_item_code` | Char | Cross-section grouping: `1127` |
| 6 | Is Master Item? | `x_studio_is_master_item` | Boolean | `True` for grouping records |
| 7 | Master Variant Code | `x_studio_master_variant_code_1` | Char | Dimension grouping: `1127-3.2` |
| 8 | Is Master Variant? | `x_studio_is_master_variant` | Boolean | `True` for variant grouping |
| 9 | M-I Master Code | `x_studio_product_family` | Char | Links metric/imperial: `1127-M` |
| 10 | Is M-I Master? | `x_studio_product_family_1` | Boolean | `True` for M-I grouping |
| 11 | Measurement System | `x_studio_measurement_system` | Selection | `Metric` · `Imperial` |
| 12 | Unit of Measure | `uom_id` | Many2one | `m` (metric) or `LF` (imperial) |
| 13 | Company | `company_id` | Many2one | Kebony Holding for wood |
| 14 | Product Category | `categ_id` | Many2one | GL routing (see §5.10) |
| 15 | Product Type | `type` | Selection | `Goods` · `Service` · `Combo` |
| 16 | Lot Tracking | `tracking` | Selection | `By lots` for all wood |
| 17 | Valuation by Lot | `lot_valuated` | Boolean | `True` — FIFO per lot |
| 18 | Track Inventory | `is_storable` | Boolean | `True` for stockable goods |

*Fields 1–4 are Odoo standard; fields 5–11 are Studio-defined; fields 12–18 are Odoo standard.*

### 5.2 Classification Fields

| # | Label | Technical Field | Type | Notes |
|---|-------|----------------|------|-------|
| 19 | Wood Species | `x_studio_word_species` | Selection | `Scots Pine` · `Radiata` · `N.A.` |
| 20 | Production Family | `x_studio_production_chain` | Selection | `Character` · `Clear` · `N.A.` |
| 21 | Application | `x_studio_many2one_field_3oj…` | Many2one | 7 values (see §6.3) |
| 22 | Shape | `x_studio_shape` | Many2one | 27 values (see §6.4) |
| 23 | Shape Value | `x_studio_many2one_field_6up…` | Many2one | 27 values (see §6.5) |
| 24 | Product Lifecycle | `x_studio_product_lifecycle` | Selection | 6 values (see §6.2) |
| 25 | Product Classification | `x_studio_product_classification` | M2M | `wood` · `accessory` |
| 26 | Special Treatment | `x_studio_special_treatment_applied` | Boolean | Chemically treated? |

*All classification fields are Studio-defined. Full technical names for #21 and #23: `x_studio_many2one_field_3oj_1jaj6o7st` (Application), `x_studio_many2one_field_6up_1jaj7h762` (Shape Value).*

### 5.3 Technical Geometry — Metric (Engineering Base)

All derived fields must be reproducible from the **four base dimensions**: length, thickness, width, density.

| # | Label | Technical Field | Unit |
|---|-------|----------------|------|
| 27 | Length | `x_studio_length_m` | m |
| 28 | Thickness | `x_studio_thickness_mm` | mm |
| 29 | Width | `x_studio_width_mm_1` | mm |
| 30 | Volume (normalised) | `x_studio_volume_m3` | m³/lm |
| 31 | Weight | `x_studio_weight_kg` | kg |
| 32 | Density | `x_studio_density_kgm3_2` | kg/m³ |
| 33 | Square Factor | `x_studio_square_factor_1` | lm/m² |
| 34 | Section m² | `x_studio_width_x_thickness_m2_1` | m² |
| 35 | lm per m³ | `x_studio_number_of_lmm3_1` | lm/m³ |
| 36 | lm per m² | `x_studio_number_of_lmm2_1` | lm/m² |
| 37 | Weight per lm | `x_studio_net_weight_per_lm_kg_1` | kg/lm |
| 38 | Coverage | `x_studio_coverage_averaged_mm_2` | mm |

All fields are Float, Studio-defined. #30 is the **canonical volume ratio** (thickness × width). #27 is the **engineering source of truth** for length.

### 5.4 Technical Geometry — Imperial

Imperial values **derive from metric** or are independently controlled for US products. Same structural fields, different physical units.

| # | Label | Technical Field | Unit |
|---|-------|----------------|------|
| 39 | Length (LF) | `x_studio_length_1` | feet |
| 40 | Thickness | `x_studio_thickness` | inches |
| 41 | Width | `x_studio_width` | inches |
| 42 | Volume (localised) | `volume` | ft³/lf |
| 43 | Weight | `weight` | lb |
| 44 | Density | `x_studio_density_lbft3` | lb/ft³ |
| 45 | Square Factor | `x_studio_square_factor` | lf/ft² |
| 46 | Section ft² | `x_studio_width_x_thickness_m2` | ft² |
| 47 | LF per ft³ | `x_studio_number_of_lmm3` | lf/ft³ |
| 48 | LF per ft² | `x_studio_number_of_lmm2` | lf/ft² |
| 49 | Weight per LF | `x_studio_net_weight_per_lm_kg` | lb/lf |
| 50 | Coverage | `x_studio_coverage_averaged_mm_3` | inches |
| 51 | Pallet Height | `x_studio_pallet_height_in` | inches |
| 52 | Pallet Width | `x_studio_pallet_width_in` | inches |

All fields are Float, Studio-defined.

### 5.5 Packaging Intelligence

| # | Label | Technical Field | Type |
|---|-------|----------------|------|
| 53 | Boards per Pack | `x_studio_boards_per_pack` | Integer |
| 54 | Pcs per Layer | `x_studio_pcslayer` | Integer |
| 55 | Number of Layers | `x_studio_number_of_layers_1` | Integer |
| 56 | Pallet Height (cm) | `x_studio_pallet_height_cm_1` | Float |
| 57 | Pallet Width (cm) | `x_studio_pallet_width_cm_1` | Float |
| 58 | Items per Strap | `x_studio_itemsstrap` | Char |
| 59 | End-Matched | `x_studio_end_matched` | Selection |
| 60 | Install. Orientation | `x_studio_installation_orientation` | Selection |
| 61 | Packagings (UoMs) | `uom_ids` | M2M |
| 62 | Board of | (packaging record) | Float |
| 63 | Pack of | (packaging record) | Float |

Values — #59: `End-matched` · `End-cut` · `N.A.` | #60: `Horizontal` · `Vertical` · `Vertical, Horizontal` · `N.A.` | #61 example: `m, Board of 3.2 lm, Pack of 162 × 3.2 lm`

### 5.6 Supply Chain & Replenishment

| # | Label | Technical Field | Type |
|---|-------|----------------|------|
| 64 | Rough Sawn Parent | `x_studio_rough_sawn_parent_id_3` | M2O |
| 65 | Raw Material Origin | `x_studio_raw_material_origin_id_3` | M2O |
| 66 | Supply Chain Rule | *(to be created)* | Selection |

#64 links finished product → raw material parent. #65 links to white wood origin. #66 drives replenishment route and lead time (see §5.6.1).

#### 5.6.1 Supply Chain Rules

The **Supply Chain Rule** attribute determines the replenishment strategy, route configuration, and commercial lead time for each product. Four values:

| Rule | Stocking Point | Trigger | Lead Time |
|------|---------------|---------|-----------|
| **Make to Order** | None | Min. process batch reached | Full: procurement + production + transport |
| **ATO — White Wood** | White wood (untreated) | Min. white wood stock level | Production + transport |
| **ATO — Brown Wood** | Radiata rough sawn (treated) | Min. brown wood stock level | Machining + transport |
| **Make to Stock** | Finished goods | Min. FG stock level breach | Transport only |

**Make to Order (MTO)**
- No buffer stock held. Raw material ordered when a minimum process batch volume is accumulated from demand.
- Commercial lead time = longest chain (procurement + full production cycle + transport to customer).
- Replenishment rule: TBD — awaiting definition of minimum process batch trigger logic.

**Assemble to Order — White Wood (ATO-WW)**
- Buffer stock of **white wood** (untreated timber, e.g., white Radiata, white Scots Pine) is maintained at a minimum level.
- When a customer order arrives, production starts from the white wood stage (autoclave → dryer → machining).
- Commercial lead time = production cycle + transport.
- Min stock level driven by safety stock parameters on the white wood product.

**Assemble to Order — Brown Wood (ATO-BW)**
- Buffer stock of **brown wood** (treated rough sawn, e.g., Radiata rough sawn after autoclave + dryer, before machining) is maintained.
- When a customer order arrives, only **machining** is needed to produce the finished good.
- Commercial lead time = machining + transport.
- Min stock level driven by safety stock parameters on the rough sawn product.
- Applicable primarily to Radiata products where machining is the final conversion step.

**Make to Stock (MTS)**
- **Finished goods** buffer stock maintained at a target level.
- Replenishment triggered when projected stock approaches the minimum threshold.
- Commercial lead time = transport only (goods are already finished and available).
- Most mature / high-volume products will operate in this mode.

#### 5.6.2 Route & Lead Time Architecture

```
MTO:   [Procurement] → [Stacking] → [Autoclave] → [Dryer] → [Machining] → [Transport]
                                                                              ↑ full lead time

ATO-WW:              [White Wood Buffer]
                        ↓ trigger
                     [Autoclave] → [Dryer] → [Machining] → [Transport]
                                                              ↑ production + transport

ATO-BW:                           [Brown Wood Buffer]
                                     ↓ trigger
                                  [Machining] → [Transport]
                                                   ↑ machining + transport

MTS:                                             [Finished Goods Buffer]
                                                    ↓ trigger
                                                 [Transport]
                                                    ↑ transport only
```

The supply chain rule is set **per product** because the same cross-section may follow different strategies depending on market maturity, volume, and lifecycle stage. A product can transition from MTO (introduction) → ATO → MTS (mature) as demand stabilises.

#### 5.6.3 Product → Supply Chain Rule Assignment

> **STATUS: AWAITING INPUT FROM COO**
> The per-product assignment of supply chain rules has not yet been provided. The table below is a placeholder structure. Once the COO delivers the mapping, each product row will be populated with its assigned rule and the corresponding safety stock / reorder parameters.

| Master Item Code | Product Name | SC Rule | Buffer Product | Min Stock | Reorder Trigger | Notes |
|------------------|-------------|---------|----------------|-----------|-----------------|-------|
| *KEB-RAD-…* | *(example)* | MTO / ATO-WW / ATO-BW / MTS | *(if applicable)* | *(qty)* | *(rule)* | |
| … | … | … | … | … | … | |

**Expected deliverables from COO:**

1. Complete list of active finished-good products with their assigned supply chain rule (MTO / ATO-WW / ATO-BW / MTS)
2. For ATO and MTS products: the buffer product reference (white wood / brown wood / FG) and minimum stock level
3. For MTO products: minimum process batch trigger definition
4. Any product-specific exceptions or phased roll-out plan

**Ref**: Backlog item — *"Supply Chain Rule assignment per product"*

### 5.7 Commercial & Market

| #   | Label                | Technical Field                 | Type      |
| --- | -------------------- | ------------------------------- | --------- |
| 67  | Market Portfolios    | `x_studio_market_portfolios`    | M2M       |
| 68  | Matching Accessories | `x_studio_matching_accessories` | M2M       |
| 69  | Services Available   | `x_studio_services_available`   | M2M       |
| 70  | Portfolio Length     | `x_studio_portfolio_length`     | Selection |
| 71  | Sale Enabled         | `sale_ok`                       | Boolean   |
| 72  | Purchase Enabled     | `purchase_ok`                   | Boolean   |

Values — #67: see §6.7 | #69: see §6.8 | #70: `Standard` (only value currently)

### 5.8 Compliance & Trade

| # | Label | Technical Field | Type |
|---|-------|----------------|------|
| 73 | HS Code | `hs_code` | Char |
| 74 | Commodity Code | `intrastat_code_id` | M2O |
| 75 | Origin of Goods | `country_of_origin` | Char |
| 76 | Country of Origin | `intrastat_origin_country_id` | M2O |
| 77 | Sales Taxes | `taxes_id` | M2M |
| 78 | Purchase Taxes | `supplier_taxes_id` | M2M |

Examples — #73: `44.09.1091` (NO format) | #74: `44091018` (EU Intrastat) | #77: `21%` (BE), `6.25%` (US)

### 5.9 Manufacturing & Planning Enrichment

These fields link products to the manufacturing process layer via the **Planning Family** model (`kebony.planning.family`). The planning family ID is the only editable field; all others are read-only related fields.

| # | Label | Technical Field | RO |
|---|-------|----------------|-----|
| 79 | Planning Family | `kebony_planning_family_id` | No |
| 80 | Stacking Hours | `kebony_family_stacking_hours_ref` | Yes |
| 81 | Autoclave Hours | `kebony_family_autoclave_hours_ref` | Yes |
| 82 | Dryer Hours | `kebony_family_dryer_hours_ref` | Yes |
| 83 | Dryer h/m³ | `kebony_family_capacity_weight` | Yes |
| 84 | Typical Load m³ | `kebony_family_typical_dryer_load_volume` | Yes |
| 85 | Min Process Qty | `kebony_family_minimum_process_qty` | Yes |
| 86 | Mix kg/m³ | `kebony_family_mix_consumption_per_m3` | Yes |
| 87 | Internal Scrap % | `kebony_family_scrap_internal_percent` | Yes |
| 88 | B-Grade Scrap % | `kebony_family_scrap_b_grade_percent` | Yes |

All Float. #79 is the only editable field (Many2one to `kebony.planning.family`). Fields #80–88 are related / readonly — inherited from the family record. #82 is the **bottleneck resource**.

### 5.10 Product Categories (Accounting Routing)

Product Category (`categ_id`) determines the GL account routing for inventory valuation, COGS, and revenue recognition.

| Category | Accounting Impact |
|----------|-------------------|
| Finished Product - Wood | FIFO valuation, standard COGS |
| Semi-Finished Product - Wood | WIP valuation |
| Raw Material - White Wood | Purchase → WIP conversion |
| Raw Material - Chemical | Consumed in BoM |
| Finished Product - Accessories | Separate COGS category |
| Product in Consignment | Consignment valuation rules |
| Sample Special / Standard | Sample cost tracking |
| Services | No inventory impact |
| Expenses | Expense category |
| Certificates | Service category |
| Deliveries | Logistics cost routing |
| Landed Costs | Cost adjustment layer |

### 5.11 Computed Stock Metric Fields

These fields are **not on the product master data import** — they are computed and stored by the codebase at runtime. Documented here for completeness.

**On `product.template`** (aggregated from internal-location quants):

| Field | Type | Stored |
|-------|------|--------|
| `x_studio_number_of_boards` | Integer | Yes |
| `x_studio_available_linear_foot` | Float | Yes |
| `x_kebony_volume_m3_on_hand` | Float | Yes |
| `x_kebony_available_packs` | Integer | Yes |

**On `product.template`** (from `kebony_manufacturing`):

| Field | Type | Stored |
|-------|------|--------|
| `kebony_boards_available` | Integer | No |
| `kebony_linear_meters_available` | Float | No |
| `kebony_cubic_meters_available` | Float | No |

---

## 6. Model Values — Reference Tables

### 6.1 Wood Species

| Value | Latin Name | Origin | Production Family |
|-------|-----------|--------|-------------------|
| Scots Pine | *Pinus sylvestris* | Sweden / Norway | Character |
| Radiata | *Pinus radiata* | New Zealand / Belgium | Clear |

*Note: `x_studio_word_species` — the field name contains a typo ("word" instead of "wood"). This is a Studio field and the typo is permanent.*

### 6.2 Product Lifecycle

| Value | Meaning | Sales Impact |
|-------|---------|-------------|
| **Introduction** | New product, limited availability | Restricted distribution |
| **Growth** | Scaling production | Active promotion |
| **Mature** | Established, full availability | Standard catalogue |
| **Decline** | Reducing demand | Phase-out planning |
| **Abandon** | Decided to discontinue | Sell remaining stock |
| **Decommissioned** | Fully retired | No sales, no purchase |

### 6.3 Application

| Value | Typical Products |
|-------|-----------------|
| Decking | Floor boards, boardwalk planks |
| Cladding | Wall profiles, façade boards |
| Construction | Structural beams, battens |
| Boardwalk | Heavy-duty outdoor planking |
| Roofing | Roof boards |
| Industrial | Non-standard / custom |
| N.A. | Raw materials, semi-finished |

### 6.4 Shape (27 Values)

Batten · Beam · Bevel Halflap · Bevel T&G · Comb Faced · Dekora T&G · Halflap · Melsom Slat · N.A. · Nickel Gap · Railing · Rectangular · Rectangular Click-In · Rectangular w Side Slits · Rhombus · Rhombus Click-In · Rhombus Tiga · Roof Board · Rough Sawn · Shiplap · Shiplap Click-In · Siding · Skewed Slat · StepClip · StepClip Startboard · T&G · Triple Batten

### 6.5 Shape Value (27 Values)

Profile geometry codes combining angle and slot configuration:

`1SL` · `1SLL` · `1SLR` · `2SL` · `3SL` · `45°` · `60°` · `60° 1SL` · `75°` · `75° 1SL` · `75° 1SLL` · `75° 1SLR` · `75° 2SL` · `75° 3SL` · `78°` · `78° 1SL` · `90°` · `90° 1SL` · `90° 1SLR` · `90° 2SL` · `C1` · `C2` · `C3` · `N.A.` · `R2` · `R3` · `R5`

### 6.6 Fixing Method (8 Values)

`[blank]` · Click-In · Nickel Gap · Side Slits · Dekora · Tiga · GRAD · CAMO

### 6.7 Market Portfolios

Export · France · Nordic · DACH · Benelux · United States

*Products can belong to multiple markets simultaneously (Many2many).*

### 6.8 Services Available

Fire retardant treatment · Color finish · Brushing · Polish · Shou sugi ban · Fine sawn

### 6.9 Coverage Values (mm)

53 · 65 · 78 · 80 · 103 · 105 · 110 · 127 · 128 · 130 · 132 · 135 · 138 · 153 · 172 · 175 · 177 · 185 · 198 · 100-105 · 125-130 · variable

---

## 7. Planning Family Model (`kebony.planning.family`)

The Planning Family is the **bridge between product and manufacturing**. It defines process compatibility and reference parameters for dryer-centric batch planning.

### 7.1 Model Fields

| Field | Type | Req. | Description |
|-------|------|------|-------------|
| `name` | Char | Yes | e.g. "Kebony Radiata 1-inch" |
| `code` | Char | Yes | e.g. `KR1`, `KSP1C` |
| `active` | Boolean | — | Default True |
| `sequence` | Integer | — | Display ordering |
| `family_type` | Selection | Yes | `radiata` · `scots_pine` · `other` |
| `stacking_hours_ref` | Float | — | Stacking hours |
| `autoclave_hours_ref` | Float | — | Autoclave hours |
| `dryer_hours_ref` | Float | — | **Dryer hours — bottleneck** |
| `capacity_weight` | Float | — | Dryer hours per m³ |
| `minimum_process_qty` | Float | — | Min. feasible batch (m³) |
| `typical_dryer_load_volume` | Float | — | Reference m³ per load |
| `mix_consumption_per_m3` | Float | — | Chemical mix (kg/m³) |
| `scrap_internal_percent` | Float | — | Internal scrap rate |
| `scrap_b_grade_percent` | Float | — | B-grade downgrade rate |
| `ready_mix_product_id` | M2O | — | Chemical product for BoM |
| `notes` | Text | — | Free text |

### 7.2 Family Inventory

| Code | Name | Type | Dryer | AC | Stack | h/m³ | Mix |
|------|------|------|-------|-----|-------|------|-----|
| KSP1C | SP 1" Cladding | SP | 55 | 3.5 | 3.5 | 1.34 | 230 |
| KSP15T | SP 1.5" T&G | SP | 55 | 3.5 | 3.5 | — | — |
| KSP2PD | SP 2" Decking | SP | 65 | 3.5 | 3.5 | 1.57 | 315 |
| KSP2C | SP 2" Cladding | SP | 65 | 3.5 | 3.5 | — | — |
| KSP2CON | SP 2" Construction | SP | 65 | 3.5 | 3.5 | — | — |
| KR1 | Radiata 1" | R | 54 | 4.5 | 4.5 | 1.18 | 676 |
| KR1CL | Radiata 1" Cladding | R | 54 | 4.5 | 4.5 | — | — |
| KR2 | Radiata 2" | R | 62 | 4.5 | 4.5 | 1.36 | 600 |
| KRRS1 | Radiata RS 1" | R | — | — | — | — | — |
| KRRS2 | Radiata RS 2" | R | — | — | — | — | — |
| KSPRUCE | Kebony Spruce | O | 30 | 3.5 | 3.5 | 0.77 | 40 |

*SP = Scots Pine, R = Radiata, O = Other. Dryer/AC/Stack in hours. h/m³ = dryer hours per m³. Mix = chemical consumption kg/m³. Scrap rates defined in model but not yet populated in seed data.*

*Note: Scrap rates are defined in the model but not yet populated in seed data — to be refined during Phase 6+ of manufacturing implementation.*

---

## 8. Accessory Products

Accessories (screws, clips, fixing systems) are a separate product family with their own lifecycle. They are linked to wood products via the `x_studio_matching_accessories` Many2many field.

| SKU | Description | Supplier |
|-----|------------|----------|
| 2734 | DUO Screw 5,5×50mm A4 600pcs | Eurotec |
| 2735 | DUO Screw 5,5×60mm A4 600pcs | Eurotec |
| 2736 | DUO Screw 5,5×70mm A4 600pcs | Eurotec |
| 2612 / 2680 / 2498 / 2497 | H-clip (various) | Eurotec |
| 2741 | Ventilation Profile | Fixing Group |
| 2742 | Supporting section for vent. profile | Fixing Group |
| 2728 | Distance band | Fixing Group |
| 2731 / 2732 | Decking Screw 5,5×50 200pcs | Fixing Group |
| 2763 | Tiga 2 Clip A4 100pcs | Fixing Group |
| 2762 | Tiga 2 Starter Clip A4 50pcs | Fixing Group |
| 2765 | Dekora Alu-Zink C4 Black 100pcs | Fixing Group |
| 2748 / 2749 / 2750 | RASK clip/rail systems | Karle & Rubner |
| 2565 / 2733 | CAMO Screws 316s | Kyocera-Senco |
| 2563 / 2562 | CAMO Tools | Kyocera-Senco |
| 2679 | End-sealing wax 375ml | Saicos |
| 2737 / 2738 / 2739 | ProPlug kits + drill bit | Starborne Industries |

---

## 9. HS Code & Trade Classification

Wood products are classified under harmonised commodity codes for customs and intrastat reporting.

| Product Type | HS (NO) | HS (EU) | Origin |
|-------------|---------|---------|--------|
| Radiata Rough Sawn | 44.07.1111 | 4407 11 90 90 | BE / NO |
| White Radiata RS | 44.07.1121 | 4407 11 90 90 | NZ |
| Radiata Machined | 44.09.1091 | 4409 10 18 00 | BE / DK |
| Character ≤48×48 | 44.09.1091 | 4409 10 18 00 | NO |
| Character Standard | 44.09.1092 | 4410 10 18 00 | NO |
| Character Shiplap | 44.09.1091 | 4409 10 18 00 | NO |
| White Scots Pine | 44.09.1091 | 4409 10 18 00 | SE |
| White SYP | 44.07.1121 | 4407 11 90 90 | US |

---

## 10. Traceability Doctrine

### 10.1 Lot-Level Identity

Each physical production batch receives a unique `stock.lot` record. The lot carries:

- Treatment information (fire retardant, colour finish, brushing)
- Metrics: linear meters, boards, volume (on hand / reserved / available)
- Pack reservation: link to reserved sales order
- Legacy fields: `x_studio_boards`, `x_studio_linear_feet`

### 10.2 Product ≠ Treatment

Treatment is a **post-production attribute** applied during or after the manufacturing process. It is **never** part of the product identity or SKU. This prevents combinatorial explosion and preserves the principle that product = dimensional specification.

### 10.3 FIFO Integrity

Odoo 19's lot-valuated FIFO ensures that each lot's cost is tracked independently. The product master data feeds the FIFO mechanism through:

- `lot_valuated = True` → per-lot cost tracking
- `tracking = 'lot'` → mandatory lot assignment
- Category → GL account routing for valuation

---

## 11. Metrics Computation Architecture

### 11.1 The Mixin: `kebony.metrics.mixin`

Abstract model inherited by: `stock.quant`, `stock.lot`, `stock.move`, `sale.order.line`, `account.move.line`, `product.template`.

Core methods:
- `_kebony_linear_qty_in_m(product, qty)` — normalise any quantity to meters
- `_kebony_boards_from_linear(linear_m, length_m)` — compute board count (ROUND_UP_THRESHOLD = 0.95)
- `_kebony_volume_m3(product, linear_m)` — compute volume using `x_studio_volume_m3`
- `_kebony_is_wood_product(product)` — check `x_studio_product_classification` for `"wood"`

### 11.2 Recompute Hierarchy

```
Level 1: stock.quant     ← source of truth
           ├→ stock.lot         (aggregate from internal quants)
           └→ product.template  (aggregate from internal quants)

Level 2: stock.move           (from move lines or demand qty)
         sale.order.line      (from SO line qty + UoM)
         account.move.line    (from invoice line qty + UoM)

Level 3: sale.order           (sum of order lines)
         account.move         (sum of invoice lines)
```

### 11.3 Wood-Only Rule

Physical metrics (linear m, boards, volume m³) are **only computed for wood products** (`x_studio_product_classification` contains `"wood"`). Accessories and services return 0 for all physical metrics.

---

## 12. Entity Type & Company Architecture

Products are shared across entities but features are gated by company type:

| Code | Company | Type | Features |
|------|---------|------|----------|
| `inc` | Kebony Inc. (US) | Distribution | BOL, accruals, margin, consignment |
| `holding` | Kebony Holding (BE) | Holding | Product master ownership |
| `bnv` | Kebony BNV (BE) | Manufacturing | Planning, BoM, manufacturing |
| `kas` | Kebony KAS (NO) | Legacy | Placeholder |
| `nas` | Kebony Norge AS (NO) | Legacy | Placeholder |

**Technical field**: `res.company.x_kebony_entity_type` (Selection)

**Key methods**: `_is_kebony_us()` returns True for INC, `_is_kebony_bnv()` returns True for BNV.

---

## 13. Governance Framework

### 13.1 The Master Data Guardian

**A Super Master Data Guardian must be nominated.** This person is the single point of accountability for product data integrity across the organisation.

**Role definition**:
- **Authority**: No product creation, modification, or decommissioning happens without the Guardian's explicit validation
- **Scope**: All entities, all product types, all fields marked as "governed"
- **Escalation**: Any field change that impacts accounting, manufacturing, or compliance requires Guardian sign-off
- **Cadence**: Weekly review of pending changes, monthly audit of data quality

**Why this matters**: A single incorrect volume ratio (`x_studio_volume_m3`) on a high-volume product can silently distort margin calculations across hundreds of invoices before detection. A wrong HS code triggers customs penalties. A missing planning family breaks manufacturing scheduling. Product data errors are **silent, compounding, and expensive**.

### 13.2 RACI Matrix

| Field Family | R | A | C | I |
|-------------|---|---|---|---|
| **Identity** | MDG | COO | Sales, Prod. | All |
| **Geometry — Metric** | CTO | MDG | Production | Finance |
| **Geometry — Imperial** | CTO | MDG | US Sales | Finance |
| **Packaging** | Prod. Planning | MDG | Logistics | Sales |
| **Classification** | Product Mgmt | MDG | Eng., Sales | Marketing |
| **Lifecycle** | Product Mgmt | MDG | Sales, Finance | All |
| **Commercial** | Sales Mgmt | MDG | Marketing | Operations |
| **Compliance** | Finance / Trade | MDG | Legal | Operations |
| **Manufacturing** | Prod. Planning | MDG | Engineering | Finance |
| **Pricing** | Finance | CFO | Sales | MDG |

*MDG = Master Data Guardian. R = Responsible, A = Accountable, C = Consulted, I = Informed.*

### 13.3 Change Control Process

```
1. REQUEST    → Change request submitted (Jira / email) with:
                - Field(s) to change
                - Current value → proposed value
                - Business justification
                - Impact assessment (which domains affected?)

2. REVIEW     → Master Data Guardian evaluates:
                - Cross-domain impact (see §2 impact map)
                - Financial impact (margin, valuation, tax)
                - Operational impact (warehouse, manufacturing)

3. APPROVE    → Guardian signs off (or escalates to CFO/COO)

4. EXECUTE    → Change applied in Odoo (Studio or code deployment)

5. VALIDATE   → Post-change verification:
                - Metrics recompute correctly?
                - Existing orders/invoices unaffected?
                - Manufacturing planning intact?

6. DOCUMENT   → Change logged in product change register
```

### 13.4 Critical Rules

1. **No bulk updates without Guardian approval** — mass imports must be validated row-by-row against the field registry
2. **No Studio field creation without documentation** — every `x_studio_*` field must be documented in this registry before creation
3. **No field renaming** — Studio fields cannot be renamed after creation (Odoo limitation). Plan names carefully.
4. **Metric fields are read-only for non-Engineering** — volume, density, section area must only be modified by Engineering with Guardian sign-off
5. **Lifecycle transitions are one-way** — a product cannot move from Decommissioned back to Mature without executive approval
6. **Imperial derives from Metric** — imperial geometry values must be mathematically consistent with metric base values

---

## 14. Development Rules

### 14.1 Code Architecture

- **No duplicate logic**: All metric computations centralised in `KebonyMetricsMixin`
- **Studio fields documented exactly as named**: The typos in `x_studio_word_species` and `x_studio_customer_catagory` are permanent — never create "corrected" aliases
- **No hidden logic**: All derived fields must be reproducible from base geometry using documented formulas
- **All computed fields must declare dependencies**: Odoo's ORM compute framework requires explicit `@api.depends` declarations

### 14.2 Field Naming Convention

| Pattern | Origin | Rule |
|---------|--------|------|
| `x_studio_*` | Odoo Studio | Read-only in code |
| `x_kebony_*` | Python (bol_report) | Native codebase field |
| `kebony_*` | Python (manufacturing) | Newer naming standard |
| Standard Odoo | Core (`name`, `categ_id`) | Follow Odoo conventions |

### 14.3 Formula Reference

| Derived Field | Formula |
|--------------|---------|
| Volume (m³/lm) | thickness(m) × width(m) |
| Section m² | thickness(m) × width(m) |
| lm per m³ | 1 / `x_studio_volume_m3` |
| lm per m² | 1 / width(m) |
| Weight per lm | density × volume(m³/lm) |
| Boards | ROUND(linear_m / length_m), threshold 0.95 |
| Total volume | linear_m × `x_studio_volume_m3` |

---

## 15. Import & Migration Reference

### 15.1 Excel Source

| Sheet | Purpose | Records |
|-------|---------|---------|
| `MASTERDATA_METRIC_import` | Metric products — full field set (81 columns) | 147 products |
| `MASTERDATA_IMPERIAL_import` | Imperial products — same structure | 117 products |
| `import_master item` | Master Item grouping records | ~70 records |
| `import_master variant` | Master Variant grouping records | ~80 records |
| Reference sheets | Model values (Application, Shape, etc.) | Various |

### 15.2 Field Name Mapping (Import → Odoo)

Key fields where the import column name differs from the vault doc's simplified names:

| Actual Technical Name | Old Vault Name |
|----------------------|---------------|
| `x_studio_master_item_code` | `x_master_item_code` |
| `x_studio_master_variant_code_1` | `x_master_variant_code` |
| `x_studio_word_species` | `x_wood_species` |
| `x_studio_many2one_field_3oj…` | Application |
| `x_studio_many2one_field_6up…` | Shape Value |
| `x_studio_pcslayer` | `x_pcs_per_layer` |
| `x_studio_number_of_layers_1` | `x_layers` |

*Note: The Studio-generated field names with random suffixes (e.g., `_3oj_1jaj6o7st`) are permanent Odoo identifiers. Always use the exact technical name in code and imports.*

---

## 16. Strategic Impact

This product master data architecture:

1. **Drives cubic-based margin logic** — every financial KPI reconciles to m³ through the normalised volume ratio
2. **Enables dryer-centric manufacturing planning** — planning family links products to process parameters and bottleneck constraints
3. **Preserves FIFO integrity** — lot-valuated tracking with mandatory lot assignment prevents cost mixing
4. **Supports multi-entity operations** — shared product masters across BNV (manufacturing), INC (distribution), Holding
5. **Enables analytical accounting** — product category and classification drive GL routing and analytic distribution
6. **Ensures trade compliance** — HS codes, commodity codes, and country of origin are first-class fields with governance
7. **Scales without SKU explosion** — treatment at lot level, no dimensional variants, three-level hierarchy keeps the catalogue manageable

---

## See Also

- [[Metrics & Physical Units]] — Computation layer detail, mixin methods, recompute chain
- [[Pack Reservation]] — Pack selection and full-pack-first allocation
- [[Implementation White Paper]] — Manufacturing architecture and dryer-centric planning
- [[Dryer-Centric Architecture]] — Dryer load / autoclave / process pack models
- [[Accounting & Margin Architecture]] — COGS, accruals, margin per m³
- [[Analytical Accounting Architecture]] — 4 analytic plans, auto-posting rules
