# Pack Reservation

> Documentation for the pack selection feature (pick specific lots on SO) and the full-pack-first allocation strategy.
> Module: `kebony_bol_report` — `sale_order.py`, `sale_order_line.py`, `stock_move.py`, `stock_lot.py`

---

## Business Context

Sales team needs to select **specific packs (lots)** for a customer order rather than relying on FIFO. This is common for:
- Large orders where the customer wants specific lot numbers
- Quality matching (same production batch)
- Logistics (packs already staged in a specific warehouse location)

---

## Pack Selection Workflow

### 1. User Selects Packs (on SO in Draft/Sent)
- User opens pack selection dialog on SO line
- Dialog shows available lots filtered by product + warehouse (`lot_stock_id`)
- Selected lots are marked: `lot.x_reserved_sale_order_id = order.id`
- SO line description prefixed with `[PACK]`

### 2. Confirmation (action_confirm)
- `super().action_confirm()` creates stock pickings
- Custom logic: for products with reserved lots, replaces auto-generated move lines with lot-specific allocations
- **Proportional allocation:** qty distributed across lots based on each lot's board count ratio (not equal division)
- Last lot gets the remainder (avoids rounding drift)

### 3. Delivery
- Standard Odoo picking process — lots are already allocated

---

## Reservation Lifecycle

| Action | Effect on Reservations |
|---|---|
| **Draft → Confirmed** | Reservations pushed to picking move lines |
| **Confirmed → Cancel** | Reservations **kept** (lots stay reserved) |
| **Cancel → Draft** | Reservations **kept** (user can re-confirm) |
| **Delete SO** | Reservations **released** (lots freed via `unlink()` override) |
| **Delete SO line** | Reservations for that line's product **released** (via `unlink()` on `sale.order.line`) |

**Key design choice:** Reservations persist through Cancel → Draft → re-Confirm cycle. They are only released when the SO or line is physically deleted.

---

## Full-Pack-First Allocation (Wood Products)

When NO pack-wish exists on a wood product, the system automatically rebalances Odoo's default FIFO allocation to **prefer untouched full packs** over splitting packs.

### Strategy (3-pass algorithm in `_kebony_rebalance_full_packs`)

1. **Pass 1 — Full packs:** Take lots where `available_qty == total lot qty` (untouched) that fit entirely within remaining demand. FIFO order.
2. **Pass 2 — Best-fit partial:** Find the smallest lot that covers the remaining gap.
3. **Pass 3 — Last resort:** Take whatever is left to cover remaining demand.

### Rules
- **Wood products only** (checked via `_kebony_is_wood_product`)
- **Never over-deliver** — stick to exact demand
- **Skip if pack-wish active** — Strategy A (pack-wish) and Strategy B (full-pack-first) are mutually exclusive
- Runs inside `_action_assign()` after `super()` completes

---

## Key Fields

| Model | Field | Purpose |
|---|---|---|
| `stock.lot` | `x_reserved_sale_order_id` | Links lot to the SO that reserved it |
| `stock.lot` | `x_studio_boards` | Board count — used for proportional allocation |
| `sale.order.line` | name prefix `[PACK]` | Marks lines created by pack selection |
