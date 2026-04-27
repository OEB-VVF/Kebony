# Sales Area Architecture

**Scope**: All Kebony entities (US + Europe)
**Module**: `kebony_bol_report`
**Dependencies**: `account` (analytic plans)
**Supersedes**: [[Analytical Accounting Architecture]] section 6 (US-only flat list)

---

## 1. Problem Statement

The current design defines 9 flat sales areas for US/Canada only. Europe
needs a hierarchical, geography-flexible structure where:

- A sales area can be a region within a country (e.g. French-speaking Switzerland)
- A sales area can be a whole country (e.g. Denmark)
- A sales area can be a group of countries (e.g. Benelux)
- Areas can be split or merged as the business evolves (Benelux → Belgium + Lux + Netherlands)
- Each area has a manager (employee), with optional sub-areas and sub-managers

The analytical "Sales Area" plan must sit **on top of Country** in the
analytics, not replace it. This ensures that reorganizing sales territories
doesn't break country-level reporting.

---

## 2. Current State

### Studio field
- `x_studio_area_of_sales` — Many2one on `res.partner`, `sale.order`, `account.move`
- 9 values: Central, East Canada, Midwest, N. Rockies, North East, OEM, South East, West, West Canada
- Flat list, no hierarchy, no geography link, no manager

### Code already built (waiting for data)
- Sales area auto-inheritance: partner → SO → SO line → invoice → invoice line
- Accrual settlement wizard groups by sales area analytic account
- Sales dashboard pivot/graph views support sales area grouping
- `x_kebony_sales_area` planned as Many2one to `account.analytic.account`

### What's missing
- Hierarchy (parent/child areas)
- Manager assignment
- Geography flexibility (region, country, group of countries)
- European territories

---

## 3. Target Data Model

### 3.1 `kebony.geo.zone` — Flexible geography table

Purpose: define named geographic zones that can be a sub-country region,
a country, or a group of countries. Decoupled from `res.country` to
allow arbitrary cuts.

| Field            | Type       | Description                                |
|------------------|------------|--------------------------------------------|
| `name`           | Char       | Display name (e.g. "French Switzerland", "Benelux") |
| `code`           | Char       | Short code (e.g. `CH-FR`, `BENELUX`)       |
| `zone_type`      | Selection  | `region` / `country` / `country_group`     |
| `country_ids`    | Many2many  | res.country — which countries this covers  |
| `parent_id`      | Many2one   | Self-referential — optional grouping       |
| `description`    | Text       | Notes (e.g. "cantons: GE, VD, VS, FR, NE, JU") |
| `active`         | Boolean    | Archive flag                               |
| `company_id`     | Many2one   | res.company (multi-company)                |

**Examples:**

| Code      | Name                  | Type          | Countries         | Parent        |
|-----------|-----------------------|---------------|-------------------|---------------|
| `CH-FR`   | French Switzerland    | region        | Switzerland       | `CH`          |
| `CH-DE`   | German Switzerland    | region        | Switzerland       | `CH`          |
| `CH`      | Switzerland           | country       | Switzerland       | —             |
| `FR-NORD` | North France          | region        | France            | `FR`          |
| `FR-SUD`  | Rest of France        | region        | France            | `FR`          |
| `BENELUX` | Benelux               | country_group | BE, NL, LU        | —             |
| `DK`      | Denmark               | country       | Denmark           | `NORDICS`     |
| `NORDICS` | Nordics               | country_group | NO, SE, DK, FI    | —             |

> **Design choice**: `country_ids` is Many2many, not Many2one. A group
> like "Benelux" spans 3 countries. A region like "French Switzerland"
> links to 1 country but doesn't represent the whole country.

> **Why not use `res.country.group`?** Odoo's built-in country groups
> are for fiscal positions and pricelists — they're system-wide and
> shared across modules. We need business-specific zones that can
> be reorganized freely by the CEO without affecting tax rules.

