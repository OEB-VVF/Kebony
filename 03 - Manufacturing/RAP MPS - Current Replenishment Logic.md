# RAP MPS — Current Replenishment & MPS Logic (Excel)

**Reference: `RAP MPS.xlsx` (AX2012-era planning tool)**
**Status: Active — used daily by Supply Chain until Odoo migration**

---

## 1. Purpose

This document reverse-engineers the current replenishment logic used by Kebony's supply chain team. The logic lives in a single Excel workbook (`RAP MPS.xlsx`) that acts as the Master Production Schedule (MPS) and Material Requirements Planning (MRP) engine. It pulls data from AX2012 (sales orders, production orders, inventory, purchase orders) and computes planned production quantities for a 6-month rolling horizon.

**This logic must be replicated in Odoo** via the `kebony_manufacturing` module, enriched with the dryer-centric capacity model and planning family concepts defined in the [[Planning Considerations]] and [[Dryer-Centric Architecture]] documents.

---

## 2. Architecture — Three BOM Levels × Two Product Families

The workbook models three BOM levels, each with its own replenishment logic:

| Level | Description | Radiata Sheets | Spruce/Pine Sheets | Calc Engine |
|-------|------------|----------------|---------------------|-------------|
| **FG** | Finished Goods | `FG RAD` | `FG SP` | `FG Calc` |
| **RS** | Rough Sawn (semi-finished) | `RS RAD` | — | `RS Calc` |
| **RM** | Raw Material (boards) | `RM RAD` | `RM SP` | `RM Calc` |

Each level has:
- A **RAD/SP sheet** = the decision view (what to produce, per SKU, per month)
- A **Calc sheet** = the computation engine (rolling inventory projection)

### BOM Explosion with Waste Factors

Demand cascades down through levels with waste/yield factors:
- **FG → RS**: RS demand = FG demand × **1.10** (10% waste in finishing)
- **RS → RM**: RM demand = RS demand × **1.05** (5% waste in sawing)
- Overall RM-to-FG yield assumption: ~86% (1 / (1.10 × 1.05))

---

## 3. SKU Granularity

Each row in the RAD sheets represents one SKU, defined by:

| Column | Field | Example | Meaning |
|--------|-------|---------|---------|
| A | WW | 1934 | Input WW product (raw/semi reference) |
| B | RS | 1935 | Rough Sawn product reference |
| C | Replenishment Time | 1 | Lead time in months |
| D | Part Nr | 2131 | FG item number (AX item ID) |
| E | FT | 10, 12, 14, 16, 18 | Foot length |
| F | M | 30, 36, 42, 48, 54 | Board dimension in mm |
| H | FG Planning Method | Make to Stock / Make to Order | MTS vs MTO |

**Key insight**: Each FG product explodes into ~4-5 rows (one per foot length). The same Part Nr appears multiple times, once per length variant. This maps to Odoo's product template → product variant structure.

---

## 4. Core Replenishment Formula (FG RAD)

### 4.1 Static Columns (Current Month)

For each SKU in the current month:

```
Safety Stock     = board_dimension_mm × annual_demand_factor
                   (zero if Make to Order)

Target Stock     = annual_demand_factor × (board_dimension_mm + 0.75)
                   (zero if Make to Order)

On Hand Stock    = SUMIFS from AX inventory snapshot (tr_inventory_OnHandInventory)

Available Stock  = On Hand - Open Sales Orders (current month)
                   - Forecast (if applicable)

Proposed Prod    = IF Available ≤ Safety Stock:
                       ROUNDUP((Target Stock - Available) / Pack Size) × Pack Size
                   ELSE: 0

Pack Size        = (board_mm / 10) × boards_per_pack(WW)
                   where boards_per_pack comes from the PP sheet
```

### 4.2 Rolling Forward (M+1 through M+5)

The same logic repeats for each forward month, with:
- **Available Stock M+n** = Available M+(n-1) − Demand M+n
- **Demand** = Open Sales Orders for that month + Forecast
- **Proposed Prod** re-evaluated each month: triggers only if available drops below safety stock
- **SLOW Control** = `IF stock ≤ half_annual_demand THEN "OK" ELSE "SLOW"` (flags slow movers)
- **MOH** (Months on Hand) = `inventory / (annual_demand / 12)`

### 4.3 Replenishment Decision Rule

```
IF available_stock_after_demand ≤ safety_stock:
    proposed_qty = ROUNDUP(
        MAX(target_stock - available_stock_after_demand, 0) / pack_size
    ) × pack_size
ELSE:
    proposed_qty = 0
```

