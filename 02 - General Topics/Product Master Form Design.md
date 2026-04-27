# Product Master Form Design

> Version 0.2 — Decisions locked, ready for build
> Module: `kebony_manufacturing` (and successor of Studio product form)
> Created: 2026-04-27 · Author: VVF Consulting · Decisions logged 2026-04-27 (see §8)

---

## 1. Goal & Scope

### 1.1 Goal

Replace today's SKU-centric, Studio-bloated product form with a **master-centric** form that:

1. Makes the **Master** the daily working unit (not the SKU)
2. Surfaces all length children inline with stock and status
3. Enables bulk operations (create length, propagate update, generate Imperial twins) without opening every child record
4. Visualizes the **manufacturing chain** (upstream raw, downstream consumers) directly on the form
5. Enforces **lifecycle gates** so a Master cannot be activated with missing critical fields

### 1.2 Non-goals (this iteration)

- **Description localization by country/language** — deferred to a separate child model. See `project_product_description_localization.md`. The current iteration uses a single `description_stem` per Master.
- **Pricing matrix** by length — handled by Odoo's pricelist mechanism, not redesigned here.
- **BoM / MO management** — accessed via smart button to existing screens, not rebuilt.
- **Replacing the SKU form entirely** — the SKU form remains for engineers and direct edits; the master form is the daily work surface.

### 1.3 Background and supporting docs

- [[Product Master Data]] §17 — high-level architectural intent (master-centric, length matrix, lifecycle, propagation)
- `project_product_master_cleanup_state.md` — Phase A migration state (the data shape this form expects)
- `project_studio_fields_cleanup.md` — the Studio duplicate-field problem this form replaces
- `project_product_master_config_checklist.md` — required field checklist for activation gates
- `reference_ax_product_model.md` — 3-level hierarchy, `kebony_parent_id` dual semantics, AX decimeter encoding

---

## 2. Form Architecture

### 2.1 Header

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [Master Item]  1127  ·  Kebony Scots Pine Character 22×100 mm           │
│  [Lifecycle: ●Active]  [SP]  [Decking]  [Wood]                            │
│                                                                          │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ │
│  │ 622 m³  │ │ 14 SKUs  │ │ 3 SOs  │ │ 1 PO   │ │ 2 MOs    │ │ Chain  │ │
│  │ on hand │ │ children │ │ open   │ │ open   │ │ open     │ │ →      │ │
│  └─────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘ └────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Smart buttons** (top right, all link-through):
- **On Hand** — sum of `qty_available` across all length children, in m³
- **Children** — count of length-variant SKUs (drilldown to length matrix)
- **Open SOs** — count of sale.order.line referencing any child, drilldown
- **Open POs** — count of purchase.order.line referencing any child, drilldown
- **Open MOs** — count of mrp.production referencing any child as `product_id`
- **Pricelists** — coverage display "3/12 children priced" — clicking opens a per-length × per-pricelist grid showing where prices are explicit vs. inherited (DECIDED 2026-04-27)
- **Chain →** — opens the Chain tab (§2.7)

**Lifecycle badge** (clickable, opens state-transition dialog):
- ● Draft (grey) · ● Active (green) · ● Phasing-out (amber) · ● Archived (red)

### 2.2 Tabs (notebook)

| # | Tab | Purpose |
|---|---|---|
| 1 | General | Identity, classification, lifecycle |
| 2 | Geometry | Cross-section dimensions (constant across lengths) |
| 3 | Supply Chain | Procurement, supplier, route, lead time, supply-chain rule |
| 4 | Sales | Pricelists, customer category, sales description, market portfolios |
| 5 | Manufacturing | `kebony_parent_id` chain, planning family, BoM, yield, scrap |
| 6 | Inventory | UoM, packaging, tracking, certifications |
| 7 | Accounting | Category, valuation, GL routing |
| 8 | **Lengths** | **Length matrix — the central UX win** |
| 9 | Chain | Upstream / downstream visualization |
| 10 | Notes & History | Free notes, full chatter |

### 2.3 Tab 1 — General

