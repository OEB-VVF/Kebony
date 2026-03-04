## **Production Planning Primitives & Capacity Model**

**Conceptual Planning White Paper – Odoo 19**

---
## **1. Purpose of This Document**

This document defines the production planning grammar of Kebony manufacturing. It translates physical reality and operational constraints into plannable primitives that can later be implemented in Odoo and coordinated with MES. It answers one core question: _what are the smallest feasible and meaningful units that Kebony can plan, schedule, and cost against?_ This document sits between the Manufacturing Landscape (Document 0) and future implementation documents (MRP, routing, costing).

---
## **2. Planning Philosophy**

Planning at Kebony is capacity-driven, family-based, and time-constrained. The objective is not theoretical optimization, but the construction of **feasible and executable plans** that respect bottlenecks, batching rules, and minimum process quantities while preserving operational flexibility.

---
## **3. Planning Primitives (Foundational Objects)**

### **3.1 Process Pack**

A process pack is the smallest physical unit that moves through production. It is created during stacking and is homogeneous by product family (species, dimensions, impregnation/drying profile). A process pack carries linear meters, cubic volume, and board count. It is a feeder unit for autoclave loads and may be used flexibly to complete loads.

### **3.2 Autoclave Load**

An autoclave load is an intermediate feeder unit composed of typically 5–8 process packs of the same family. Autoclave processing time ranges from 2 to 8 hours depending on species and dimensions. The autoclave consumes ready-mix chemical during this step. Although constrained, the autoclave does not define long-term throughput and must be planned primarily to feed the dryers.

### **3.3 Dryer Load (Primary Planning Unit)**

A dryer load is the **primary planning and capacity unit** of Kebony manufacturing. It is composed of two autoclave loads, typically totaling 10–16 process packs of the same product family. Dryer cycle time ranges up to approximately 80 hours depending on species and dimensions (to be confirmed). Each dryer load blocks one dryer for the full duration and defines throughput, WIP accumulation, lead times, and fixed-cost absorption.

### **3.4 Mix Batch**

A mix batch is a fixed-quantity internal production unit triggered by minimum ready-mix tank levels. It consumes raw chemical and produces ready mix stored in the tank. Mix batches are asynchronous and act as a prerequisite constraint for autoclave operation.

### **3.5 Finished Pack**

A finished pack is the commercially sellable unit resulting from final destacking and packaging. It is the endpoint for inventory, sales, and margin reporting, but it is not a driver of production planning.

---

## **4. Capacity Model & Bottlenecks**

Kebony’s effective capacity is governed by the dryer stage. Stacking and autoclave operations are necessary feeders, but the dryer defines the critical path due to its long cycle time and limited parallel capacity (three dryers).

Indicative timing per dryer load:

- Entry stacking: ~4 hours
- Autoclave: 2–8 hours per load, i.e. 4–16 hours per dryer load
- Dryer: up to ~80 hours per dryer load (to be confirmed)
- Exit stacking / destacking: ~4 hours

Even when normalized by three dryers and paired autoclave charges, the dryer remains the dominant constraint by an order of magnitude.


> The dryer is the primary operational bottleneck. All production planning must therefore be dryer-centric.

---
## **5. Product Families & Compatibility Rules**

Autoclave and dryer operations cannot process arbitrary products together. Products are grouped into **product families** defined by species, board dimensions, and impregnation/drying profiles. Only one family may be processed within a given autoclave load or dryer load. Families are not mixable, even if dimensions appear close. These compatibility rules are structural and must be enforced by planning.

---
## **6. Minimum Process Quantities & Planning Flexibility**

A dryer load normally requires two autoclave loads, which defines a natural minimum process quantity per product family. However, this minimum is **not strictly rigid**. To increase planning flexibility, a **dummy process pack** may be added to an autoclave load to complete a dryer load when the exact family quantity is not available. Dummy process packs have no commercial output and exist solely to complete loads and utilize capacity. This mechanism reduces the effective minimum batch size and enables make-to-order or low-volume planning without violating physical constraints. Minimum process quantity is therefore a managed planning rule rather than a hard mathematical limit.

---
## **7. Time as a Planning Dimension**

Lead times at Kebony are not averages; they are hard constraints. Each planning primitive occupies constrained resources for a defined duration. Species and board dimensions act as time multipliers, particularly for Scots Pine, which consumes significantly more dryer time. Capacity consumption must therefore be expressed primarily in **dryer hours**, not volume.

---
## **8. Planning Triggers**

### **8.1 Make-to-Stock**

Make-to-stock planning is driven by safety stock and minimum stock rules, rounded up to family-compatible quantities and adjusted for minimum dryer load constraints. Production is scheduled forward based on dryer availability.

### **8.2 Make-to-Order**

