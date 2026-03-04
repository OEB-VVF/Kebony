
**Conceptual Reference White Paper – Odoo 19 (V1.2 – Consolidated)**

---
## **1. Purpose of This Document**

This document defines the **conceptual manufacturing landscape of Kebony**, independent of any ERP or MES implementation.

Its objectives are to:

- Establish a **single shared truth** of how Kebony produces    
- Describe **physical flows, inventories, and transformations**
- Clarify **planning, capacity, and cost drivers**
- Define **system boundaries** between Odoo, MES, and external partners  
- 
This document is intentionally **non-technical**:
- No Odoo models
- No fields
- No configuration choices

 It defines _what is true_, not _how it is implemented_.

---
## **2. Guiding Design Principles**

### **2.1 Physical Reality First**

Kebony manufacturing is a **flow process with batching, waiting zones, and bottlenecks**.
Any system must conform to this reality.
### **2.2 Separation of Responsibilities**

- **MES** captures what _physically happens_
- **Odoo** plans, values, traces, and audits
- External partners execute defined transformations
### **2.3 Planning Is Structural**

Production objects (packs, loads, batches) exist because they are **planning and capacity primitives**, not because they are convenient labels.
### **2.4 Traceability Is Mandatory**

End-to-end traceability (FSC / PEFC) is a **first-class design constraint**.

---
## **3. Global End-to-End Manufacturing Landscape**

Kebony operates **two interdependent material flows**:
### **3.1 Wood Flow**

Suppliers
  ↓
Inbound Logistics (3PL / Plant)
  ↓
Production (4 core stages)
  ↓
External Machining (RDK)
  ↓
Finished Goods Inventory (Optional)
  ↓
  OPTIONAL (external future Finishing Treatment)
  ↓
Customer Shipment

### **3.2 Chemical Flow (Internal Supply Chain)**

Chemical Suppliers
  ↓
Raw Chemical Inventory
  ↓
Mix Production
  ↓
Ready-Mix Tank Inventory
  ↓
Autoclave Consumption

## **4. Raw Materials & Inbound Landscape**

### **4.1 White Wood Families**

Kebony purchases _white wood_ in two distinct operational forms:

| **Species** | **Product Line** | **Origin**  | **State at Reception** |
| ----------- | ---------------- | ----------- | ---------------------- |
| Radiata     | **Clear**        | New Zealand | Rough lumber — requires post-kebonisation machining (profiling, planing) |
| Scots Pine  | **Character**    | Sweden      | Pre-machined (planed, profiled) — some products may need cut-to-length at RDK |

Although commercially similar, they behave **very differently** in production and planning.

---
### **4.2 Inbound Logistics & Quality Gates**

Inbound materials may arrive at:

- **TabakNatie** (external 3PL, reception & QC)
- **Kallo Plant** (direct reception)

Suppliers provide a **picking list**, used to preload a _draft reception_.
Final acceptance is confirmed after **quantity and quality checks**.

Quality deviations may immediately generate:

- B-grade material
- Short lengths

These are treated as **normal stock movements**, not exceptions.

---

## **5. Production Landscape – Physical Reality**

Kebony production consists of **four core physical stages**:
### **5.1 Entry Stacking (Process Pack Creation)**

- Formation of **process packs** (boards sorted by planning family)
- **Primary QC gate** — every board is inspected on the stacking machine
- Board-by-board inspection triggers **3 stock transfers**: A-Grade (continues), B-Grade (different valuation), Reject (scrap / cut-off)
- No packaging materials consumed at this stage

### **5.2 Autoclave (Chemical Impregnation)**

- Single autoclave (feeder to the dryer — **not** the primary bottleneck)
- Cycle time depends on species:
    - Radiata: short
    - Scots Pine: long (×2–3)
- Consumes **ready-mix chemical** (one mix recipe for all production; what varies by family is autoclave duration)
- Requires minimum mix availability to operate
### **5.3 Dryer (Time-Based Transformation — Primary Bottleneck)**

- Three dryers — **the primary bottleneck** defining throughput and economics
- **One dryer load = two autoclave charges** (the atomic planning unit)
- Significant waiting zones required (one space for one autoclave charge to complete one dryer load)
- Long, species-dependent elapsed time (up to ~80 hours per dryer load, to be confirmed)
### **5.4 Exit Stacking / Destacking & Packaging**

