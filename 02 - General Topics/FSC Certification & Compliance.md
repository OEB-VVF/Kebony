# FSC Certification & Compliance

**Scope**: All Kebony entities (global)
**Module**: `kebony_bol_report`
**Entity filter**: None — applies to all companies

---

## 1. Overview

Kebony products carry FSC (Forest Stewardship Council) chain-of-custody
certification. The FSC code must appear on outbound documents (BOLs,
invoices) to prove compliance.

Three Studio fields carry FSC data at two levels: **product** and
**company**. A fallback resolution pattern determines which value prints
on each document.

---

## 2. Field Registry

All fields are defined via Odoo Studio (`x_studio_*` prefix):

| Label              | Field                  | Model              | Type | Description                                    |
|--------------------|------------------------|--------------------|------|------------------------------------------------|
| FSC Code (Product) | `x_studio_fsc_`       | `product.template` | Char | Product-level FSC claim code (e.g. "FSC Mix 70%") |
| FSC Number         | `x_studio_fsc_number` | `product.template` | Char | FSC certificate number (e.g. "FSC-C123456")    |
| FSC Code (Company) | `x_studio_fsc_code`   | `res.company`      | Char | Company-level FSC code. Global fallback.       |

**Important distinction**: `x_studio_fsc_` is the **claim type** (what
appears on BOLs). `x_studio_fsc_number` is the **certificate identifier**
(what appears on invoices). These are separate compliance concepts.

---

## 3. Fallback Resolution Pattern

The same product → company fallback is used on both BOL reports:

```
fsc_product = product.product_tmpl_id.x_studio_fsc_
fsc_company = picking.company_id.x_studio_fsc_code
display     = fsc_product OR fsc_company OR ''
```

**Priority**: Product-level takes precedence. If product has no FSC
code, the company-level code applies. If neither is set, the column
is left blank.

This allows mixed-FSC inventory (some products certified, others not)
while maintaining a company-wide default.

---

## 4. Usage by Report

| Report               | Field Used           | Fallback                        | File                                  |
|----------------------|----------------------|---------------------------------|---------------------------------------|
| Expedition BOL (US)  | `x_studio_fsc_`     | `x_studio_fsc_code` (company)  | `report/bol_us_template.xml`          |
| Reception BOL (US)   | `x_studio_fsc_`     | `x_studio_fsc_code` (company)  | `report/bol_reception_us_template.xml`|
| Invoice (US)         | `x_studio_fsc_number`| None (blank if missing)        | `report/invoice_us_report.xml`        |

**Note**: The Invoice uses a different field (`fsc_number`) and has
**no company fallback**. This is intentional — the certificate number
is product-specific and should not be defaulted from the company.

---

## 5. Design Decisions

- **No Python logic involved.** The fallback is purely in QWeb template
  conditionals. No computed field is created.
- **Product-level FSC takes precedence.** This supports mixed inventory
  where only some products carry certification.
- **Invoice uses a separate field.** The claim code (BOL) and certificate
  number (invoice) serve different regulatory purposes.

---

## See Also

- [[Product Master Data]] — Product field registry (FSC fields should be
  added to the Compliance section)
- [[Entity Registry]] — Entity types that may use FSC