**For M (current month — first row, no production orders yet):**
- Subtracts existing production orders (col M = "Prod orders 30 Days")
- Only triggers if after counting existing orders, stock is still below safety

**For M+1 onward:**
- Also subtracts existing Prod orders for that month
- Accounts for proposed production from previous months (cascading inventory balance)

---

## 5. The Calc Engine (FG Calc / RS Calc / RM Calc)

The Calc sheets contain a **7-row repeating block** per SKU, rolling 12+ months forward:

| Row | Label | Source | Formula |
|-----|-------|--------|---------|
| 1 | **OpenSales** | `So` sheet | `SUMIFS(So!$H, product, footlength, year, month)` |
| 2 | **FC** (Forecast) | `Demand Data` sheet | `SUMIFS(historical_demand) × growth_rate × monthly_split` |
| 3 | **US FC** | `US FC` sheet | `SUMIFS(us_forecast) × quarterly_split% × conversion_factor` |
| 4 | **Prod** | `Prod` sheet | `SUMIFS(production_orders, product, footlength, year, month)` |
| 5 | **PlndProd** | Computed | The replenishment trigger (see formula below) |
| 6 | **Inv** (Inventory) | Computed | Rolling balance |
| 7 | **MOH** | Computed | Months on Hand |

### 5.1 Planned Production Formula (PlndProd)

```
PlndProd[month] = IF(
    Inv[month-1] - OpenSales[month] - OpenSales[month+1]
    - FC[month] - US_FC[month] + Prod[month]
    < Safety_Stock × Replenishment_Factor
  THEN:
    MAX(Safety_Stock × Factor - (projected_available), 0)
  ELSE: 0
)
```

This is a **two-month lookahead** — it checks if current inventory minus next two months of demand plus incoming production drops below safety stock threshold.

### 5.2 Inventory Balance (Rolling)

```
Inv[month] = Inv[month-1]
             - OpenSales[month]
             - FC[month]
             - US_FC[month]
             + Prod[month]        (actual/confirmed production)
             + PlndProd[month]    (proposed production)
```

### 5.3 Global Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Growth target | 1.2 (Calc) / 1.1 (RAD) | Applied to historical demand for forecast |
| US Quarterly Split | 5%/5%/5% (Q1) → 9%/9%/9% (Q2) → 10%/10%/10% (Q3) | Seasonality weights |
| Waste RS→FG | 1.10 | 10% yield loss in finishing |
| Waste RM→RS | 1.05 | 5% yield loss in sawing |
| Replenishment Time | 1 month | Production lead time for all items |

---

## 6. Data Source Sheets

| Sheet | Source System | Rows | Purpose |
|-------|-------------|------|---------|
| `So` | AX Sales Orders | 904 | Open SO by product/footlength/month |
| `SCP_SO` | AX Supply Chain Planning | 450 | Filtered SO view |
| `Demand Data` | AX Historical Sales | 9,908 | Forecast base (12-month rolling) |
| `Demand Data (2)` | Backup/alternate | 11,817 | Extended demand data |
| `US FC` | Manual forecast | 19 | US-specific annual forecast by product group |
| `Prod` | AX Production Orders | 126 | Existing/planned manufacturing orders |
| `Pur` | AX Purchase Orders | 618 | Open POs for raw material |
| `Inv` | AX Inventory Snapshot | 6,255 | Current on-hand by item/warehouse/batch |
| `PP` | Reference data | 122 | Pack parameters: boards per pack by WW product |
| `Safety Stocks` | Reference data | 316 | Safety stock levels by SKU |
| `Item Master Data` | AX Item master | 98 | Product description, planning method (MTS/MTO) |
| `Customers` | AX Customer master | 1,850 | Customer reference data |
| `Monthly Split` | Reference data | 168 | Monthly demand distribution weights |
| `md_scp ProductsReleased` | AX Product master | 1,350 | Full product master with 60 attributes |
| `PO m3` / `PO m3 Dynamic` | Computed | — | Purchase order volume tracking |
| `Prod m3` | Computed | — | Production volume tracking |

---

## 7. Key Design Patterns to Preserve in Odoo

### 7.1 Safety Stock Reorder Point
The core trigger is a classic **reorder point with safety stock**. When projected available inventory drops below safety stock, production is triggered to bring stock up to target level. This maps directly to Odoo's replenishment rules but needs:
- **Planning family awareness** (not per-SKU but per family batch)
- **Pack rounding** (production quantity rounded to pack multiples)
- **Dryer capacity constraint** (Excel ignores this entirely)

