# Localized Send Framework

**Scope**: All Kebony entities (global framework, US templates implemented)
**Module**: `kebony_bol_report`
**Entity filter**: Keyed by `x_kebony_entity_type` on `res.company`

---

## 1. Overview

Kebony operates multiple legal entities (INC, BNV, Holding, KAS, NAS).
Each entity needs entity-specific PDF reports and email templates when
sending customer-facing documents (invoices, quotations, BOLs).

The Localized Send Framework routes the Odoo **Send** button to the
correct mail template and PDF report based on the company's
`x_kebony_entity_type`. Currently only **US (INC)** templates are
implemented. Adding other entities requires only XML + dictionary entries.

---

## 2. Architecture

Two class-level dictionaries on `res.company` drive the routing:

- **`_KEBONY_TEMPLATE_MAP`** — maps `(entity_type, doc_type)` →
  `mail.template` XML ID
- **`_KEBONY_REPORT_MAP`** — maps `(entity_type, doc_type)` →
  `ir.actions.report` XML ID

Two helper methods resolve the lookups:

- **`_get_kebony_mail_template(doc_type)`** — returns `mail.template`
  record or empty recordset
- **`_get_kebony_report(doc_type)`** — returns `ir.actions.report`
  record or empty recordset

**Fallback**: If the entity has no mapping (or `x_kebony_entity_type`
is not set), all overrides fall back to Odoo's standard behaviour
via `super()`.

---

## 3. Document Types

| `doc_type` key       | Odoo Model       | Description                     |
|----------------------|------------------|---------------------------------|
| `invoice`            | `account.move`   | Customer invoice                |
| `quotation`          | `sale.order`     | Draft quotation                 |
| `order_confirmation` | `sale.order`     | Confirmed sale order            |
| `bol`                | `stock.picking`  | Expedition BOL (outgoing)       |
| `reception_bol`      | `stock.picking`  | Reception BOL (incoming)        |

---

## 4. Template Map (Current State)

### Entity: `inc` (Kebony Inc. — US)

| doc_type             | Mail Template XML ID                                     | Report XML ID                                            |
|----------------------|----------------------------------------------------------|----------------------------------------------------------|
| `invoice`            | `kebony_bol_report.mail_template_invoice_us`            | `kebony_bol_report.action_report_invoice_us`            |
| `quotation`          | `kebony_bol_report.mail_template_quotation_us`          | `kebony_bol_report.action_report_draft_quotation_us`    |
| `order_confirmation` | `kebony_bol_report.mail_template_order_confirmation_us` | `kebony_bol_report.action_report_order_confirmation_us` |
| `bol`                | `kebony_bol_report.mail_template_bol_us`                | `kebony_bol_report.action_report_bill_of_lading_us`     |
| `reception_bol`      | `kebony_bol_report.mail_template_reception_bol_us`      | `kebony_bol_report.action_report_reception_bol_us`      |

### Other entities

`bnv`, `holding`, `kas`, `nas` — **not yet implemented**. Adding them
is a matter of creating templates + dictionary entries (see section 6).

---

## 5. Override Points (3 Integration Hooks)

Each Odoo document flow has its own override that calls into the
framework:

### 5a. Invoices: `account.move.send`

File: `models/account_move_send.py`

| Method                           | Purpose                           |
|----------------------------------|-----------------------------------|
| `_get_default_pdf_report_id(move)` | Returns entity-specific PDF report |
| `_get_default_mail_template_id(move)` | Returns entity-specific mail template |

Fallback: `super()` which uses Odoo's partner → journal → default
cascade.

### 5b. Quotations / Order Confirmations: `sale.order`

File: `models/sale_order.py`

| Method                | Purpose                                |
|-----------------------|----------------------------------------|
| `_find_mail_template()` | Selects entity template by SO state  |

Logic: `"order_confirmation"` if `state == 'sale'`, else `"quotation"`.
Fallback: `super()._find_mail_template()`.

### 5c. Deliveries (BOL): `stock.picking`

File: `models/stock_picking.py`

| Method                        | Purpose                                   |
|-------------------------------|-------------------------------------------|
| `_send_confirmation_email()` | Auto-send on delivery validation           |
| `action_send_bol()`          | Manual "Send BOL" button (mail composer)   |

Only applies to outgoing pickings (`picking_type_id.code == 'outgoing'`).

---

## 6. Adding a New Entity

Step-by-step procedure:

1. **Create mail templates** in `data/mail_template_data.xml` with
   entity-specific subject/body content
2. **Create QWeb report templates** in `report/` (body + wrapper)
3. **Register `ir.actions.report` records** in `report/report_us.xml`
   (or a new entity-specific file)
4. **Add the entity key** to both `_KEBONY_TEMPLATE_MAP` and
   `_KEBONY_REPORT_MAP` in `models/res_company.py`
5. **No additional Python code needed** — the framework routes
   automatically based on the dictionary entries

---

## 7. Odoo Module Reference

| Component               | File                         | Purpose                                     |
|-------------------------|------------------------------|---------------------------------------------|
| Template/Report maps    | `models/res_company.py`     | `_KEBONY_TEMPLATE_MAP`, `_KEBONY_REPORT_MAP`|
| Invoice send override   | `models/account_move_send.py`| PDF report + mail template for invoices     |
| Quotation/OC override   | `models/sale_order.py`      | `_find_mail_template()` for sales           |
| BOL send override       | `models/stock_picking.py`   | Auto-send + manual Send BOL button          |
| Mail template records   | `data/mail_template_data.xml`| 5 US templates (noupdate=1)                |
| Report action records   | `report/report_us.xml`      | `ir.actions.report` registrations           |

---

## See Also

- [[Entity Registry]] — List of all entities and their `x_kebony_entity_type` codes
- [[Reception BOL & Inbound Logistics]] — Newest document type in the framework
- [[Metrics & Physical Units]] — Formatting reference for this vault
