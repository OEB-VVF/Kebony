# Metrics & Physical Units

**Scope**: All Kebony entities (global)
**Module**: `kebony_bol_report`
**Entity filter**: None — applies to all companies

---

## 1. Overview

Kebony trades timber products that are measured in three physical
dimensions: **linear length**, **board count**, and **cubic volume**.

The metrics layer computes and stores these values across all relevant
models (quants, lots, products, stock moves, sale order lines, invoice
lines) and propagates them up to document totals (sale orders, invoices).

---

## 2. Canonical Units

All internal calculations are normalised to **metric units**:

| Dimension  | Internal Unit | Display     |
|------------|---------------|-------------|
| Linear     | **meters (m)**| m, lm       |
| Boards     | integer count | boards      |
| Volume     | **m3**        | cubic metres |

Imperial units (feet, ft3) are used only for display in US reports and
transport documents.

### Conversion Constants

```
FT_PER_M  = 3.280839895
M_PER_FT  = 1 / FT_PER_M
FT3_PER_M3 = 35.3146667
```

---

## 3. Key Product Fields (Studio)

These fields are defined via Odoo Studio on `product.template`:

| Field                        | Unit    | Description                              |
|------------------------------|---------|------------------------------------------|
| `x_studio_length_m`         | meters  | Board length in metres (preferred)       |
| `x_studio_length_1`         | feet    | Board length in feet (legacy, converted) |
| `x_studio_volume_m3`        | m3/lm   | Normalised volume per linear metre       |
| `x_studio_boards_per_pack`  | integer | Boards per standard pack                 |
| `x_studio_product_classification` | M2M | Values: `"wood"`, `"accessory"`     |

### Important: `x_studio_volume_m3` vs `product.volume`

- **`x_studio_volume_m3`** = normalised m3 per linear metre. Always
  metric regardless of product measurement system. Used for all internal
  volume calculations.
- **`product.volume`** = localised value (m3/lm for metric products,
  ft3/lf for imperial). Used only for transport/supply chain documents.

**Rule**: Never use `product.volume` for Kebony metric calculations.

---

## 4. Computation Layer: `kebony.metrics.mixin`

Abstract model mixed into: `stock.quant`, `stock.lot`, `stock.move`,
`sale.order.line`, `account.move.line`, `product.template`.

### Core Methods

**`_kebony_linear_qty_in_m(product, qty, line_uom=None)`**
- Normalises any quantity to linear metres
- If `line_uom` differs from `product.uom_id` (e.g. packaging), first
  converts via `uom._compute_quantity`
- Then normalises to metres based on UoM detection (meter/foot)
- Odoo 19 merged packaging and UoM, so line_uom may be a "Pack of 50"

**`_kebony_boards_from_raw(total_qty, length_per_board)`**
- Low-level board count; both args in the **same** unit (feet or metres), method is unit-agnostic.
- `raw = total_qty / length_per_board`
- Snap tolerance: `BOARD_SNAP_TOLERANCE = 0.2`
- Rule: if `|raw - round(raw)| <= 0.2` → snap to nearest integer, otherwise truncate.
  - Absorbs bidirectional float/UoM drift (e.g. `89.97 → 90`, `90.03 → 90`)
  - Stays well below a genuine partial board (0.5+), so `10.5 → 10` (not 11).
- Replaces the older `ROUND_UP_THRESHOLD = 0.95` rule (removed after a rounding bug in UoM conversion produced systematic under-counts).
- `_kebony_boards_from_linear` kept as an alias for backwards compatibility.

Implementation: `kebony_bol_report/models/kebony_metrics_layer.py:164-192`

**`_kebony_volume_m3(product, linear_m)`**
- `volume = linear_m x x_studio_volume_m3`
- Uses the normalised m3/lm ratio, NOT `product.volume`

**`_kebony_length_per_board(product)`**
- Returns `x_studio_length_m` if available
- Falls back to `x_studio_length_1 x M_PER_FT`

**`_kebony_volume_ft3(volume_m3)`**
- Reporting only: `volume_m3 x FT3_PER_M3`

**`_kebony_is_wood_product(product)`**
- Checks `x_studio_product_classification` for value `"wood"`
- Only wood products get linear metrics computed

### Wood-Only Rule

Physical metrics (linear m, boards, volume m3) are **only computed for
wood products**. Accessories get 0 for all physical metrics. This is
enforced at compute time in both `sale.order.line` and `account.move.line`.

### UoM Conversion Chain

```
Line UoM (Pack, Board, etc.)
  -> product.uom_id (Linear Feet, Linear Meter)
    -> Meters (normalised)
```