---

### 3.2 `kebony.sales.area` — Sales territory with hierarchy

Purpose: the actual sales territory structure. Links to geography, has
a manager, supports parent/child hierarchy.

| Field                | Type       | Description                              |
|----------------------|------------|------------------------------------------|
| `name`               | Char       | Territory name (e.g. "Benelux", "West")  |
| `code`               | Char       | Short code (e.g. `BENELUX`, `WEST`)      |
| `parent_id`          | Many2one   | Self-referential — parent sales area     |
| `child_ids`          | One2many   | Sub-areas                                |
| `manager_id`         | Many2one   | hr.employee — area manager               |
| `geo_zone_ids`       | Many2many  | kebony.geo.zone — covered geography      |
| `analytic_account_id`| Many2one   | account.analytic.account — for analytics |
| `company_id`         | Many2one   | res.company                              |
| `active`             | Boolean    | Archive flag                             |
| `entity_type`        | Selection  | `us` / `europe` / `all` — visibility     |

**Hierarchy examples:**

```
Europe (VP Sales Europe)
├── Nordics (Regional Manager Nordics)
│   ├── Norway
│   ├── Sweden
│   └── Denmark
├── Benelux (Regional Manager Benelux)
│   ├── Belgium
│   ├── Netherlands
│   └── Luxembourg
├── DACH (Regional Manager DACH)
│   ├── Germany
│   ├── Austria
│   ├── French Switzerland
│   └── German Switzerland
├── France
│   ├── North France
│   └── Rest of France
└── UK & Ireland

US & Canada (VP Sales Americas)
├── North East
├── South East
├── Central
├── Midwest
├── West
├── N. Rockies
├── East Canada
├── West Canada
└── OEM
```

**Rules:**
- A customer (`res.partner`) is assigned to a **leaf** sales area
- Reporting can roll up to any level in the hierarchy
- The `analytic_account_id` links to the analytic plan for financial reporting
- Only leaf areas appear in the analytic plan (parent areas = reporting rollup only)

---

### 3.3 Extend `res.partner`

Replace the current flat Studio field with the new model.

| Field                        | Type       | Description                    |
|------------------------------|------------|--------------------------------|
| `x_kebony_sales_area_id`     | Many2one   | kebony.sales.area              |

> **Migration**: map existing `x_studio_area_of_sales` values to matching
> `kebony.sales.area` records. Keep Studio field read-only for transition
> period, then deprecate.

Auto-inheritance chain (unchanged from current design):
```
res.partner → sale.order → sale.order.line → account.move → account.move.line
```

---

## 4. Relationship to Analytical Accounting

The existing analytical plan architecture has 5 plans:

| Plan | Level | Sales Area interaction |
|------|-------|-----------------------|
| Country | Country | **Independent**. Sales area sits on top. "French Switzerland" → Country = CH. "Benelux" → Countries = BE/NL/LU. |
| BU | Business unit | Independent |
| Sales Area | Territory | **This model.** Leaf areas = analytic accounts. |
| CM Level | P&L waterfall | Independent |
| Distributor | Customer category | Independent |

**Key principle**: Sales Area and Country are **orthogonal**. Reorganizing
sales territories (splitting Benelux, merging Nordics) does not affect
country-level reporting. The `geo_zone_ids` on the sales area provides
the join path when needed.

### Analytic account creation

When a `kebony.sales.area` is created (leaf node), the system auto-creates
a matching `account.analytic.account` under the "Sales Area" plan. This
keeps the analytic plan in sync without manual work.

---

## 5. Business Rules

### Rule 1: Customer assignment at leaf level
Customers are assigned to leaf-level sales areas only. The hierarchy is
for reporting rollup, not for assignment.

### Rule 2: Area determines manager, not the other way around
The `manager_id` on the sales area defines who owns that territory.
This is not the same as `x_studio_sales_representative` (sales rep on
the contact) — one is territory ownership, the other is deal attribution.