| Field | Source | Editable | Notes |
|---|---|---|---|
| Master Item Code | `default_code` | Yes (Draft only) | e.g. `1127` |
| Description Stem | `description_stem` (NEW) | Yes | Drives all length descriptions — see §6 |
| Wood Species | `x_studio_word_species` | Yes | Scots Pine / Radiata / N.A. |
| Production Family | `x_studio_production_chain` | Yes | Character / Clear / N.A. |
| Application | `x_studio_many2one_field_3oj…` | Yes | Decking / Cladding / etc. |
| Shape | `x_studio_shape` | Yes | 27 values |
| Shape Value | `x_studio_many2one_field_6up…` | Yes | Profile geometry |
| Classification | `x_studio_product_classification` | Yes | wood / accessory |
| Master Lifecycle | `kebony_master_lifecycle` (NEW) | Via state buttons | Draft / Active / Phasing-out / Archived |
| SKU Lifecycle (default) | `x_studio_product_lifecycle` | Yes | Default for newly-created length children (Introduction / Growth / Mature / Decline / Abandon / Decommissioned) |

### 2.4 Tab 2 — Geometry

Cross-section dimensions are **constant across all length children of a Master**. Edit once, propagate via the "Push to children" button (§5.3).

| Field | Source | Unit | Notes |
|---|---|---|---|
| Thickness | `x_studio_thickness_mm` | mm | Engineering metric base |
| Width | `x_studio_width_mm_1` | mm | Engineering metric base |
| Volume Ratio | `x_studio_volume_m3` | m³/lm | Critical — drives all margin calc |
| Density | `x_studio_density_kgm3_2` | kg/m³ | |
| Square Factor | `x_studio_square_factor_1` | lm/m² | Computed if Width set |
| Section m² | `x_studio_width_x_thickness_m2_1` | m² | Computed if Thickness × Width set |

**Imperial mirror** (collapsed by default, "Show Imperial values" toggle):
| Thickness in | `x_studio_thickness` | inches |
| Width in | `x_studio_width` | inches |
| Density lb/ft³ | `x_studio_density_lbft3` | lb/ft³ |

Imperial values **derive from metric** by default — locked unless "Override" checkbox is ticked (rare; only for US-specific products).

### 2.5 Tab 3 — Supply Chain

| Field | Source | Notes |
|---|---|---|
| Supply Chain Rule | TBD (new field) | MTO / ATO-WW / ATO-BW / MTS — see [[Product Master Data]] §5.6.1 |
| Buffer Product | TBD (new field) | Required for ATO and MTS |
| Min Stock Level | TBD (new field) | Per buffer product |
| Lead Time (days) | `sale_delay` | Commercial lead time per supply chain rule |
| Primary Supplier | first `seller_ids` | Inline list shown below |
| Vendor Pricelist | `seller_ids` (M2O list) | Editable inline |
| Route | `route_ids` | Buy / Manufacture / MTO / Replenish-on-Order |

### 2.6 Tab 4 — Sales

| Field | Source | Notes |
|---|---|---|
| Sales Description | `description_sale` | Shown on quotations |
| Customer Category | `x_studio_customer_catagory` (typo permanent) | Distributor / Direct / etc. |
| Market Portfolios | `x_studio_market_portfolios` | M2M — Export, France, Nordic, DACH, Benelux, US |
| Matching Accessories | `x_studio_matching_accessories` | M2M to other product templates |
| Services Available | `x_studio_services_available` | M2M — fire retardant, brushing, etc. |
| Sale Enabled | `sale_ok` | Boolean |
| HS Code (NO) | `hs_code` | Customs |
| HS Code (EU) | `intrastat_code_id` | Intrastat |
| Country of Origin | `country_of_origin` | Customs |

### 2.7 Tab 5 — Manufacturing

| Field | Source | Notes |
|---|---|---|
| Planning Family | `kebony_planning_family_id` | Required for activation |
| Manufacturing Parent | `kebony_parent_id` | **Dual semantics — see §2.7.1** |
| Yield Rule | `kebony_yield_rule` (NEW) | "trim_10cm" (Scots Pine) / "rs_chemistry" (Radiata) / "none" |
| Internal Scrap % | `kebony_family_scrap_internal_percent` (related) | Read-only from family |
| B-Grade Scrap % | `kebony_family_scrap_b_grade_percent` (related) | Read-only from family |
| BoM Template | smart button | Opens BoM if exists, "Create BoM" wizard if not |

#### 2.7.1 Dual Semantics Inline Warning

When the user clicks the `kebony_parent_id` field, a small inline alert appears:

> ⚠️ **Dual semantics**: this field carries different meaning depending on measurement system.
> · Metric SKU → points to **another Metric SKU** (raw material consumed in BoM)
> · Imperial SKU → points to **the Metric twin** (system-conversion link, NOT a raw material)
>
> Do not "fix" an Imperial SKU's parent thinking it's a bug — it is by design.

