# Manufacturing Test Data — Import Guide

Target: **kebonyprod-test** instance
Company: **Kebony BNV** (id=3)

## Prerequisites

The test instance must already have:
- 4 Work Centers: Stacking (STACK), Autoclave (AC), Dryer (DRY), Chemical Mixing (MIX)
- 17 Planning Families (installed via `kebony_manufacturing` module data)
- 1 Cost Version: "Standard 2026 (Belgium)"
- Kallo warehouse with Kallo/Stock location (id=47)
- Products already exist (1003, 1929, 1934, 1127-M-* etc.)

## Import Order

Import files **sequentially** in numbered order. Each file depends on the previous ones.

### Step 1: `01_stock_locations.csv`
**Model:** `stock.location`
**Action:** Import (create new records)

Creates 8 sub-locations under Kallo/Stock (id=47):
- Raw - Prime, Raw - B-Grade (inbound receiving)
- WIP - Kebonisation, WIP - Clear, WIP - Ready-Mix (work-in-process)
- FG - Character, FG - Clear (finished goods)
- RDK - Machining (supplier location for subcontracting)

Uses `location_id/.id` = 47 (numeric ID of Kallo/Stock). Verify this ID matches your instance.

### Step 2: `02_products_update_type.csv`
**Model:** `product.template`
**Action:** Import with "Match existing records" on `name` field

Updates existing products from `consu` to `product` (storable) with lot tracking.

**WARNING:** Some products (e.g. 1929, 1934) may have duplicates. During import:
1. Use Odoo's import preview to check for duplicate matches
2. If duplicates exist, skip those rows and fix manually
3. Products that are Master Items (non-sellable) should remain `consu`

Covers 53 products across all planning families:
- KSP families: 1003, 1127, 1171, 1243, 1407, etc.
- KRRS families: 1929, 1931, 1934, 1935, 2220, etc.

### Step 3: `03_chemical_products.csv`
**Model:** `product.template`
**Action:** Import (create new records)

Creates 4 chemical products:
- Furfuryl Alcohol (FA) — raw chemical, lot-tracked
- Citric Acid — raw chemical, lot-tracked
- Water (Process) — no tracking
- Kebony Ready-Mix — WIP chemical, lot-tracked

**Note:** `categ_id` uses name matching. Verify that product categories "All / Raw Material" and "All / Work In Process" exist, or adjust to match your instance.

### Step 4: `04_purchase_orders.csv`
**Model:** `purchase.order`
**Action:** Import (create new records)

Creates 4 POs from "Kebony Norge AS":
- PO_TEST_RAW_001 (2026-03-01): 1003, 1929, 1934
- PO_TEST_RAW_002 (2026-03-15): 1003, 1929, 1934
- PO_TEST_RAW_003 (2026-04-01): 1003, 1929
- PO_TEST_CHEM_001 (2026-03-01): FA, Citric Acid, Water

**After import:**
1. Confirm each PO (button "Confirm Order")
2. Validate each receipt (Kallo/Stock > Raw - Prime)
3. This creates FIFO valuation layers at different unit costs

Price differences between batches enable FIFO testing:
- 1003: 3.20 -> 3.25 -> 3.30 EUR/m
- 1929: 2.85 -> 2.90 -> 2.95 EUR/m
- 1934: 4.10 -> 4.15 EUR/m

### Step 5: `05_bom_chemical_mix.csv`
**Model:** `mrp.bom`
**Action:** Import (create new records)

Creates 1 BOM for Ready-Mix production (1000 kg batch):
- 650 kg Furfuryl Alcohol
- 50 kg Citric Acid
- 300 kg Water

This is the independent chemical mix MO described in the architecture.

### Step 6: `06_bom_ksp_character.csv`
**Model:** `mrp.bom`
**Action:** Import (create new records)

Creates BOMs for 5 Character (Scots Pine) finished products:
- 1127-M-3.5 through 1127-M-4.7

Each BOM consumes:
- 1003 (raw KSP 28x120) at scrap factor 1.062 (6.2% total scrap)
- Kebony Ready-Mix at 0.001039 kg/m (= 309 kg/m3 x 0.00336 m3/m)