### 7.2 Make-to-Stock vs Make-to-Order
The planning method is per-SKU. MTO items get zero safety stock and are only produced against demand. This maps to Odoo's `route_ids` (MTO vs MTS) on the product.

### 7.3 Multi-Level BOM Explosion
FG demand cascades to RS and RM via waste factors. In Odoo, this is handled natively by the MRP scheduler when BOMs are properly structured with correct quantities (including yield/waste).

### 7.4 Slow Mover Detection
The "SLOW Control" flag is valuable — it identifies SKUs where stock exceeds half the annual demand. This is the FIFO discipline mechanism discussed in [[Costing Architecture & COGS Decomposition]]. Should be replicated as a periodic Odoo report or dashboard.

### 7.5 US Forecast Overlay
The US market has its own forecast layer with quarterly seasonality splits. This is separate from the base demand forecast and is additive. In Odoo, this could be modeled as a separate forecast source per sales area.

---

## 8. What Excel CANNOT Do (Odoo Must Add)

| Limitation | Odoo Solution |
|-----------|---------------|
| No capacity constraint — ignores dryer availability | Dryer-centric scheduling (see [[Dryer-Centric Architecture]]) |
| No family batching — plans per SKU independently | Planning Family grouping on `kebony.planning.family` |
| No autoclave/dryer load composition | Process Pack → Autoclave Load → Dryer Load hierarchy |
| No WIP tracking — only FG/RS/RM inventory | Real-time WIP via stock locations + MO states |
| No lot traceability | Full lot tracking from RM → RS → FG |
| No cost integration — quantities only | FIFO lot cost flows through BOM explosion |
| No multi-entity — single warehouse view | Multi-company with entity-specific replenishment rules |
| Static forecast — manual Excel refresh | Dynamic forecast from Odoo SO pipeline + CRM |
| No chemical/mix planning link | Mix batch MO triggered by tank level (reorder point on Ready-Mix location) |
| Pack rounding is approximate | Exact pack calculation from `kebony.planning.family.pack_boards` |

---

## 9. Migration Path

### Phase 1 (Current — Planning Families)
- Planning families defined in Odoo with reference process times
- Basic MTS/MTO replenishment rules per product
- Safety stock and reorder point configured per SKU
- Manual planning using planning family views

### Phase 2 (Target — Full MPS in Odoo)
- Automated replenishment scheduler respecting:
  - Safety stock + target stock logic (from RAP MPS)
  - Pack rounding to family-compatible quantities
  - Dryer capacity constraint (max dryer loads per week)
  - Waste factor cascade (FG → RS → RM)
- Rolling 6-month projection view replacing FG Calc / RS Calc / RM Calc
- US forecast overlay integrated with Odoo's demand forecast
- Slow mover report from FIFO lot age analysis

### Phase 3 (Future — Optimisation)
- Dryer scheduling optimisation (family sequencing to minimise changeovers)
- MES integration (Prediktor actual vs planned cycle times)
- AI-assisted demand forecasting replacing static growth factors

---

## 10. Reference Mapping: Excel → Odoo

| Excel Concept | Odoo Model / Field |
|--------------|-------------------|
| Part Nr (item ID) | `product.product.default_code` |
| FT (foot length) | Product variant attribute |
| M (board dimension mm) | Product variant attribute |
| WW / RS product | BOM parent ↔ child relationship |
| Planning Method (MTS/MTO) | `product.template.route_ids` |
| Safety Stock | `product.product` reordering rule (min qty) |
| Target Stock | Reordering rule (max qty) |
| On Hand Stock | `product.product.qty_available` |
| Open Sales Orders | `product.product.outgoing_qty` (from confirmed SO) |
| Production Orders | `product.product.incoming_qty` (from confirmed MO) |
| Forecast (FC) | Odoo Demand Forecast module or custom forecast model |
| US FC | Sales area-specific forecast overlay |
| Pack Size | `kebony.planning.family.pack_boards` × board dimensions |
| Boards per Pack (PP sheet) | `kebony.planning.family.pack_boards` |
| Growth Rate | Forecast parameter (configurable) |
| Waste Factor | BOM quantity ratio (e.g., 1.10 RS per 1.00 FG) |
| SLOW Control | Custom report: stock vs annual demand ratio |
| MOH | Custom report: inventory ÷ monthly consumption |