This callout is non-dismissable (always visible when the field is in focus) — see [[Product Master Data]] §5.6.A for full doctrine.

### 2.8 Tab 6 — Inventory

| Field | Source | Notes |
|---|---|---|
| Default UoM | `uom_id` | `LM` (metric) or `LF` (imperial) |
| Packagings | `uom_ids` | M2M — Pack of N × X lm, Board of X lm, etc. |
| Boards per Pack | `x_studio_boards_per_pack` | Integer |
| Pcs per Layer | `x_studio_pcslayer` | |
| Layers per Pallet | `x_studio_number_of_layers_1` | |
| Tracking | `tracking` | by_lots (mandatory for wood) |
| Lot Valuated | `lot_valuated` | True (FIFO per lot) |
| Storable | `is_storable` | True for sellables |
| FSC / PEFC | `kebony_certifications` (NEW M2M) | Both required for wood — see `project_certifications_fsc_pefc.md` |

### 2.9 Tab 7 — Accounting

| Field | Source | Notes |
|---|---|---|
| Product Category | `categ_id` | Drives GL routing |
| Stock Valuation Account | related from category | Read-only display |
| Stock Variation Account | related from category | Read-only display |
| **Production Cost Account (WIP)** | related from category | Read-only display — **must be set or MOs post no JE** |
| Income Account (override) | `property_account_income_id` | Optional |
| Expense Account (override) | `property_account_expense_id` | Optional |

A **red banner** appears at the top of the tab if `property_stock_account_production_cost_id` is missing on the category. Activation gate blocks Draft → Active until resolved (see §3.2).

### 2.10 Tab 8 — Lengths (the central UX)

The length matrix lists every length child SKU of this Master, **metric and imperial side by side** when they share a logical length, separately when they don't.

```
┌──────┬──────────────┬────────┬───────────┬──────────────┬────────┬───────────┬────────┬──────────┐
│      │ Metric       │ Stock  │ Lifecycle │ Imperial     │ Stock  │ Lifecycle │ Has    │          │
│ Slot │ SKU          │ (lm)   │           │ SKU          │ (lf)   │           │ BoM    │ Action   │
├──────┼──────────────┼────────┼───────────┼──────────────┼────────┼───────────┼────────┼──────────┤
│ 2.4  │ 1127-M-2.4   │ 142    │ Mature    │ —            │ —      │ —         │ ✅      │ [edit]   │
│ 3.0  │ 1127-M-3.0   │ 480    │ Mature    │ 1127-I-10    │ 220    │ Mature    │ ✅      │ [edit]   │
│ 3.2  │ 1127-M-3.2   │ 0      │ Mature    │ —            │ —      │ —         │ ✅      │ [edit]   │
│ 3.5  │ 1127-M-3.5   │ 38     │ Growth    │ —            │ —      │ —         │ ✅      │ [edit]   │
│ 3.6  │ 1127-M-3.6   │ 0      │ Growth    │ 1127-I-12    │ 80     │ Mature    │ ✅      │ [edit]   │
│ 4.2  │ —            │ —      │ —         │ 1127-I-14    │ 35     │ Mature    │ ⚠️      │ [edit]   │
│ 4.8  │ —            │ —      │ —         │ 1127-I-16    │ 0      │ Mature    │ ❌      │ [edit]   │
└──────┴──────────────┴────────┴───────────┴──────────────┴────────┴───────────┴────────┴──────────┘

[+ Create Length]  [Generate Imperial Twins]  [Bulk Edit Selection]  [Push Geometry to Children]
```

**Slot logic**: pair metric and imperial when their physical lengths match (3.0 m ≈ 10 ft = 3.048 m, within ±5% tolerance). If only one system has a length at this slot, the other column shows `—`.

**Inline editing** is disabled by default — clicking Edit opens the SKU form. Bulk operations are the primary path for lengths-level changes.

**Status icons**:
- ✅ Has BoM
- ⚠️ BoM exists but coefficient mismatch (yield ≠ rule)
- ❌ No BoM (cannot produce / cannot ship as MTO)

**Buttons under matrix** — see §5 for full wizard specs.

### 2.11 Tab 9 — Chain

Visualizes the manufacturing flow this Master is part of. Three horizontal lanes:

```
┌────────────────────────────────────────────────────────────────┐
│ ── Upstream (what I am made FROM) ─────────────────────────── │
│                                                                │
│  [Master 1003: White Wood Scots Pine Σ4×Σ22cm]                 │
│       ↓ −10 cm yield trim                                      │
│  [THIS MASTER: 1127 — Scots Pine Character 22×100]             │
│                                                                │
│ ── This Master's lengths ──────────────────────────────────── │
│                                                                │
│  Metric: 2.4 · 3.0 · 3.2 · 3.5 · 3.6 · 3.9 · 4.2 · 4.5         │
│  Imperial: 8 · 10 · 12 · 14 · 16                               │
│                                                                │
│ ── Downstream (Masters that consume me as raw) ─────────────  │
│                                                                │
│  (none — this is a finished product)                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

For a raw white-wood Master, the downstream lane lists the FG Masters that consume it. For a Rough-Sawn Master, both lanes are populated (upstream WW, downstream FG).

**Drilldown**: click any Master tile to navigate to that Master's form. Click the lengths band to drop into the Lengths tab of the current Master.

**Implementation note**: this is a computed view, not stored. Source is `kebony_parent_id` aggregated across all length children — both directions:
- Upstream = `set(child.kebony_parent_id.x_studio_master_item_code_1 for child in self.length_child_ids if metric)`
- Downstream = `set(other.x_studio_master_item_code_1 for other where other.length_child.kebony_parent_id in self.length_child_ids)`

Cached with TTL ≤ 5 min to avoid heavy query on every form open.

### 2.12 Tab 10 — Notes & History

- Free `notes` text field
- Full chatter (mail.thread) — covers writes on the Master itself
- **Aggregated child chatter** (NEW) — collapsed by default; shows "23 changes on length children in last 30 days" with a button to expand. Implementation: a wrapper that pulls `mail.message` for all `length_child_ids`.

---

## 3. Master-Level Lifecycle

### 3.1 States

| State | Color | Meaning | Sales / Production impact |
|---|---|---|---|
| Draft | grey | Newly created, fields incomplete | `sale_ok = False`, `purchase_ok = False`, cannot be on MO/SO/PO |
| Active | green | Validated, full operations | All flags True |
| Phasing-out | amber | No new orders, finish existing | `sale_ok = False`, `purchase_ok = False`, existing MOs/SOs continue |
| Archived | red | Terminal | All flags False, `active = False` on Master and all children |

### 3.2 Transitions and gates

```
Draft ──[Activate]──> Active ──[Start Phase-out]──> Phasing-out ──[Archive]──> Archived
                         │                                                       │
                         └──[Archive Direct]─────────────────────────────────────┘

Reverse (Active → Draft) only via "Reset to Draft" button, requires:
  - No length children with stock
  - No open SOs / POs / MOs referencing any child
```

**Activation policy (DECIDED 2026-04-27 — soft validation, NOT hard block):**

The transition Draft → Active is **never blocked** by the system. The user is always free to save and operate. Instead, missing mandatory fields trigger:

1. A **red banner at the top of the form** listing every missing field, kept visible until resolved
2. A **⚠️ icon next to the lifecycle badge** signalling validation failure on this Master
3. An entry in the **Migration Audit report** (§5.5) — aggregated view of all Masters with warnings

Mandatory-field checklist (drives the banner content):
- Planning Family set
- Classification = wood OR accessory
- `x_studio_volume_m3` set (wood only)
- `kebony_parent_id` set (FG/RS only — not raw)
- Product Category set with `property_stock_account_production_cost_id` populated (wood/manufactured only)
- At least 1 length child exists
- At least 1 length child has a BoM (manufactured only)
- FSC + PEFC certifications set (wood only)
- `description_stem` populated

**Rationale**: legacy Masters being migrated will arrive with gaps; halting operations is unacceptable. Visibility-driven cleanup via the audit report is the chosen mechanism. The gate exists on screen, not in the database.

**Phase-out gate**: no validation — soft transition. UI shows confirmation dialog warning that no new SOs can be opened.

**Archive gate**: requires either no children with stock OR explicit "Archive with stock write-down" confirmation. The latter triggers a write-down JE (out of scope for this design — separate accounting decision).

### 3.3 Cascade behavior

- **Master → Active**: existing Draft children are NOT auto-activated; each child has its own SKU-level lifecycle (`x_studio_product_lifecycle` — Introduction → Mature → Decommissioned)
- **Master → Phasing-out**: all children with `sale_ok = True` get `sale_ok = False` set; children remain Active for fulfilment
- **Master → Archived**: all children get `active = False`; activation timestamp stored for audit

---

## 4. Length Matrix Detail

### 4.1 Data model

The length matrix is a computed view sourced from a new One2many relationship:

```python
class ProductTemplate(models.Model):
    _inherit = "product.template"

    # On a Master record only:
    length_child_ids = fields.One2many(
        "product.template",
        "x_studio_master_item_code_1",
        string="Length Children",
        domain=[("x_studio_is_master_item", "=", False)],
    )

    length_matrix_html = fields.Html(compute="_compute_length_matrix_html", sanitize=False)