- Creation of **Finished Good Packs** (sellable packs)
- Performed on the **same stacking machine** as entry stacking (separate operation)
- Consumption of packaging materials:
    - Plastic foil
    - Strips
    - Pallet beams
- **Board-by-board QC** — same inspection as entry stacking, same 3-way grading (A-Grade / B-Grade / Scrap)
- Possible downgrade to B-grade or short length
## **6. Operational Impact of Species Choice & Product Families**

Although Radiata and Scots Pine are both classified as “white wood”, they have **fundamentally different operational and economic impacts** on Kebony’s production system.

These differences are driven not only by species, but also by **board dimensions**, which together determine how materials can be processed through constrained resources.

---
### **6.1 Species-Driven Time Consumption**

Impregnation and drying times depend on:
- the **wood species** (Radiata vs Scots Pine)
- the **dimensions of the boards** (thickness, section)

As a result:

- **Scots Pine**    
    - Shorter supply lead time
    - Pre-machined at reception
    - **Significantly longer autoclave and dryer cycles**
    - Consumes **2 to 3 times more bottleneck time**
    
- **Radiata**
    
    - Longer supply lead time
    - Rough lumber
    - Faster internal processing
    - Frees constrained resources more quickly
    - Requires downstream machining
    
This difference is **not primarily visible in variable costs** (energy, utilities), but has a **major impact on fixed-cost absorption**, as constrained resources are occupied for longer periods.
  

> At Kebony, species choice primarily changes how fast the factory is consumed, not how much material or energy is used.

---

### **6.2 Product Families & Compatibility Constraints**

Autoclave and dryer operations cannot process arbitrary products together.
Both resources can only handle **homogeneous “families” of products**, defined by:

- species
- board dimensions
- impregnation and drying profiles

This introduces a **family compatibility rule**:

> Only products belonging to the same processing family can be grouped within the same autoclave load and dryer load.

This constraint has **structural consequences**:

- It limits how production can be mixed    
- It affects achievable batch sizes
- It shapes stock formation and replenishment logic

---

### **6.3 Minimum Process Quantities (Structural Constraint)**

Because:

- a **dryer load requires two autoclave charges**, and    
- autoclave / dryer loads must be **family-homogeneous**

The system implicitly defines a **minimum process quantity per product family**.

In practice:
- Production below this minimum is **not physically feasible** 
- Make-to-stock and replenishment rules must respect this threshold
- Minimum order quantities and safety stock levels may be driven by **process constraints**, not commercial preferences
    

This minimum process quantity becomes the **true atomic unit of production** for planning purposes.
    
---

## **7. Inventory & Location Topology**

At any moment, Kebony inventory may exist in:

- **Kallo** (plant)    
- **TabakNatie** (3PL)
- **RDK** (machining & outbound partner)
- Future finishing partners (fire retardant, coloring)

Inventory states include:

- Available
- In process
- Waiting for synchronization
- Quarantine
- Downgraded (B-grade)
- Externally held but owned

Ownership, physical location, and valuation are **distinct dimensions**.
## **8. B-Grade Conceptual Model**

B-grade is:
- The **same product**
- In a **different quality location**    
- With a **different valuation**

Operationally:
- Triggered by quality control
- Executed via internal stock transfers
- Causes value adjustment, not loss of traceability

This preserves:

- Auditability
- Margin transparency
- Certification continuity

---

## **9. Chemical Landscape & Mix Production**

### **9.1 Two-Level Chemical Model**

Chemical exists in two distinct inventory forms:
1. **Raw chemical**
2. **Ready mix** (used by the autoclave)

The autoclave **never consumes raw chemical directly**.

---
### **9.2 Mix Production as an Asynchronous Process**

Mix production is:
- Asynchronous
- Triggered by **minimum buffer rules**
- Driven by autoclave requirements, not sales

Mechanism:
Ready-Mix Tank < Minimum Level
  → Trigger Mix Batch
  → Consume Raw Chemical
  → Increase Mix Inventory

Each mix batch:

- Produces a fixed quantity of mix
- Consumes a defined quantity of raw chemical
- Depending on the pH level, consumption of a given chemical may be adjusted
- Is stored in the ready-mix tank

This creates:

- Inventory of raw chemical    
- Inventory of mix
- A clear cost transformation chain
## **10. MES ↔ Odoo Boundary (Conceptual)**

### **MES Responsibilities**

- Measure actual quantities
- Record cycle times
- Capture QC outcomes
- Report chemical usage and tank levels