### Rule 3: Splitting an area
When the CEO splits "Benelux" into "Belgium + Lux" and "Netherlands":
1. Create 2 new child areas under the existing Benelux parent
2. Reassign customers from Benelux to the appropriate child
3. Benelux becomes a **parent** (reporting rollup) and loses its analytic account
4. New analytic accounts created for the children
5. Historical data stays on the old analytic account — no rewriting history

### Rule 4: Geography flexibility
`kebony.geo.zone` records can be created by authorized users (e.g. COO).
They don't need IT intervention. A zone like "North France" can be defined
with a text description of which departments/regions it covers — we don't
need sub-sub-country admin boundaries in the database.

---

## 6. UI Design

### Sales Area list/tree view (Settings or Sales config)
- Tree view with parent/child indentation
- Columns: name, code, manager, geography, analytic account
- Buttons: create, archive, "Split Area" wizard

### Sales Area on contact form
- Many2one field in the Sales tab (replacing `x_studio_area_of_sales`)
- Domain filter: only leaf areas matching partner's entity/country
- Smart button: "X Customers" count on the sales area form

### Geo Zone configuration (Settings)
- Simple list view: name, code, type, countries, parent
- Rarely edited — setup once, update when territories change

---

## 7. Seed Data — US (migrate from current)

| Code       | Name         | Manager    | Geo Zone     |
|------------|--------------|------------|--------------|
| CENTRAL    | Central      | (assign)   | US regions   |
| EAST-CAN   | East Canada  | (assign)   | Canada East  |
| MIDWEST    | Midwest      | (assign)   | US regions   |
| N-ROCKIES  | N. Rockies   | (assign)   | US regions   |
| NORTH-EAST | North East   | (assign)   | US regions   |
| OEM        | OEM          | (assign)   | All US/CAN   |
| SOUTH-EAST | South East   | (assign)   | US regions   |
| WEST       | West         | (assign)   | US regions   |
| WEST-CAN   | West Canada  | (assign)   | Canada West  |

Europe seed data to be defined with Sales VP after workshop.

---

## 8. Implementation Plan

### Phase 1 — Models + migration
- Create `kebony.geo.zone` and `kebony.sales.area` models
- Seed US sales areas (migrate from Studio field)
- Create `x_kebony_sales_area_id` on `res.partner`
- Map existing `x_studio_area_of_sales` data
- Auto-create analytic accounts under "Sales Area" plan
- Adapt inheritance chain (SO → invoice → lines)

### Phase 2 — Europe
- Define European geo zones with CEO/Sales VP
- Create European sales area hierarchy
- Assign European customers
- Extend sales dashboard for hierarchy rollup

### Phase 3 — Advanced
- "Split Area" wizard (automates customer reassignment)
- Territory map visualization (optional)
- Sales target assignment by area (links to budget/reforecast)

---

## 9. Open Questions

1. **European hierarchy**: exact structure TBD with Sales VP. The model
   supports any depth — 2 levels (region → country) or 3 (region →
   sub-region → micro-zone) work equally well.

2. **OEM**: is OEM a sales area or a sales channel? It spans all geography.
   Current design keeps it as a sales area (US). If Europe has OEM too,
   do we want a separate "Europe OEM" or a cross-entity "OEM" area?

3. **Geo zone granularity**: for "North France" vs "Rest of France" —
   is a text description sufficient, or do we need a formal list of
   departments/postal codes? Text is simpler and more flexible.

4. **Sales rep vs. manager**: confirm these remain separate concepts.
   Manager = territory owner (on sales area). Rep = deal-level
   attribution (on contact). Both inherited to SO/invoice.

---

## See Also

- [[Analytical Accounting Architecture]] — 5-plan structure, Sales Area = Plan 4
- [[Product Master Data]] — Product classification (wood vs. accessory)
- [[Entity Registry]] — Entity types (US, Belgium, Norway)
