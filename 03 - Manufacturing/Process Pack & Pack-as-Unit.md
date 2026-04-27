## **1. Purpose**

This spec formalizes how a **Process Pack** represents the physical stacking
and autoclave unit at Kebony, how pack-level quantities map to Manufacturing
Order quantities and BoM consumption, and how planned vs. actual values flow
back from MES.

It closes gaps identified during end-to-end MO testing:
- UoM mismatch (`total_m3` written as if it were the product's UoM)
- Consumption of the **master** parent SKU instead of the length-specific one
- No "pack" unit of input or output — only loose m³ / LM
- No planned/actual distinction on pack quantities

This doc is the source of truth for the `kebony.process.pack` model.
Complements `Dryer-Centric Architecture.md` (geometry) and `Metrics & Physical
Units.md` (board/LM/m³ conversions).

---
## **2. The Physical Flow (Recap)**

```
White Wood pack(s)
    │  stacking
    ▼
Process Pack (full or half)      ← assembled on a chariot
    │  autoclave (+ Ready-Mix)
    │  dry
    ▼
Destack
    │
    ├─▶ 1..N Rough-Sawn packs (if producing RS)
    └─▶ 1..N Finished-Goods packs (if producing FG, after machining)
```

Key rules:
- Input and output are **always whole packs** (full or half on input; integer count on output).
- Pack size in boards is a **product attribute** (`x_studio_boards_per_pack`).
- Boards are **conserved 1-to-1 in the autoclave step**. The kebonisation scrap
  (internal + B-grade) lives on the **planning family** and represents drying
  losses plus QC downgrades, not a unit conversion.
- 99 boards vs 100 — *"shit happens"*. The plan is full packs; the actual
  is whatever MES reports. Both are recorded.

---
## **3. Pack Sizing — The Two Numbers**

Every wood product must expose:

| Field (on `product.template`) | Meaning |
|---|---|
| `x_studio_boards_per_pack` | Boards in one full pack of this product (e.g. 95 for `1931-I-10`, 162 for `1127-M-3.5`) |
| `x_studio_length_m` | Board length in meters |
| `x_studio_volume_m3` | m³ per linear meter of this board (despite the stored label) |

Derived pack metrics:

```
pack_boards   = x_studio_boards_per_pack
pack_lm       = pack_boards × x_studio_length_m
pack_m3       = pack_lm × x_studio_volume_m3
```

**WW (raw White Wood) gap**: WW master SKUs today have
`x_studio_boards_per_pack = 0` and `x_studio_volume_m3 = 0`. Since WW becomes
RS without changing board dimensions, WW must inherit the same values as the
same-length RS product. This is a data-cleanup task, not a code one.

---
## **4. The Process Pack Model**

### 4.1 Identity

| Field | Type | Purpose |
|---|---|---|
| `autoclave_batch_id` | m2o | Parent AC batch (AC1 or AC2) |
| `pack_number` | int | Sequence inside the AC (1, 2, …) |
| `pack_unit` | selection | **`'full'` (1.0)** or **`'half'` (0.5)**. Only two legal values. |
| `pile_position` | int | Which pile in the chariot (1–4, depends on length) |
| `height_position` | int | Which layer in the pile (1–3 for full; 1–6 for half stacks) |

### 4.2 Input side (what goes in)

| Field | Type | Note |
|---|---|---|
| `input_product_id` | m2o product.product | WW parent when producing RS; RS parent when producing FG |
| `input_pack_qty` | float | Derived from `pack_unit`: 1.0 or 0.5. Not user-editable. |
| `input_boards_planned` | int | = `input_pack_qty × input_product.boards_per_pack` |
| `input_lm_planned` | float | = `input_boards_planned × input_product.length_m` |
| `input_m3_planned` | float | = `input_lm_planned × input_product.volume_m3` |

### 4.3 Output side (what comes out)

| Field | Type | Note |
|---|---|---|
| `product_id` | m2o product.product | **Output** product (RS or FG) — existing field, kept. |
| `output_pack_qty_planned` | int | Full output packs planned (e.g. 1, 2) |
| `output_boards_planned` | int | = `output_pack_qty_planned × product.boards_per_pack` |
| `output_lm_planned` | float | = `output_boards_planned × product.length_m` |
| `output_m3_planned` | float | = `output_lm_planned × product.volume_m3` |

### 4.4 Actuals (from MES, Phase 9)

Every `_planned` field has an `_actual` twin. Actuals override planned in
reporting once MES reports them. Examples:
- `input_boards_actual`
- `output_pack_qty_actual` (fractional allowed — e.g. 0.99 if 99/100 boards made it)
- `output_boards_actual`
- `output_lm_actual`, `output_m3_actual`

Mirrors the existing `estimated_duration_hours` / `actual_duration_hours`
pattern on `kebony.dryer.load`.

### 4.5 Compatibility fields

To avoid breaking existing views, keep these as **computed**:

| Legacy field | New computation |
|---|---|
| `total_lm` | `= output_lm_planned` |
| `total_m3` | `= output_m3_planned` |
| `board_count` | `= output_boards_planned` |
| `actual_lm` / `actual_m3` / `actual_board_count` | from `_actual` fields |
| `is_half_pack` | `= (pack_unit == 'half')` |

### 4.6 Constraints

1. `pack_unit ∈ {'full', 'half'}`
2. `output_pack_qty_planned ≥ 1` when a product is set
3. Per autoclave batch: `sum(pack_unit_value grouped by pile_position) ≤ chariot_height_units`
   (see §4.7). Soft warning, not hard error — overrides happen.
4. Per autoclave batch: `pile_count ≤ floor(chariot_length_m / product_length_m)` (see §4.7).
   Soft warning.
5. `input_product_id = product.kebony_parent_id.product_variant_ids[:1]` by
   default (auto-filled on product set, editable if needed).

### 4.7 Chariot Geometry — Shared System Setting

The autoclave chariot is one physical object shared by all planning families.
Its dimensions live as **system parameters** (`ir.config_parameter`), exposed
in **Settings → Manufacturing → Autoclave Chariot**, not on the planning
family:

| `ir.config_parameter` key | Default | Used by |
|---|---|---|
| `kebony.chariot_length_m` | `12.8` | Pile-count constraint |
| `kebony.chariot_height_units` | `3.0` | Height-stack constraint (units of process-pack, full=1.0 / half=0.5) |

Future extension (thickness-aware stacking): add
`kebony.chariot_height_mm` and derive `height_units` per product as
`floor(chariot_height_mm / product.x_studio_thickness_mm)`. Until needed,
`chariot_height_units` stays the direct editable knob.

Helpers:
- `env['ir.config_parameter'].sudo().get_param('kebony.chariot_length_m', 12.8)`
- Wrap in a small helper on `kebony.autoclave.batch` or a mixin for cached access.

---
## **5. BoM & MO Quantity — Fixing the UoM Mismatch**

### 5.1 The bug (pre-fix)

`action_create_mo` on `kebony.dryer.load`:

```python
mo_vals = {
    "product_id": product.id,
    "product_qty": total_m3,              # ← m³ value
    "product_uom_id": product.uom_id.id,  # ← but UoM is LF or m !
    ...
}
```

For `1931-I-10` (UoM = LF), a 5 m³ pack became a 5 LF MO → BoM math inflated
consumption by 12× (1 LF ≈ 12 m for this product).

### 5.2 The rule (post-fix)

MO qty must always be expressed in the **output product's native UoM**:

```python
qty_in_product_uom = sum(pp.output_lm_planned for pp in packs_of_this_product)
if product.uom_id.name == 'LF':
    qty_in_product_uom = qty_in_lm / 0.3048  # m → LF
mo_vals = {
    "product_id": product.id,
    "product_qty": qty_in_product_uom,
    "product_uom_id": product.uom_id.id,
    ...
}
```

(Equivalent: use Odoo's `uom._compute_quantity(qty_m, target_uom)`.)

### 5.3 BoM line semantics

BoM lines on an FG/RS are **per 1 unit of output in output UoM**.

- Parent wood line: `qty = 1 / (1 - total_scrap_pct)` in the **parent's UoM**
  (already in meters for Metric RS, LF/m for Imperial — UoM categories match
  since they're both length).
- Ready-Mix line: `qty = mix_consumption_per_m3 × volume_m3_per_output_unit`
  (kg, so we need to express consumption **per 1 output LF or m**, not per m³).

Concrete example for `1931-I-10` (1 LF output):
- Length per LF = 0.3048 m; volume per LF = `0.3048 × 0.005` ≈ 0.001524 m³
- Ready-Mix line qty = `676 × 0.001524` ≈ **1.03 kg per LF output**
- Parent `1931-M-3.05` qty = `1 / (1 - 0.039)` ≈ **1.0406 LF per LF output**

`_create_chemical_line` must convert `mix_consumption_per_m3` (kg/m³) into
kg per output-unit using `product.x_studio_volume_m3 × length_per_uom_unit`.

### 5.4 MO generation from a DL

```
for each output product P across all packs in the DL:
    output_qty_in_P_uom = Σ output_lm_planned (packs of P) / uom_conversion(m → P.uom)
    create MO(
        product = P,
        qty = output_qty_in_P_uom,
        uom = P.uom,
        bom = bom_for(P),
        dryer_load = this DL,
    )
```

One MO per distinct output product (unchanged from today's logic). Multiple
packs of the same product → their `output_lm_planned` sums.

---
## **6. DL / AC / PP View: Consumption Summary**

Today the DL form shows FG output only. After this spec, each view surfaces
both sides of the transform:

**Process Pack row (list)**:
```
Pack #1  [full]  1929-M-3.05 → 1931-M-3.05   in: 95 boards / 290 m / 1.45 m³
                                              out: 95 boards / 290 m / 1.45 m³
```

**Autoclave Batch header (computed aggregates)**:
```
AC1   4 packs (3 full + 1 half)   in: 333 boards / 1015 m / 5.08 m³
                                  out: 333 boards / 1015 m / 5.08 m³
Ready-Mix needed: 3 432 kg
```

**Dryer Load header**:
```
DL-26-0001   2 ACs, 8 packs   plan in: 760 boards  plan out: 730 boards (3.9% scrap)
                              actual in: — (awaiting MES)
```

The MO already carries raw material moves; those appear under the MO, not
directly on the DL. The DL views show the **planned** reality pre-MO and the
**actual** reality once MES reports.

---
## **7. Data Cleanup Dependencies**

Before this spec can be fully exercised in production:

1. **WW SKUs must have `x_studio_boards_per_pack` and `x_studio_volume_m3`**
   populated (inherit from same-length RS).
2. **`kebony_parent_id` must point to the length-specific parent**, not the
   master. (E.g. `1131-I-10 → 1931-M-3.05`, not `1931-M`.) The populate
   scripts already do this; the manual overrides from test-setup that pointed
   to masters (e.g. `1127-M-3.5 → 1127-M`) must be corrected.
3. **KRRS1 Metric FGs need `kebony_parent_id` linked** — the populate cascade
   missed them. Follow-up task.

---
## **8. Implementation Checklist**

Code changes (target: `kebony_manufacturing` addon):

- [ ] Add `res.config.settings` fields for `kebony.chariot_length_m` (default 12.8) and `kebony.chariot_height_units` (default 3.0), stored as `ir.config_parameter`. Expose under Settings → Manufacturing → Autoclave Chariot.
- [ ] Add `pack_unit` (Selection: full/half) on `kebony.process.pack`, default `'full'`
- [ ] Add `input_product_id`, `input_pack_qty` (computed from pack_unit)
- [ ] Add `output_pack_qty_planned` (integer)
- [ ] Add planned/actual pair for boards, lm, m3 (input + output)
- [ ] Refactor `total_lm` / `total_m3` / `board_count` / `is_half_pack` as computed
- [ ] `_create_chemical_line` — qty in kg per output-unit (not per m³)
- [ ] `_create_raw_wood_line` — already reads `kebony_parent_id` ✅ (committed)
- [ ] `action_create_mo` on `kebony.dryer.load` — qty in product's native UoM
- [ ] Views: add input/output summary columns on PP list; aggregates on AC and DL
- [ ] Constraint: `pack_unit` ∈ {full, half}; soft-warn on chariot capacity overflow
- [ ] Migration: backfill `pack_unit='full'` on existing records; `output_pack_qty_planned`
      approx from `board_count / pack_boards` rounded

Tests:
- [ ] Create DL with 1 full + 1 half pack → verify MO qty in LF and in m
- [ ] Verify Ready-Mix consumption ≈ `mix_per_m3 × output_m3` (not 12× inflated)
- [ ] Verify parent wood consumption ≈ `output_boards × (1 + scrap)`
- [ ] Verify DL view shows plan vs. actual once MES `_actual` fields are populated