The `line_uom` parameter handles the first conversion. The mixin handles
the second (feet -> meters or via `uom._compute_quantity`).

---

## 5. Metrics by Model

### Stock Quant (`stock.quant`)

Lowest level — stored computed fields:

| Field                              | Description           |
|------------------------------------|-----------------------|
| `x_kebony_linear_m_on_hand`       | Linear m (on hand)    |
| `x_kebony_linear_m_reserved`      | Linear m (reserved)   |
| `x_kebony_linear_m_available`     | Linear m (available)  |
| `x_kebony_boards_on_hand`         | Boards (on hand)      |
| `x_kebony_boards_reserved`        | Boards (reserved)     |
| `x_kebony_boards_available`       | Boards (available)    |
| `x_kebony_volume_m3_on_hand`      | Volume m3 (on hand)   |
| `x_kebony_volume_m3_reserved`     | Volume m3 (reserved)  |
| `x_kebony_volume_m3_available`    | Volume m3 (available) |

Legacy mirrors: `x_studio_number_of_boards`, `x_studio_lf_avail`,
`x_studio_available_linear_foot`

### Stock Lot (`stock.lot`)

Aggregated from internal quants:

Same field structure as quant (on_hand / reserved / available).
Legacy mirrors: `x_studio_boards`, `x_studio_linear_feet`

### Product Template (`product.template`)

Aggregated from internal quants across all variants:

| Field                              | Description           |
|------------------------------------|-----------------------|
| `x_studio_number_of_boards`       | Total boards available|
| `x_studio_available_linear_foot`  | Total linear m avail. |
| `x_kebony_volume_m3_on_hand`      | Total volume m3       |
| `x_kebony_available_packs`        | Count of distinct lots|

### Stock Move (`stock.move`)

| Field                        | Description                |
|------------------------------|----------------------------|
| `x_studio_lf`               | Linear metres              |
| `x_studio_boards`           | Board count                |
| `x_kebony_volume_m3`        | Volume m3                  |
| `x_kebony_dryer_hours_eq`   | Dryer equivalent hours     |
| `x_kebony_autoclave_hours_eq` | Autoclave equiv. hours   |

Uses `move_line_ids.quantity` (done qty) if available, else
`product_uom_qty` with `product_uom` conversion.

### Sale Order Line (`sale.order.line`)

| Field                    | Description              |
|--------------------------|--------------------------|
| `x_studio_boards`        | Boards                   |
| `x_studio_linear_feet`   | Linear metres            |
| `x_studio_price_lf`      | Price per linear metre   |
| `x_kebony_volume_m3`     | Volume m3                |
| `x_kebony_price_m3`      | Price per m3             |

### Sale Order (`sale.order`)

Aggregate totals: `x_kebony_total_linear_m`, `x_kebony_total_boards`,
`x_kebony_total_volume_m3`

### Account Move Line (`account.move.line`)

| Field                    | Description              |
|--------------------------|--------------------------|
| `x_studio_linear_feet`   | Linear metres            |
| `x_boards`               | Board count              |
| `x_price_lf`             | Price per linear metre   |
| `x_kebony_volume_m3`     | Volume m3                |
| `x_kebony_price_m3`      | Price per m3             |

### Account Move (`account.move`)

Aggregate totals: `x_kebony_total_linear_m`, `x_kebony_total_boards`,
`x_kebony_total_volume_m3`

---

## 6. Recompute Hierarchy

The dependency chain for bulk recomputation:

```
Level 1: stock.quant  (source of truth)
    |
    +-> stock.lot     (aggregate from quants)
    |
    +-> product.template (aggregate from quants)

Level 2: stock.move   (from move lines or demand qty)
         sale.order.line (from SO line qty + UoM)
         account.move.line (from invoice line qty + UoM)

Level 3: sale.order   (sum of order lines)
         account.move  (sum of invoice lines)
```

The **Rebuild Metrics** button on `res.company` triggers this full chain
in order, batched at 1000 records.

---

## 7. Volume Formula

For a board of height H (m) x width W (m) x length L (m):
- `x_studio_volume_m3` = H x W (cross-sectional area in m2, expressed as m3/lm)
- Total volume = `linear_meters * x_studio_volume_m3`

Example: board 2.54cm x 20.066cm x 304.8cm
- `x_studio_volume_m3` = 0.0254 x 0.20066 = 0.005097 m3/lm

---

## See Also

- [[Pack Reservation]] — Pack selection and full-pack-first allocation
- [[Product Master Data]] — Product architecture and field registry