**Note:** Chemical qty is per linear meter of output. The 309 kg/m3 rate comes from family KSP15T; the 0.00336 m3/m is the volume ratio for 28x120mm cross-section.

### Step 7: `07_bom_krrs_clear.csv`
**Model:** `mrp.bom`
**Action:** Import (create new records)

Creates BOMs for 3 Clear (Radiata) semi-FG products:
- 1931-M-3.5, 1931-M-3.8, 1931-M-4.1

Each BOM consumes:
- 1929 (raw Radiata 25mm RS) at scrap factor 1.039 (3.9% total scrap)
- Kebony Ready-Mix at 0.004225 kg/m (= 676 kg/m3 x 0.00625 m3/m)

These produce semi-finished goods that go to RDK for machining.

### Step 8: `08_bom_operations.csv`
**Model:** `mrp.routing.workcenter` (BOM operations)
**Action:** Import (create new records)

Adds work center operations to each BOM created in steps 6-7:
- Entry Stacking: 3.5h (KSP) / 4.5h (KRRS)
- Autoclave: 75h (KSP) / 54h (KRRS)
- Dryer: 75h (KSP) / 54h (KRRS)

**WARNING:** This file references BOMs by external ID (`bom_id/id`). This only works if the BOMs in steps 6-7 were imported with their `id` column values preserved as external IDs. If Odoo did not create external IDs during import, you will need to either:
1. Import BOMs via Settings > Technical > External Identifiers first
2. Or add operations manually via the BOM form

Hours come from planning family reference data:
- KSP15T: stacking=3.5h, dryer=75h
- KRRS1: stacking=4.5h, dryer=54h

## Manual Steps After Import

### A. Route configuration
After importing locations, configure warehouse routes:
1. Kallo warehouse > Routes: ensure "Manufacture" route exists
2. Manufacturing location should use WIP - Kebonisation
3. Raw material procurement: Raw - Prime

### B. Planning family assignment
Assign planning families to products (via product form or family assignment wizard):
- 1127-M-* products -> KSP 1.5" Terrace (KSP15T)
- 1931-M-* products -> KRRS 1" (KRRS1)
- 1003 -> not assigned (raw material)
- 1929 -> not assigned (raw material)

### C. Cost version lines
In the "Standard 2026 (Belgium)" cost version:
1. Use "Snapshot Families" button to populate family lines
2. Add WC cost lines for each work centre + GL account
3. Add product price lines for raw materials (1003, 1929, chemicals)

### D. Duplicate product cleanup
Products 1929 and 1934 have known duplicates. Before import:
1. Search for these products in Odoo
2. Archive duplicates, keeping only the canonical record
3. Then import file 02

## BOM Calculation Reference

### Scrap factor
```
scrap_factor = 1 / (1 - b_grade% - internal%)
```
- KSP15T: 1 / (1 - 0.04 - 0.022) = 1.066 (used 1.062 for margin)
- KRRS1:  1 / (1 - 0.023 - 0.016) = 1.041 (used 1.039 for margin)

### Chemical consumption per linear meter
```
chem_per_lm = mix_consumption_per_m3 * volume_per_lm
```
- KSP15T (28x120mm): 309 kg/m3 * 0.00336 m3/m = 1.038 kg/m -> 0.001039 kg/mm (typo: kg/m)
- KRRS1 (25mm RS):   676 kg/m3 * 0.00625 m3/m = 4.225 kg/m -> 0.004225 kg/m

### Volume per linear meter (approximate)
- 28x120mm (KSP decking): 0.028 * 0.120 = 0.00336 m3/m
- 25mm rough sawn (KRRS1): ~0.025 * 0.250 = 0.00625 m3/m (rough sawn width varies)

## File Format Notes

- All CSVs use comma delimiter, UTF-8 encoding
- `/.id` suffix = numeric database ID (use when external ID unavailable)
- `/id` suffix = external ID (XML ID)
- Name matching used for many2one fields where no XML ID exists
- Empty cells in repeated rows = continuation of same parent record (Odoo sub-record import format)
