# Consignment & Biewer (US)

**Scope**: Kebony Inc. (US entity) — Odoo 19
**Module**: `kebony_bol_report`
**Entity filter**: `x_kebony_entity_type == 'inc'`

---

## 1. Business Context

Kebony Inc. holds inventory on consignment from **Biewer Lumber, LLC**.
The goods are physically stored in Kebony's warehouses but **do not
belong to Kebony** — they remain Biewer's property until sold.

When Kebony sells consigned goods to a customer, Kebony must then
purchase those goods from Biewer at pre-agreed prices. This creates a
unique accounting and inventory challenge.

---

## 2. Consignment Detection

A product is consignment if:
- `product.categ_id.name == "Product in Consignment"` (exact match)
- OR `x_is_consignment` flag is True on product (if field exists)

---

## 3. Inventory Treatment

### Product Category: "Product in Consignment"

A special product category is configured with **all stock valuation
accounts left blank**:

| Setting              | Value   |
|----------------------|---------|
| Cost Method          | FIFO    |
| Inventory Valuation  | Automated |
| Stock Input Account  | *(blank)* |
| Stock Output Account | *(blank)* |
| Valuation Account    | *(blank)* |

### Why blank accounts?

Because the goods **do not belong to Kebony**:

- **No inventory valuation journal entries** are created on receipt or
  delivery
- Stock movements (receipts, deliveries, internal transfers) still occur
  physically — the goods are tracked in Odoo's inventory module for
  operational purposes (dispatch notes, picking, reporting)
- But there is **no financial impact** on the balance sheet for
  inventory movements of consigned goods

### What IS tracked

- Full stock movements: receipts, internal transfers, deliveries
- Lot/serial tracking (packs)
- Dispatch notes and delivery orders
- Inventory reporting (quantities on hand, reserved, available)
- Wood metrics (linear m, boards, volume m3)

### What is NOT tracked

- Inventory valuation journal entries
- COGS on delivery (handled differently — see below)

---

## 4. Sales Flow

When Kebony sells consigned goods to a customer:

1. **Sales Order** — standard flow, lines reference consignment products
2. **Delivery** — stock is dispatched, no valuation entries (blank accounts)
3. **Customer Invoice** — revenue is recognised normally

### COGS for Consignment

COGS is computed via the **consignment pricing table** (model:
`stock.consignment.price`):

```
COGS = unit_price (from consignment price table) x qty_in_product_uom
```

This is Path 1 in the margin recompute logic (see [[Accounting & Margin Architecture]]).

### Accrual Exceptions

Consignment products have **special accrual rules**:
- **NO royalties** (skipped)
- **NO management fees** (skipped)
- Marketing accruals: normal rules apply
- Sales rep charges: normal rules apply

---

## 5. Consignment Price Table

### Model: `stock.consignment.price`

Stores the agreed unit price per product per warehouse per owner.

| Field          | Type       | Description                     |
|----------------|------------|---------------------------------|
| `partner_id`   | Many2one   | Owner (e.g. Biewer Lumber, LLC) |
| `warehouse_id` | Many2one   | Warehouse where stock is held   |
| `product_id`   | Many2one   | Consigned product               |
| `unit_price`   | Float      | Agreed unit price               |
| `currency_id`  | Many2one   | Price currency                  |
| `active`       | Boolean    | Archive flag                    |

**Constraint**: One price per (partner, warehouse, product).

### Wizard: "Generate Consignment Prices from Stock"

Model: `consignment.price.from.stock` (TransientModel)

Generates or updates consignment price records based on current stock
in a warehouse. Uses `product.standard_price` as the default unit price.

- Input: owner partner, warehouse, overwrite flag
- Creates missing price records
- Optionally overwrites existing prices

---

## 6. Purchase Order Generation (Biewer PO)

When consigned goods are sold and invoiced, Kebony must create a
**Purchase Order to Biewer** to formally acquire the goods.

### Trigger

Button on Accounting Hub: *"Generate Consignment Purchase Orders"*.
Can also be triggered directly from `account.move`.

### Vendor

Exact match: `"Biewer Lumber, LLC"` with `supplier_rank > 0`.

### Logic (`action_generate_biewer_po`)

