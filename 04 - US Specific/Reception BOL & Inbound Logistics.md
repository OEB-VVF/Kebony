# Reception BOL & Inbound Logistics

**Scope**: Kebony Inc. (US entity) — Odoo 19
**Module**: `kebony_bol_report`
**Entity filter**: `x_kebony_entity_type == 'inc'`

---

## 1. Overview

Kebony now has two Bill of Lading reports:

| Report          | Direction | Use Case                        |
|-----------------|-----------|----------------------------------|
| Expedition BOL  | Outgoing  | Deliveries to customers          |
| Reception BOL   | Incoming  | Receipts from suppliers          |

The Reception BOL mirrors the Expedition BOL structure but with
**reversed addresses** (vendor → warehouse), additional **logistics
metadata** (container, master BOL, dates), and support for lines
**without lot assignment** (common on incoming receipts before QC).

Five fields on `stock.picking` capture inbound logistics details.
These are visible on both **incoming receipts** and **dropship**
documents (via `is_dropship` from `stock_dropshipping`).

---

## 2. Field Registry (`stock.picking`)

All fields use the `x_kebony_*` naming convention (Python-defined):

| Label                    | Field                           | Type | Description                                     |
|--------------------------|---------------------------------|------|-------------------------------------------------|
| Container #              | `x_kebony_container_number`    | Char | Container number for the inbound shipment       |
| Master Bill of Lading #  | `x_kebony_master_bol_number`   | Char | Master BOL number from the carrier              |
| Expedition Date          | `x_kebony_expedition_date`     | Date | Date goods were dispatched by the supplier      |
| Arrival Date             | `x_kebony_arrival_date`        | Date | Date goods arrived at the port or transit hub   |
| Delivered Date           | `x_kebony_delivered_date`      | Date | Date goods arrived at Kebony's warehouse        |

These are user-entered, not computed. They document the inbound
logistics timeline for traceability.

---

## 3. UI: Reception Details Tab

A notebook page **"Reception Details"** is injected on the `stock.picking`
form, before the standard "Extra" tab.

**Visibility**:
```
invisible="picking_type_code != 'incoming' and not is_dropship"
```
Shows on:
- **Incoming receipts** (`picking_type_code == 'incoming'`)
- **Dropship documents** (`is_dropship == True` — standard Odoo field
  from `stock_dropshipping` module)

> **Dependency**: `stock_dropshipping` added to `kebony_bol_report`
> manifest to ensure `is_dropship` field is available at view
> validation time.

Layout:

```
── Reception Details ──────────────────────────
  Shipping References         Logistics Dates
  ┌──────────────────┐       ┌──────────────────┐
  │ Container #      │       │ Expedition Date   │
  │ Master BOL #     │       │ Arrival Date      │
  └──────────────────┘       │ Delivered Date    │
                             └──────────────────┘
```

View record: `view_picking_form_reception_details` in
`views/stock_picking_view.xml`.

---

## 4. Reception BOL Report

**Report action**: `action_report_reception_bol_us`
**QWeb template**: `report_reception_bol_us` in
`report/bol_reception_us_template.xml`

### Comparison: Expedition vs Reception

| Aspect             | Expedition BOL                  | Reception BOL                        |
|--------------------|---------------------------------|--------------------------------------|
| Direction          | Outgoing (delivery)             | Incoming (receipt)                   |
| Title              | "Bill of Lading (US)"           | "Bill of Lading — Reception (US)"   |
| Identifier         | "Delivery: WH/OUT/xxxxx"       | "Receipt: WH/IN/xxxxx"             |
| Left address       | Warehouse (shipped from)        | Vendor (shipped from)               |
| Right address      | Customer (shipped to)           | Warehouse (received at)             |
| Extra header       | —                               | Container #, Master BOL #           |
| Logistics dates    | —                               | Expedition, Arrival, Delivered      |
| Lot handling       | Lot lines only                  | Lot lines + no-lot lines            |
| Signature block    | Loaded By / Carrier / Customer  | Shipped By / Carrier / Received By  |
| FSC column         | Product → company fallback      | Same fallback                       |

---

## 5. Line Rendering: Lots vs No-Lots

The reception BOL handles two cases:

- **`lot_lines`** = `move_line_ids.filtered(lambda l: l.lot_id)` —
  lines with lot assignment. Shows lot name in the Lot column.
- **`no_lot_lines`** = `move_line_ids.filtered(lambda l: not l.lot_id)` —
  lines without lots. Shows "—" in the Lot column.

This is necessary because incoming receipts may not yet have lot
assignments at the time of printing (before QC / lot creation).

The expedition BOL only renders lot lines (assumes lots are always
assigned on outbound).

---

## 6. Board Count (In-Template Calculation)

Boards are computed inline in QWeb:

```
boards = round(ml.quantity / x_studio_length_1, 0)
```

Where `x_studio_length_1` is the board length in feet from
`product.template`. Falls back to 0 if length is missing.

**Note**: This is a simplified calculation. The full metrics mixin
(`_kebony_boards_from_linear`) has the `ROUND_UP_THRESHOLD = 0.95`
rule. The report uses basic rounding for display purposes.

---

## 7. Odoo Module Reference

| Component              | File                                    | Purpose                              |
|------------------------|-----------------------------------------|--------------------------------------|
| Reception fields (5)   | `models/stock_picking.py`              | Field definitions on `stock.picking` |
| Reception details tab  | `views/stock_picking_view.xml`         | Form view extension (visibility gated)|
| Reception BOL template | `report/bol_reception_us_template.xml` | QWeb report body + wrapper           |
| Report action          | `report/report_us.xml`                 | `ir.actions.report` registration     |
| Mail template          | `data/mail_template_data.xml`          | `mail_template_reception_bol_us`     |

---

## See Also

- [[FSC Certification & Compliance]] — FSC column logic used in this report
- [[Localized Send Framework]] — How the reception BOL template is dispatched
- [[Accounting & Margin Architecture]] — US accounting context
- [[Metrics & Physical Units]] — Full board count calculation with round-up threshold
