# Sales Responsibility Tracking

## Context

Tom requested (30 March 2026) that all sales be tracked and linked to the Kebony employee who owns the deal. Currently three roles exist but only two are captured in Odoo.

## Three Roles in Every Sale

| Role | Who | Example | Current Odoo Field |
|------|-----|---------|-------------------|
| **Kebony Sales Responsible** | Internal employee who owns the deal | Sami Kivisto, Andy Hehl, Jim Dowd | **NONE** |
| **Back Office Person** | Admin staff processing the order | Bethany Dunnam, Briawna Willingham | `user_id` (mislabeled "Salesperson") |
| **External Sales Agent** | Partner company representing Kebony | Rob Langenfeld Sales, Mako, Onshore | `x_studio_sales_representative` |

## Proposed Solution

### Field mapping (after change)

| Field | Technical Name | Type | Contains |
|-------|---------------|------|----------|
| **Sales Responsible** | `x_kebony_sales_responsible_id` | Many2one → res.users | **NEW** — Kebony employee who owns the deal |
| **Back Office Person** | `user_id` | Many2one → res.users | **RELABEL** from "Salesperson" — admin handler |
| **External Sales Agent** | `x_studio_sales_representative` | Many2one → res.partner | **KEEP** — external agent company (US commissions) |

### Migration

1. Relabel `user_id` from "Salesperson" to "Back Office Person" (no data change)
2. Create `x_kebony_sales_responsible_id` on sale.order and account.move
3. Add propagation: SO → Invoice → Credit Note
4. Make required on SO confirmation
5. Add to pivot/reporting views

### Process change

- Back office fills **Sales Responsible** when creating an SO (the Kebony employee who owns the customer)
- Cannot confirm SO without it
- Back Office Person auto-fills with logged-in user (unchanged)
- External Sales Agent stays optional (US-only, commission tracking)

## Effort

**2-3 hours** total implementation.

## Decision Needed

Validate with Joris & Sami, then brief Andy and back-office teams.