1. Find all **posted customer invoices** (`out_invoice` / `out_refund`) with consignment product lines
2. Exclude invoices already treated (linked via `x_invoice_id` on PO lines of confirmed POs)
3. Group lines by **warehouse** (determined from done picking linked to sale)
4. Per warehouse, create one draft PO with:
   - **Qty** = invoice line quantity (in invoice UoM)
   - **UoM** = invoice line UoM (preserves packaging)
   - **Price** = unit cost from stock moves or quant `x_studio_unit_cost`
   - **Price conversion** = if invoice UoM differs from product base UoM, convert via `_compute_price`
   - **Description** = includes invoice reference and lot/pack traceability
   - **`x_invoice_id`** = links PO line back to source invoice (prevents double processing)
   - Analytic distribution copied from invoice line
5. The PO is created in **draft** status

### Key Design Decision: Goods Are Never Received

The Purchase Order to Biewer is purely financial — Kebony already has
physical possession of the goods. **No receipt picking is created.**

The `_create_picking()` method on `purchase.order` is overridden:
POs flagged `x_kebony_is_consignment_po = True` skip receipt creation
entirely. Only non-consignment POs call `super()._create_picking()`.
This prevents accidental double-counting of inventory.

### Cost Determination (for PO price_unit)

1. **Primary:** Stock move valuation — `move.value / qty_done` for done moves linked to the invoice
2. **Fallback:** Quant `x_studio_unit_cost` on the lot at the internal location

Cost is expressed in **product base UoM**, then converted to the invoice line UoM if different.

### PO Line Traceability

Each PO line carries:
- `x_invoice_id` — links back to the customer invoice that triggered it
- Lot names in the description for audit trail

---

## 7. Consignment Price — Initial Stock Values

A custom model registers all **initial stock values** agreed with Biewer
when Kebony acquired the company. This table provides the unit prices
used in the Purchase Orders.

The `stock.consignment.price` model serves this purpose — it holds the
contractual per-product prices that Kebony owes Biewer for each unit
sold.

---

## 8. End-to-End Flow Diagram

```
                    PHYSICAL FLOW
                    =============

Biewer ships goods --> Kebony warehouse (receipt, no valuation)
                              |
                    Customer orders
                              |
                    Delivery to customer (no valuation JE)
                              |
                    Customer invoice (revenue recognised)


                    FINANCIAL FLOW
                    ==============

Customer Invoice posted
        |
        +-> COGS computed from consignment price table
        |   (for margin calculation / commission)
        |
        +-> Accruals posted (marketing + sales rep only,
        |   NO royalties, NO management fees)
        |
        +-> "Generate Consignment PO" button
                |
                +-> Draft PO to Biewer Lumber
                    (one PO per warehouse, with lot detail)
                        |
                        +-> Confirm PO -> Vendor invoice from Biewer
                            DR: Expense / Inventory
                            CR: Accounts Payable
```

---

## 9. Custom Fields

| Model | Field | Purpose |
|---|---|---|
| `purchase.order` | `x_kebony_is_consignment_po` | Boolean — marks PO as consignment (financial-only, no receipt picking) |
| `purchase.order.line` | `x_invoice_id` | Links PO line to source customer invoice (prevents reprocessing) |

---

## 10. Odoo Module Reference

| Component                     | File                                | Purpose                          |
|-------------------------------|-------------------------------------|----------------------------------|
| Consignment price model       | `stock_consignment_price.py`        | Price per product/warehouse/owner|
| Consignment price wizard      | `consignment_price_from_stock.py`   | Bulk-generate prices from stock  |
| Consignment price views       | `stock_consignment_price_views.xml` | List + form + action             |
| Wizard views                  | `consignment_price_from_stock_views.xml` | Wizard form + action        |
| Biewer PO generation          | `account_move_biewer_po.py`         | `action_generate_biewer_po()`    |
| Consignment PO flag + skip receipt | `purchase_order.py`            | `x_kebony_is_consignment_po` + `_create_picking()` override |
| PO line source tracking       | `purchase_order_line.py`            | `x_invoice_id` field             |
| Accounting Hub button         | `kebony_accounting_hub_views.xml`   | UI entry point                   |
| COGS path 1 (consignment)    | `account_move.py`                   | `_is_consignment_product()` check|
| Accrual exceptions            | `account_move_line.py`              | Skips royalties + mgmt fees      |
| Security                      | `ir.model.access.csv`               | Access rules for both models     |