### **Odoo Responsibilities**

- Plan production    
- Manage inventory and valuation
- Trigger replenishment
- Ensure traceability
- Produce financial truth

Systems are **complementary, not overlapping**.

## **11. Planning Is Implicitly Present**

Even at this global level, one constraint dominates:

> **Autoclave and dryer capacity define Kebony’s throughput and economics.**


Therefore:

- Planning objects are structural    
- Time is a primary cost driver
- Buffers exist to absorb synchronization delays

This document intentionally prepares the ground for a **dedicated planning design document**.

---
## **12. Units of Measure & Measurement Doctrine**

Kebony operates in a **multi-dimensional measurement reality** that cannot be reduced to a single unit of measure without losing economic truth.

This section defines the **measurement doctrine** that underpins inventory, costing, margin analysis, and reporting across the entire manufacturing landscape.

---
### **12.1 Metric vs Imperial – Structural Separation**

Kebony deliberately maintains a **strict separation between metric and imperial systems** at the product level.
- European operations:
    - Purchase, stock, and produce in **metric units**
        
- US-facing sales:
    - Receive products converted to **imperial units at shipment time**

This is achieved by:

- Maintaining **separate products** for metric and imperial representations    
- Avoiding mixed-unit stock at rest 
- Performing conversion only at **commercial boundary points** (shipment)

This approach ensures:
- Inventory integrity
- Auditability
- Elimination of rounding drift in stock quantities

---

### **12.2 Linear Measure Is Operational, Not Economic**

Operationally:
- Wood is purchased, handled, and sold primarily in **linear meters** (or linear feet)    
However:
- Linear measure is **not sufficient** to represent economic reality

Costs, capacity consumption, and profitability are fundamentally driven by **volume**, not length.

---
### **12.3 Cubic Measure as the Economic Reference Unit**

Kebony therefore adopts **cubic meters** (or equivalent imperial volume) as the **economic reference unit**.

All financial analysis ultimately converges to cubic volume, including:
- Production costs
- Cost absorption
- Profitability
- Margin analysis

As a consequence:
- Any margin expressed in linear meters must also be expressible in cubic meter
- Financial comparability across products, species, and dimensions requires volume normalization

> Cubic volume is the common denominator between material, capacity, and cost.

---
### **12.4 Multi-Dimensional Product Properties**

Products inherently carry conversion properties allowing translation between:
- Linear measure
- Cubic volume
- Surface coverage (square meters)
- Weight

These properties are **product characteristics**, derived from:

- species    
- section
- dimensions

They allow:
- operational handling in linear units
- economic analysis in volume units
- optional reporting in coverage or weight when relevant
---
### **12.5 Enriched Inventory Information**

For planning, reporting, and financial analysis, **stock information must be enriched beyond its operational unit**.

Even when stock is managed in linear units, inventory records must also expose:
- cubic volume equivalent
- number of boards

This enrichment is required because:
- costs are analyzed per cubic meter
- capacity consumption correlates with volume
- board counts are operationally meaningful for logistics and production
- reporting convenience and analytical clarity depend on it
As a result:
- Stock quantities are **operationally linear**
- Stock valuation and margin analysis are **economically volumetric**    
- Board count is maintained as an informational dimension
---
### **12.6 Margin & Reporting Implications**

This doctrine enables:
- Margin analysis at invoice level:
    - in linear meters (commercial view)
    - in cubic meters (economic view)
- Consistent profitability comparison across:
    - species
    - dimensions
    - product families
- Alignment between:
    - operational reporting
    - financial reporting
    - strategic decision-making
Any system that restricts analysis to a single unit of measure will:
- distort margins
- obscure capacity economics
- weaken decision support
---
### **12.7 Design Consequence**

Units of measure are **not a configuration detail**.
They are a **foundational design choice** that:
- shapes inventory structure
- conditions cost allocation
- enables meaningful margin analysis

This doctrine must therefore be respected consistently across:
- production
- inventory
- costing
- reporting
## **13. What This Document Enables**

With this conceptual landscape frozen, Kebony can:
- Design planning primitives coherently    
- Define MES interfaces without ambiguity
- Build Odoo manufacturing without distortion
- Onboard everyone with a shared language
---
## **14. What This Document Does Not Cover (By Design)**

- ERP configuration
- Costing methods
- Routing or work order structures
- MRP parameters
These are addressed in subsequent documents.