```

The matrix HTML is rendered server-side for the Lengths tab. Each row pairs metric and imperial when physical length matches (within tolerance).

### 4.2 Pairing tolerance

```python
PAIRING_TOLERANCE_M = 0.05  # 5 cm

def pair_metric_imperial(children):
    metric = sorted([c for c in children if c.measurement == "Metric"], key=lambda c: c.length_m)
    imperial = [c for c in children if c.measurement == "Imperial"]
    for m in metric:
        match = next((i for i in imperial if abs(i.length_m - m.length_m) <= PAIRING_TOLERANCE_M), None)
        yield (m, match)
        if match: imperial.remove(match)
    for i in imperial:
        yield (None, i)  # imperial-only rows
```

### 4.3 Stock context (DECIDED 2026-04-27)

The Stock columns show **all internal stock**, but **broken down by company AND by location** — not just a single aggregate number.

**Display model**: each child row's Stock cell expands to a small breakdown popover:

```
1127-M-3.0 — On hand: 622 lm

  Kebony BNV (BE)            342 lm
    └ Kallo / Stock           320 lm
    └ Kallo / B-grade          22 lm
  Kebony Inc (US)             280 lm
    └ TabakNatie / Stock      280 lm
```

The headline number in the column = total across all companies and locations. Click expands the breakdown.

**Implementation**: a single SQL query against `stock.quant` grouped by `(product_id, company_id, location_id)` for all internal locations of all companies, rendered into the popover HTML. Cached with TTL ≤ 5 min.

No filter dropdown — the user always sees the full picture.

---

## 5. Wizards

### 5.1 Create Length wizard

**Trigger**: "+ Create Length" button on the Lengths tab.

**Inputs**:
- Length value (Float, required)
- Measurement system (Metric / Imperial, default = same as Master's primary system)
- Auto-fill from Master (checkbox, default ON) — if ticked, copies all Geometry, Supply Chain, Sales, Manufacturing, Inventory, Accounting fields from the Master to the new SKU
- Description override (Char, optional) — defaults to `Master.description_stem + " | " + length_label`

**Behavior**:
1. Validates length is unique within Master
2. Generates `default_code` = `{master}-{M|I}-{length_str}` (e.g. `1127-M-3.5`, `1127-I-10`)
3. Creates `product.template` with `x_studio_master_item_code_1` set to Master
4. Auto-resolves `kebony_parent_id`:
   - For Metric: same length on the parent Master (e.g. `1003-M-3.6` for `1127-M-3.5`, applying yield trim rule)
   - For Imperial: nearest Metric twin per §3.5 of [[Product Master Data]] — flagged "proposed, requires validation"
5. Generates BoM if `kebony_parent_id` is resolved and parent has a BoM template (uses Push BoM wizard logic on planning family)
6. Sets `x_studio_product_lifecycle = "Introduction"`

**Validation**:
- Length must be > 0
- Length must not duplicate an existing child
- Master must be Active or Draft (Phasing-out / Archived → blocked)

### 5.2 Generate Imperial Twins wizard (DECIDED 2026-04-27)

**Gating**: a new Boolean field on Master, `kebony_imperial_twins_applicable`:
- **Default True** for FG and RS Masters
- **Default False** for White Wood Masters
- Editable — user can override (e.g. an experimental WW that ships to US)

The "Generate Imperial Twins" button is **hidden** when this flag is False. White Wood Masters never see the option, removing a class of user error at source.

**Trigger**: "Generate Imperial Twins" button on the Lengths tab — only visible when `kebony_imperial_twins_applicable = True` AND Master has at least one Metric child.

**Inputs**: a checklist of standard foot lengths (8, 10, 12, 14, 16). Pre-selected lengths = those that have a metric twin within tolerance and aren't already created.

**Behavior**:
1. For each selected foot length, find the nearest Metric child (within 0.6 m)
2. Create Imperial SKU `{master}-I-{ft_int}` with:
   - `x_studio_length_1` = ft value
   - `x_studio_length_m` = ft × 0.3048
   - `kebony_parent_id` = the matched Metric SKU (best-guess)
   - All other fields auto-filled from the Master
3. Flag the new SKU's `kebony_parent_id` as "proposed" via a Boolean `kebony_parent_id_proposed = True` (NEW field)
4. **Chatter entry on the new SKU**: `"Twin proposed: 1127-I-10 → 1127-M-3.0 (auto-resolved by Generate Imperial Twins wizard)"`

**Validation flow (implicit + chatter audit)**:
- The "proposed" flag clears the moment a planner opens the SKU and saves any field — implicit confirmation
- A chatter entry is written: `"Parent confirmed by {user} on {date}"`
- No explicit "Validate" button — the work the planner does on the SKU IS the validation
- Audit trail comes from the chatter pair (one auto-generated, one on first save)

**Bulk audit**: a report `Imperial Twins — Pending Confirmation` lists every SKU still flagged `kebony_parent_id_proposed = True`, sorted by age. Master Data Guardian works through it as backlog.

### 5.3 Push to Children wizard

**Trigger**: "Push Geometry to Children" / "Push Supply Chain to Children" / "Push Sales to Children" buttons (one per logically-grouped propagation domain).

**Inputs**: which fields to push (checklist), pre-selected based on the calling tab.

**Behavior** (dry-run preview → confirm):
1. Lists all length children
2. Shows side-by-side current vs proposed value per field per child
3. Highlights children with manual overrides (`description_override`, `x_studio_volume_m3_override`, etc. — TBD whether to support overrides)
4. Confirm → writes the new value to each child, with chatter entry on each: "Field X pushed from Master {master} on {date} by {user}"

**Field propagation table** (default rules — overridable in wizard):

| Field | Propagates? | Notes |
|---|---|---|
| description_stem | ✅ Always | The whole point of the model |
| x_studio_volume_m3 | ✅ Always | Constant per cross-section |
| x_studio_thickness_mm / width_mm | ✅ Always | Constant per cross-section |
| x_studio_density_kgm3_2 | ✅ Always | Constant per species |
| x_studio_boards_per_pack | ⚠️ Usually | May vary if pack design changes per length |
| x_studio_classification | ✅ Always | |
| x_studio_word_species | ✅ Always | |
| Planning Family | ✅ Always | |
| FSC / PEFC certifications | ✅ Always | |
| Product Category | ✅ Always | |
| Sales Description (`description_sale`) | ✅ Always | |
| Customer Category | ✅ Always | |
| Market Portfolios | ✅ Always | |
| HS Code | ✅ Always | |
| Country of Origin | ✅ Always | |
| **`kebony_parent_id`** | ❌ Never | Length-specific — never propagated from Master |
| **`x_studio_length_m` / `x_studio_length_1`** | ❌ Never | Length-specific by definition |
| **`description_full`** | ❌ Never (computed) | Auto-derives from stem + length |
| **`standard_price`** | ❌ Never | FIFO — irrelevant under our valuation method |

### 5.4 Bulk Edit wizard

**Trigger**: "Bulk Edit Selection" button — enabled when ≥ 2 rows selected in the Lengths matrix.

**Inputs**:
- One field at a time (selected from a dropdown of allowed fields)
- New value
- Optional: skip-children-with-this-value-different (for safe re-runs)

**Behavior**: applies the same change to each selected child, with chatter entry per child.

**Allowed fields**: any field NOT in the "always propagates from Master" list — i.e. fields that legitimately vary per length:
- `kebony_parent_id` (with the dual-semantics warning)
- `x_studio_product_lifecycle`
- `x_studio_boards_per_pack`
- `seller_ids` (for length-specific suppliers)
- Per-length pricing overrides (if any)

---

## 6. Description Model

### 6.1 New fields on `product.template`

| Field | Type | On Master | On SKU | Notes |
|---|---|---|---|---|
| `description_stem` | Char | ✅ Editable | ❌ Not present | The single source of truth for the prefix |
| `description_full` | Char (computed, stored) | Mirror of stem | Computed | `stem + " \| " + length_label` |
| `description_override` | Char | ❌ Not present | ✅ Editable (unless locked) | Optional per-SKU escape hatch; blank by default |
| `description_lock_overrides` | Boolean | ✅ Editable | ❌ N/A | **DECIDED 2026-04-27** — when True, no child SKU of this Master may have `description_override` set; enforced via `@api.constrains`. Default False. Use case: lock luxury / regulated product lines to strict description consistency. |
| `length_label` | Char (computed) | ❌ N/A | Computed | `"3.5 m"` or `"10 ft"` based on measurement system |

### 6.2 Compute logic

```python
@api.depends("x_studio_master_item_code_1.description_stem", "length_label", "description_override")
def _compute_description_full(self):
    for sku in self:
        if sku.description_override:
            sku.description_full = sku.description_override
            continue
        master = sku.x_studio_master_item_code_1
        stem = master.description_stem if master else ""
        sku.description_full = f"{stem} | {sku.length_label}" if stem and sku.length_label else (stem or "")