Make-to-order planning is driven by sales demand and scheduled backward from the requested delivery date. It must still respect family compatibility, dryer capacity, and minimum process quantities, potentially using dummy process packs where necessary.

### **8.3 Chemical**

Chemical planning is driven by projected autoclave and dryer loads. Mix production is triggered by ready-mix tank minimum thresholds and is independent of sales orders.

---
## **9. Planning Outputs**

A valid production plan produces a feasible sequence of dryer loads, synchronized autoclave loads, mix batch triggers, realistic production dates, and credible stock projections. Any plan that violates family compatibility, capacity constraints, or minimum process quantity rules is invalid by design.

---
## **10. What This Document Enables**

This document enables realistic MRP design, alignment between Odoo planning and MES execution, time-based fixed-cost absorption, feasible replenishment logic, and capacity-driven margin analysis. It ensures that planning reflects how the factory actually behaves.

---
## **11. What This Document Does Not Decide**

This document does not define Odoo routing or work order structures, detailed MRP configuration, costing method implementation, or technical MES interfaces. These decisions follow once the planning grammar is locked.

# **Appendix A**

## **Capacity Math & Bottleneck Normalisation**

This appendix defines how Kebony converts product characteristics into capacity consumption, using the dryer as the reference bottleneck. It provides the mathematical backbone for planning, costing, and margin analysis.

### **A.1 Bottleneck Reference**
  
All capacity consumption is normalised against the dryer. Dryer cycle time (up to ~80 hours per dryer load, to be confirmed) dominates the critical path, dryers are limited to three units, and all products must pass through drying. Dryer time is therefore the common capacity currency.

### **A.2 Process Time Components**

Each product family consumes capacity across three stages: stacking/destacking, autoclave, and dryer. Indicative timing per dryer load is ~4 hours for entry stacking, 4–16 hours for autoclave (two loads of 2–8 hours), up to ~80 hours for drying (to be confirmed), and ~4 hours for exit stacking/destacking. Even when feeder-stage times vary, dryer time dominates and defines throughput.

### **A.3 Capacity Normalisation Principle**

For planning purposes, each product family is assigned a reference dryer time. If a family spans a range of dimensions or variants, the longest applicable dryer time is always used. Feeder-stage times are subordinated to dryer time unless they exceed it, which is considered an exception case. This conservative approach prevents optimistic overbooking and guarantees feasible plans.
### **A.4 Dummy Process Pack Impact**

The use of dummy process packs does not change dryer time or capacity consumption. It improves load completion, reduces the effective minimum batch size, and increases planning flexibility, but does not increase throughput.

### **A.5 Capacity Expression**

Capacity is expressed in dryer loads or dryer hours per period. All higher-level KPIs such as utilisation, saturation, backlog, and fixed-cost absorption derive from this representation.

---

# **📘 Document 2ter**

## **Product Planning Enrichment & Capacity Attributes**

This document defines the additional planning attributes that products must carry to enable realistic capacity planning, family grouping, and bottleneck-based scheduling. It bridges product master data with the planning grammar defined in Document 2bis.
### **1. Why Product Enrichment Is Necessary**

Dimensions alone are insufficient for planning. Production planning requires behavioural information describing how products can be grouped, how long they occupy constrained resources, and how they interact with minimum batch rules. Without this enrichment, plans become infeasible, capacity is overstated, and margins are distorted.

### **2. Planning Family Concept**

Each product belongs to a planning family that defines compatibility for autoclave and dryer loads. A family is defined by species, impregnation profile, drying profile, and a dimensional class rather than an exact SKU.

### **3. Absolute vs Range-Based Families**

An absolute family maps to a single fixed profile and is strict but rigid. A range-based family covers a defined range of dimensions and aligns all products to the longest process time within the range. This model provides flexibility while preserving feasibility and is the recommended approach for Kebony.  
### **4. Required Planning Attributes per Product**

Each product or product template must expose a planning family ID used for load compatibility. It must also expose reference process times for stacking, autoclave, and dryer, expressed as fixed values or ranges. For planning, the maximum applicable time is always used. Optionally, a derived capacity weight may be stored, expressing dryer hours consumed per unit or per fraction of a dryer load. Informational fields may also indicate typical and minimum load sizes, without acting as hard constraints.

### **5. Planning Alignment Rules**  

When planning a batch, all products must share the same planning family. The longest dryer time in the family defines the batch duration. Feeder stages are planned to support dryer availability, and dummy process packs may be used to complete loads when needed.
### **6. Strategic Consequence**

This enrichment allows Kebony to plan at family level rather than SKU level, preserve operational flexibility, align planning with costing and margin logic, and simulate the capacity impact of product mix decisions. Products do not only carry dimensions; they carry behaviour.
### **7. Scope Exclusions**
	
This document does not define technical field implementation, UI design, or MES data structures. These follow once the planning attributes are approved.