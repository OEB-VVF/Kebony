# Electronic Signatures — Odoo Sign Rollout

> Version 1.0 — Migration from DocuSign to Odoo Sign
> Module: sign, sale, purchase | Updated: 2026-04-02

---

## 1. Executive Summary

Kebony currently uses **DocuSign** for electronic signatures. Odoo includes a built-in **Sign** module as part of the Enterprise subscription — unlimited signatures, no per-envelope fees, and tight integration with Sales, Purchase, and HR.

This document outlines the functionality, compares it to DocuSign, and gathers requirements from the team.

---

## 2. What Odoo Sign Does

### 2.1 Core Workflow

1. **Upload** a PDF document (or pick from the Documents app)
2. **Design** the template — drag-and-drop signature fields, initials, text, dates, checkboxes
3. **Assign roles** — each field belongs to a role (Customer, Vendor, Employee, HR…)
4. **Send** — recipients get a secure link by email (or WhatsApp)
5. **Sign** — recipients draw, type, or upload their signature
6. **Done** — all parties receive the signed PDF + a **Certificate of Completion** (audit trail)

### 2.2 Key Features

| Feature | Detail |
|---------|--------|
| **Reusable templates** | Upload once, send many times with different recipients |
| **Multi-signer** | Multiple signers with enforced sequential order |
| **Smart prefilling** | Fields auto-populate from Odoo data (contact name, address, SO total…) |
| **Multi-document bundles** | Combine multiple PDFs into one signature request |
| **Validity & reminders** | Set expiration dates + automatic reminder emails |
| **Carbon copy** | Designated followers receive copies without signing |
| **Refusal** | Signers can refuse and provide a reason |
| **Signature methods** | Draw, type (handwriting fonts), or upload scanned image |
| **Audit trail** | Certificate of Completion with signatory hash and timestamps |

### 2.3 Authentication Options

| Method | Module | Notes |
|--------|--------|-------|
| **Email link** | `sign` (core) | Default — unique secure link per signer |
| **SMS code** | `sign_sms` | 6-digit OTP via SMS (requires IAP credits) |
| **itsme** | `sign_itsme` | EU identity verification (BE, NL, EU/EEA) |

---

## 3. Integration with Odoo Modules

### 3.1 Purchase Orders (optional)

From any PO, use **⚙ Actions → Request Signature** to send the PO for vendor/customer signature. The signed document attaches to the PO record.

**Use case**: formal PO acknowledgement from suppliers.

### 3.2 Sale Orders / Quotations (optional)

Two levels available:

| Option | How | Sign Module Required? |
|--------|-----|----------------------|
| **Portal signature** | Customer signs directly on the quotation portal page to confirm the order | No — built into Sales settings |
| **Full Sign template** | Attach a formal Sign template to the SO, send via email for signature | Yes |

Portal signature is enabled in **Sales → Settings → Quotations & Orders → Online Signature**.

### 3.3 Ad-hoc Documents

Upload any PDF — contracts, NDAs, agreements, policy acknowledgements — and send for signature. No module integration needed, works standalone.

### 3.4 HR Contracts (future)

If HR module is used, Sign integrates natively with employee contract signing (dual-role: Employee + HR Responsible).

---

## 4. Benchmark — Odoo Sign vs DocuSign

| Criteria | Odoo Sign | DocuSign |
|----------|-----------|----------|
| **Cost** | Included in Enterprise — no extra fees | Per-envelope pricing, escalates with volume |
| **Signature limits** | Unlimited | Limited envelopes per plan |
| **Odoo integration** | Native — PO, SO, HR, Documents, CRM | Requires connector / manual upload |
| **Template editor** | Drag-and-drop, smart prefill from Odoo | More advanced conditional logic |
| **EU compliance** | eIDAS, ESIGN Act | Same + HIPAA (extra cost) |
| **Bulk send** | Limited — no mass-send feature | PowerForms, bulk send to hundreds |
| **Mobile** | Mobile-friendly web | Dedicated mobile apps |
| **Audit trail** | Certificate of Completion | More granular timestamped events |
| **Third-party integrations** | Odoo ecosystem only | 900+ integrations |
| **Workflow automation** | Via Server Actions / custom dev | Native workflow builder |

### 4.1 What We Gain

- **Zero per-signature cost** — unlimited documents
- **Signed docs link back to Odoo records** — PO, SO, contact
- **Single platform** — no context switching between Odoo and DocuSign
- **Templates reuse Odoo data** — auto-fill customer name, address, amounts

### 4.2 What We Lose

- No bulk/mass-send for hundreds of recipients
- Fewer authentication options (no KBA)
- No dedicated mobile app (web works on mobile)
- Simpler audit trail (still legally compliant)

**Verdict**: for Kebony's use case (PO/SO signatures + ad-hoc documents), Odoo Sign fully covers the need.

---

## 5. Questions for the Team

Please answer the following so we can configure Sign correctly:

### 5.1 Purchase Order Signatures

> **Do you want vendors/customers to sign Purchase Orders electronically?**
>
> This adds a "Request Signature" button on POs. The signed document attaches to the PO record.
>
> ☐ Yes, activate PO signatures
> ☐ No, not needed

### 5.2 Sale Order / Quotation Signatures

> **Do you want customers to sign quotations/sale orders to confirm?**
>
> **Option A** — Portal signature (customer signs on the Odoo portal page)
> **Option B** — Full Sign template (formal PDF sent by email for signature)
>
> ☐ Option A — Portal signature
> ☐ Option B — Full Sign template
> ☐ Both options available
> ☐ No, not needed

### 5.3 Other Documents

> **What other documents do you currently send for signature via DocuSign?**
>
> Examples: contracts, NDAs, policy acknowledgements, terms & conditions…
>
> If you have **recurring templates** (documents you send regularly), please email a sample PDF to **oeb@kebony.com** so we can set them up as Odoo Sign templates.

### 5.4 SMS Verification

> **Do you need SMS code verification for signers?**
>
> This sends a 6-digit code by SMS before the signer can access the document. Adds security but requires SMS credits.
>
> ☐ Yes
> ☐ No — email link is sufficient

---

## 6. Next Steps

| # | Action | Timeline |
|---|--------|----------|
| 1 | Answer questions above | This week |
| 2 | Install, configure + training guide | Next week |
| 3 | Go-live + deactivate DocuSign | Next week |

A **training guide** with screenshots of the full signing flow will be provided at go-live.

Templates can be created anytime — just upload a PDF and drag fields onto it. If you need help setting one up, email the PDF to **oeb@kebony.com**.