```

### 6.3 Migration of existing `x_studio_description`

The existing per-SKU `x_studio_description` field is migrated as follows:

1. **Pre-migration**: dump all current `x_studio_description` values to a CSV for audit
2. **Stem extraction**: per Master, pick the most-common prefix among children's descriptions (split at " | " or by length-suffix detection); set as `description_stem`
3. **Per-SKU validation**: compute `description_full` for each child; compare to existing `x_studio_description`; for each mismatch, set `description_override` to preserve the original value
4. **Post-migration**: `x_studio_description` becomes a read-only view of `description_full` OR is retired (depends on whether external integrations read it)

This is a separate migration script, not part of the form code.

### 6.4 Localization extension point (deferred)

The `description_stem` field is the **default** value. A future child model `kebony.product.description.localization` (`master_id`, `country_id`, `lang_id`, `description_stem`) will hold per-(country, lang) overrides. The compute on `description_full` will then resolve via:

1. Match on (current_country, current_lang) → use that stem
2. Match on (current_lang) only → use that stem
3. Fall back to the default `description_stem` on the Master

**Critical**: the current iteration must NOT hard-code `description_full` to read only `master.description_stem`. The compute should call a method that future-proofs the resolution chain:

```python
def _get_resolved_description_stem(self):
    """Returns the appropriate description_stem for the current context.
    Currently returns master.description_stem; will resolve via localization
    child model when that is built."""
    return self.x_studio_master_item_code_1.description_stem
