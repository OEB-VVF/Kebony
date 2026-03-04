# Prepayment Flag

**Scope**: Kebony Inc. (US entity) — Odoo 19
**Module**: `kebony_bol_report`
**Entity filter**: `x_kebony_entity_type == 'inc'`

---

## 1. Overview

A Boolean flag `x_is_prepayment` on `account.move` marks invoices
created as **down payments** (prepayments) from the Sales flow.

The flag is set **automatically** when the Down Payment wizard creates
an invoice. It can also be **toggled manually** on the invoice form.

Purpose:
- Filtering and reporting
- Distinguishing prepayment invoices from regular invoices
- **Margin skip**: prepayment invoices are excluded from margin computation
- **Cross-linking**: navigation between prepayment ↔ final invoices
- **Final Invoice Issued**: stored Boolean for tracking/filtering

---

## 2. Field Registry

| Label                   | Field                                  | Model          | Type    | Stored | Default |
|-------------------------|----------------------------------------|----------------|---------|--------|---------|
| Is Prepayment           | `x_is_prepayment`                     | `account.move` | Boolean | Yes    | `False` |
| Final Invoice Issued    | `x_kebony_final_invoice_issued`        | `account.move` | Boolean | Yes    | `False` |
| Final Invoices          | `x_kebony_linked_final_invoices`       | `account.move` | M2M (computed) | No | — |
| Prepayment Invoices     | `x_kebony_linked_prepayment_invoices`  | `account.move` | M2M (computed) | No | — |

### `x_is_prepayment`
- **`copy=False`**: Prevents propagation to credit notes or duplicated invoices.
- **Widget**: `boolean_toggle` — visual toggle on the invoice form.

### `x_kebony_final_invoice_issued`
- **Stored Boolean** — searchable and filterable in list views.
- Set automatically by the wizard when a final invoice is created
  (see §3). Also synced by the cross-link compute as a
  belt-and-suspenders fallback (see §3.1).

### `x_kebony_linked_final_invoices` / `x_kebony_linked_prepayment_invoices`
- **Unstored computed M2M** — recalculated every time the form loads.
- On a **prepayment**: shows linked final invoices (clickable tags).
- On a **final invoice**: shows linked prepayment invoices (clickable tags).
- Navigation: click a tag to open the linked invoice directly.
- Compute traces: invoice → `sale_line_ids.order_id` → `invoice_ids` →
  filter siblings by `x_is_prepayment`.

---

## 3. Automatic Detection & Final Invoice Tracking

**Model**: `sale.advance.payment.inv` (TransientModel — Down Payment wizard)
**Method**: `create_invoices()` override

Logic:
1. Snapshot existing invoice IDs on the sale order **before** calling `super()`
2. Call `super().create_invoices()` to create the invoice(s)
3. Detect **newly created** invoices by comparing sets (after − before)
4. Check `advance_payment_method` to distinguish DP from final:
   - `"percentage"` or `"fixed"` → **down payment** → mark new invoices
     `x_is_prepayment = True`
   - `"all"` or `"lines"` → **final invoice** → find prepayment siblings
     and set `x_kebony_final_invoice_issued = True` on them

This ensures:
- Only down payment invoices are flagged as prepayments
- When the final invoice is created, all related prepayments are
  automatically marked as "final issued"

### 3.1 Belt-and-Suspenders Sync

The cross-link compute (`_compute_prepayment_cross_links`) also
syncs `x_kebony_final_invoice_issued` via direct SQL every time the
form loads. This catches:
- Existing records created before the wizard logic was added
- Manual `x_is_prepayment` toggles
- Edge cases where the wizard didn't fire

---

## 4. UI Placement

The toggle appears on the invoice form view, immediately after the
invoice number (`name` field).

- **Editable**: Users can manually toggle the flag for corrections
- **View record**: XPath after `//field[@name='name']` in
  `views/account_move_view.xml`

---

## 5. Accounting Context

Odoo's Down Payment wizard creates invoice lines using the "Down Payment"
product. By Kebony configuration, this product's income account maps to
**account 212000 (Deferred Revenue)**.

### Journal Entry Flow

```
Prepayment Invoice:
  DR  121000  Accounts Receivable
  CR  212000  Deferred Revenue

Final Invoice (regular):
  DR  121000  Accounts Receivable
  CR  400000  Revenue (full amount)
  DR  212000  Deferred Revenue (reversal of prepayment)
  CR  121000  Accounts Receivable (net of prepayment)
```

The prepayment flag helps identify which invoices hit Deferred Revenue
vs regular Revenue without inspecting individual journal lines.

---

## 6. Identifying Prepayments Programmatically

If the flag is lost or needs bulk correction, real prepayments can be
detected via the journal entry chain:

```python
real_prepayments = env["account.move"].search([
    ("invoice_line_ids.sale_line_ids.is_downpayment", "=", True),
    ("invoice_line_ids.account_id.code", "=", "212000"),
    ("move_type", "in", ["out_invoice", "out_refund"]),
])
```

This traces: **invoice line → sale order line → `is_downpayment`** (standard
Odoo field) AND verifies the line hits account 212000.

---

## 7. Margin Integration

Prepayment invoices are **excluded** from margin computation:
- The margin button is hidden on invoices where `x_is_prepayment = True`
- `action_recompute_management_margin()` skips prepayment records

On **final invoices**, down payment revenue is restored:
- Traces invoice → SO → sibling prepayments
- Sums `amount_untaxed` of posted prepayment invoices
- Adds back to `net_sales` (Odoo's DP deduction line already reduced
  `amount_untaxed`)

The combined value (DP − Credit Notes) is displayed in the
**"Credit Note / Pre-payment"** field (`x_studio_credit_note`).

See [[Accounting & Margin Architecture]] §7 for the full margin formula.

---

## 8. Odoo Module Reference

| Component                        | File                               | Purpose                                    |
|----------------------------------|------------------------------------|--------------------------------------------|
| `x_is_prepayment`               | `models/account_move_prepayment.py`| Boolean field on `account.move`            |
| Cross-link M2M fields            | `models/account_move_prepayment.py`| Computed navigation links                  |
| `x_kebony_final_invoice_issued`  | `models/account_move_prepayment.py`| Stored Boolean + compute sync              |
| Wizard override                  | `models/account_move_prepayment.py`| `sale.advance.payment.inv.create_invoices()`|
| Form view toggle                 | `views/account_move_view.xml`      | XPath injection after invoice name         |
| Cross-link tags in form          | `views/account_move_view.xml`      | `many2many_tags` widget for navigation     |

---

## See Also

- [[Accounting & Margin Architecture]] — US accounting framework,
  accrual engine, COGS, margin formula with DP handling
- [[Consignment & Biewer]] — Consignment flow (no prepayments on
  consignment products)
