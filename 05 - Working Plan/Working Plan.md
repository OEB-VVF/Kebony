
# General loop of development:

- Code to be snapshot in the folder locally by AI
- local code base t be used directly for update by AI
- Commit and push done by User
# **🔷 PHASE 1 — PRODUCT ENRICHMENT (Foundation Layer)**

  

We cannot build DL without product being enriched properly.

  

## **STEP 1 — Add Manufacturing Fields to product.template**

  

Deliverable:

- Python model extension
    
- XML layout
    
- New tab: “Manufacturing”
    
- Fields:
    
    - planning_family_id
        
    - stacking_hours_ref
        
    - autoclave_hours_ref
        
    - dryer_hours_ref
        
    - dryer_hours_equivalent
        
    - minimum_process_qty
        
    - mix_consumption_per_m3
        
    - scrap_internal_percent
        
    - scrap_b_grade_percent
        
    

  

Goal:

Product becomes planning-ready.

  

After this step:

You can visually validate the tab in UI.

  

👉 When ready you say:

**“Step 1 — generate code”**

---

# **🔷 PHASE 2 — CORE STRUCTURAL MODELS**

  

We now create the structural manufacturing object layer.

  

## **STEP 2 — Create DL (Dryer Load) Model**

  

Deliverable:

- Python model
    
- Sequence
    
- Basic tree view
    
- Basic form view
    

  

Fields:

- name (sequence DL-YY-XXXX)
    
- planning_family_id
    
- estimated_start_date
    
- estimated_duration_hours
    
- estimated_finish_date (computed)
    
- total_lm
    
- total_m3
    
- board_count
    
- state (draft / planned / locked / done)
    

  

Tree view must show:

- Name
    
- Family
    
- Start
    
- Finish
    
- m3
    
- State
    

  

Goal:

DL exists as object.

  

👉 “Step 2 — generate DL model”

---

## **STEP 3 — Autoclave Batch Model**

  

Deliverable:

- Python model
    
- Relation to DL
    
- Sequence: DL-XXXX-AC01
    

  

Fields:

- dl_id
    
- name
    
- batch_number
    
- estimated_hours
    
- start_date
    
- finish_date
    

  

Relation:

DL has One2many → autoclave_batch_ids

  

Goal:

We can open DL and see two batch containers.

  

👉 “Step 3 — generate Autoclave model”

---

## **STEP 4 — Process Pack Model**

  

Deliverable:

- Python model
    
- Linked to Autoclave Batch
    
- Sequence: DL-XXXX-AC01-PP01
    

  

Fields:

- autoclave_batch_id
    
- raw_lot_ids (Many2many stock.lot)
    
- total_lm
    
- total_m3
    
- board_count
    
- qc_flag
    

  

Goal:

Inside DL → inside Batch → inside Process Packs → raw lots visible.

  

👉 “Step 4 — generate Process Pack model”

---

# **🔷 PHASE 3 — DL FULL SCREEN**

  

## **STEP 5 — Complete DL Form View Layout**

  

DL form must show:

  

Top:

- Planning info
    
- Dates
    
- Family
    
- Capacity data
    

  

Middle:

Two notebook pages:

Page 1: Autoclave Batches (one2many)

Page 2: Finished Lots (linked via stock.move or MO)

  

Inside each batch:

Inline list of process packs.

  

Goal:

DL becomes operational planning object.

  

👉 “Step 5 — generate DL full XML layout”

---

# **🔷 PHASE 4 — MANUAL DL → MO GENERATION**

  

Now the financial boundary.

  

## **STEP 6 — Generate MO from DL**

  

Deliverable:

Button on DL:

  

“Generate Manufacturing Order”

  

Logic:

- Create 1 MO
    
- Product = family representative product
    
- Quantity = total_lm
    
- Routing = stacking → autoclave → dryer
    
- Link MO to DL
    

  

Add field:

mrp_production_id on DL

  

Goal:

DL becomes atomic MO creator.

  

👉 “Step 6 — generate MO creation logic”

---

## **STEP 7 — DL ↔ MO Sync Engine**

  

We must handle DL changes.

  

Logic:

If DL modified:

- Update MO quantity
    
- Update routing duration
    
- If MO confirmed → block structural edits
    

  

Add DL states:

draft → planned → locked → done (matches implementation)

  

Goal:

Planning flexibility preserved before confirmation.

  

👉 “Step 7 — generate sync logic”

---

# **🔷 PHASE 5 — DEMAND → DL PROPOSAL ENGINE**

  

## **STEP 8 — DL Proposal Wizard**

  

Deliverable:

Wizard that:

- Reads open SO lines + Replenishment
    
- Groups by planning_family
    
- Suggests DL size based on minimum_process_qty
    
- Creates DL draft
    

  

Manual override allowed.

  

Goal:

Semi-automatic family grouping.

  

👉 “Step 8 — generate DL proposal wizard”

---

# **🔷 PHASE 6 — MES FEEDBACK**

  

## **STEP 9 — MES Data Integration Layer**

  

Question you asked:

  

> Is stock intake update native?

  

Yes.

  

If MES posts:

- workorder finish
    
- production done
    
- lot creation
    

  

Odoo natively:

- creates stock.move
    
- updates quants
    
- creates valuation layer
    

  

What we add:

  

DL update logic on:

- MO done
    
- lot creation
    

  

DL fields updated:

- actual_start_date
    
- actual_finish_date
    
- actual_m3
    
- actual_dryer_hours
    

  

Goal:

DL reflects reality after MES run.

  

👉 “Step 9 — generate DL completion hook”

---

# **🔷 PHASE 7 — INVENTORY ENRICHMENT (Advanced)**

  

After MO completion:

- Snapshot cubic
    
- Snapshot board count
    
- Snapshot capacity equivalent
    

  

We enrich stock.move at production time.

  

👉 That comes after MES integration.

---

# **🔷 Important Clarification (Your Question)**

  

You asked:

  

> Is MES feedback native?

  

Odoo natively:

- handles MO completion
    
- handles stock moves
    
- handles lot tracking
    
- handles valuation
    

  

What is NOT native:

- DL awareness
    
- Capacity snapshot storage
    
- Batch reconstruction logic
    

  

That’s what we add.