```

This is the extension point. See `project_product_description_localization.md`.

---

## 7. Studio Field Cleanup (pulled in)

The redesign is the natural moment to retire the 18+ duplicate-label Studio fields documented in `project_studio_fields_cleanup.md`.

### 7.1 Approach

Per-pair decision (made during this work, captured in a CSV):

| Pair | Action |
|---|---|
| `description` (native) + `x_studio_description` | Keep `x_studio_description` until full migration to computed `description_full`; then retire |
| `x_studio_rough_sawn_parent_id` + `x_studio_rough_sawn_parent_id_3` | Audit which has data; retain the one in active use, archive the other |
| `x_studio_density_kgm3` (mislabelled "Density, lb/ft3") + `x_studio_density_kgm3_2` | Relabel `_kgm3` to fix the label, then retire `_kgm3_2` |
| ... | (full inventory in the cleanup memory) |

### 7.2 Execution

A separate Shell script renames or removes Studio field labels via XML-RPC. Data preservation is mandatory — no field with active data is deleted; the field is renamed (e.g. `Description (legacy)`) and hidden from views.

This is sub-task of the form redesign and runs in Phase 5 (see §9).

---

## 8. Decisions Log

All open questions resolved 2026-04-27 with Olivier (CFO, VVF Consulting). Decisions are baked into the design above.

| # | Question | Decision |
|---|---|---|
| 1 | Stock filter context | **All-internal, broken down by company AND by location** in a popover (no filter dropdown — always full picture). See §4.3. |
| 2 | Per-SKU description override | **Yes — `description_override` is the escape hatch**, blank by default. Plus a **Master-level flag `description_lock_overrides`** to forbid overrides on a per-Master basis. See §6.1. |
| 3 | Activation gate strictness | **Soft validation, never blocks save.** Red banner + ⚠️ on lifecycle badge + Migration Audit report aggregating all warnings. Visibility-driven cleanup. See §3.2. |
| 4 | Pricelist Coverage smart button | **Surface it.** Header smart button: "Pricelists: 3/12 children priced". Drilldown to a per-length × per-pricelist grid. (Implementation note added to §2.1.) |
| 5 | Imperial twin validation | **Implicit + chatter audit.** Wizard generates twins, writes a chatter entry "Twin proposed: X → Y". On first save by a planner, the proposed flag clears and a "Parent confirmed" chatter entry is written. No explicit Validate button. **Plus: gating flag `kebony_imperial_twins_applicable`** — default True for FG/RS, False for WW; wizard hidden when False. See §5.2. |
| 6 | Phase-out → Archive transition | **Always manual.** No auto-transition even at stock=0. Notification only. See §3.2. |
| 7 | Aggregated child chatter window | **30 days.** No pagination at this stage; revisit if performance issues surface in UAT. See §2.12. |
| 8 | Master creation path | **Bulk import first** (the Phase A migration writes Masters directly). Once data is in, the **new Master form becomes the day-to-day creation entry point** — no more Studio-import workflow for new Masters. See §1.1. |

These decisions are now part of the build spec. Deviations during implementation require explicit re-discussion.

---

## 9. Implementation Phasing

Total estimate: **9–11 working days** of focused build, plus testing and iteration.

### Phase 1 — Data model and migrations (1.5 days)

- Add new fields: `description_stem`, `description_full`, `description_override`, `length_label`, `kebony_master_lifecycle`, `kebony_yield_rule`, `kebony_parent_id_proposed`, `length_child_ids`, `kebony_certifications`
- Migration script: extract `description_stem` from existing `x_studio_description`; populate `length_child_ids` from `x_studio_master_item_code_1`; flag mismatches
- Unit tests for compute logic on `description_full`
- Rebuild `length_matrix_html` compute
- **Deliverable**: data model + migration runs cleanly on test instance

### Phase 2 — Master form structure (2 days)

- Replace the Studio form for Master records (`x_studio_is_master_item = True`)
- Build all 10 tabs with field mappings per §2
- Smart buttons in header
- Inline dual-semantics warning on `kebony_parent_id`
- **Deliverable**: form opens cleanly, all fields edit/save, badges and smart buttons work

### Phase 3 — Length matrix (1.5 days)

- Length-pairing algorithm (§4.2)
- HTML rendering with stock figures and status icons
- Context filter dropdown (company / plant / location)
- Inline action buttons (edit, create, generate, bulk-edit)
- **Deliverable**: matrix renders correctly for any Master, drilldowns work

### Phase 4 — Wizards (2.5 days)

- Create Length wizard (§5.1)
- Generate Imperial Twins wizard (§5.2)
- Push to Children wizard with dry-run preview (§5.3)
- Bulk Edit wizard (§5.4)
- **Deliverable**: all 4 wizards functional, with audit/chatter entries

### Phase 5 — Lifecycle, gates, Studio cleanup (1.5 days)

- Master lifecycle states with state-buttons
- Activation gate validator (red ✗ checklist)
- Cascade behaviors (Phase-out → child sale_ok = False, etc.)
- Studio duplicate-field cleanup script (one-time)
- **Deliverable**: lifecycle works, gates block correctly, Studio field warnings resolved on next build

### Phase 6 — Chain visualization + polish (1 day)

- Chain tab rendering (§2.11) with cached upstream/downstream resolution
- Aggregated child chatter widget
- Final UX polish (icons, spacing, colors)
- **Deliverable**: full form ready for user acceptance

### Phase 7 — UAT + iteration (1 day buffer)

- Walk through with COO / Production Planning
- Issue list + fixes

### Out of scope / follow-on

- Country/language description localization (separate model + UI iteration)
- Master form for non-wood (accessories) — needs separate review
- Pricing matrix screen — separate doc

---

## 10. Sign-off

This design must be reviewed and approved by:

| Role | Why |
|---|---|
| Olivier (CFO) | Architectural decisions, accounting impact |
| COO | Daily operational fit, lifecycle gates, supply-chain rule mapping |
| Production Planning | Length matrix usability, wizard ergonomics |
| Master Data Guardian (TBN) | Field registry consistency, migration safety |

Sign-off captures:
- Tab structure and field placement
- Activation gate criteria
- Wizard behaviors (especially propagation rules in §5.3)
- Phasing and timeline

Once signed off, this doc becomes the **build spec** — deviations during implementation require explicit approval.

---

## See Also

- [[Product Master Data]] §17 — high-level architectural intent
- `project_product_master_cleanup_state.md` — Phase A migration (data this form expects)
- `project_studio_fields_cleanup.md` — Studio duplicate cleanup (pulled in by Phase 5)
- `project_product_master_config_checklist.md` — required fields for activation gate
- `project_product_description_localization.md` — deferred i18n extension
