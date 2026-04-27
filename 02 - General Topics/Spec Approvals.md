# Spec Approvals

> Custom approval workflow for Vendor Bills (`account.move`) and Purchase Orders (`purchase.order`).
> Implements multi-level approval with Business Unit routing, amount thresholds, and status tracking.

---

## Business Context

Kebony US requires that all Vendor Bills and Purchase Orders be approved before posting/confirmation. The approval chain is driven by the **Business Unit** assigned to each vendor, ensuring that the right department head reviews each transaction.

### Key Requirements
- Every vendor must have a **Business Unit** assigned (required field on `res.partner`)
- Approval rules differ per document type (Vendor Bill vs Purchase Order)
- Approvers are notified via email when action is needed
- Documents cannot be posted/confirmed until fully approved
- Optional amount-based thresholds trigger additional approvers

---

## Business Unit Classification

Vendors are categorized into Business Units on their partner record:

| Business Unit | Description |
|---|---|
| **Marketing** | Marketing-related vendors (agencies, events, materials) |
| **Production** | Manufacturing and production suppliers |
| **Logistics** | Transport, freight, and logistics providers |
| **Warehousing** | Warehouse services and storage vendors |

> **Warning:** Business Units may differ depending on the supplier. This means multiple Approval rules per model (Vendor Bill, Purchase Order) are needed — one per Business Unit configuration.

---

## New Approvals Model / App

A dedicated `kebony.approval` model manages all approval configurations centrally.

### Approval Configuration Fields

| Field | Description |
|---|---|
| **Approval name** | Descriptive label for the rule |
| **Model** | Target document: `account.move` (Vendor Bill) or `purchase.order` |
| **Company** | Scoped to a specific company |
| **Approver 1** | First (mandatory) approver — typically the BU Head |
| **Approver 2** | Second approver (conditional — see validation rules below) |
| **Business Unit** | Links rule to a specific Business Unit |
| **Business Unit Head** | Auto-resolved from the BU configuration |

### Approver Extra (Amount-Based)

An optional extra approver can be configured based on document amount:

| Field | Description |
|---|---|
| **Based on amount** | Checkbox — enables amount threshold |
| **Min** | Minimum amount (currency) that triggers this extra approver |
| **Amount approver** | The user who must approve when threshold is exceeded |

> The "Min" field and "Amount approver" are only displayed if "Based on amount" is checked.

---

## Validation Rules — Number of Approvers

### Vendor Bills (`account.move`)
- **2 validators always:** BU Head + another BU unit head (e.g., Finance)

### Purchase Orders (`purchase.order`)
- **1 validator only** if one → PO responsible only
- **2 validators** if no → BU Head + another BU unit head like Finance

---

## Approval List View

All requested approvals are grouped in a centralized list view with sortable/filterable columns:

| Column | Description |
|---|---|
| **Date** | Date the approval was requested |
| **Delay** | Time elapsed since request |
| **Approver** | Assigned approver |
| **Supplier** | Vendor on the document |
| **Model** | Document type (Bill / PO) |
| **Business Unit** | Vendor's Business Unit |
| **Amount** | Document total |
| **Status** | Current approval status |

> Dynamic fields adapt based on the Model (Vendor Bill fields vs Purchase Order fields).

---

## Workflow — Vendor Bills (`account.move`)

### Step 1: User Confirms the Bill
1. User opens the Vendor Bill in **Draft** status
2. User clicks **Confirm**
3. System sends an email notification to the **first approver** (Approver 1)
4. Bill status changes to **Waiting for Approval**

### Step 2: Approver Reviews
The approver sees the bill with **Approve** and **Reject** buttons:

- **Approve →** If this is the first approver and Approver 2 exists, an email/notification is sent to the next approver. If this is the final approver, status changes to **Approved**.
- **Reject →** An email/notification is sent back to the Bill responsible so they can make changes.

### Step 3: Final Approval
- When the final approver approves, status changes to **Approved**
- Users from the **"Accounting Department"** user group can then **post** the invoice

### New Status Values on `account.move`
| Status | Description |
|---|---|
| **Draft** | Initial state — editable |
| **Waiting for Approval** | Confirmed, pending approver action |
| **Approved** | All approvers have signed off |
| **Approval Rejected** | Returned to responsible for changes |
| **Posted** | Standard Odoo posted state (after approval) |

---

## Workflow — Purchase Orders (`purchase.order`)

### Step 1: User Confirms the PO
1. User opens the RFQ / Purchase Order
2. User clicks **Confirm**
3. System sends an email notification to the **first approver**
4. PO status changes to **Waiting for Approval**

### Step 2: Approver Reviews
The approver sees the PO with **Approve** and **Reject** buttons:

- **Approve →** If Approver 2 exists, notification sent to next approver. Otherwise, status → **Approved**.
- **Reject →** An email/notification is sent to the PO responsible so they can make changes.

### Step 3: Final Approval
- When the final approver approves, status changes to **Approved**
- Users from the **"PO Department"** user group can then proceed with the Purchase Order

### New Status Values on `purchase.order`
| Status | Description |
|---|---|
| **Draft** | Initial state (RFQ) |
| **Waiting for Approval** | Confirmed, pending approver action |
| **Approved** | All approvers have signed off |
| **Approval Rejected** | Returned to responsible for changes |
| **Purchase Order** | Standard Odoo confirmed PO state |

---

## Approvals Follow-Up Widget

Each document (Bill or PO) displays an **Approvals follow-up** section embedded in the form view:

- Shows **Approver 1** and **Approver 2** tabs with their current action status
- Displays a **Status** indicator (color-coded progress bar)
- Linked as a **sub-task** on the document
- Uses a **Statusbar widget** to track progression

### Tags for Tracking
| Tag | Meaning |
|---|---|
| **Waiting for Approval** | Pending approver action |
| **Approved** | Approver has signed off |
| **Rejected** | Approver has rejected |

---

## Approvals Tab on Documents

A new **"Approvals"** tab is added to both the Vendor Bill form and the Purchase Order form (alongside Invoice Lines, Journal Items, Other Info). This tab shows the approval status and history inline.

---

## Invoice Tracking Dashboard (SUIVI DES FACTURES)

A follow-up dashboard provides visibility on approval timelines:

| Feature | Description |
|---|---|
| **Time filters** | 1 Jour, 1 Mois, 2 Mois |
| **Date range** | Custom date range selector |
| **Reminders (Rappels)** | Track overdue approvals |
| **Maturity** | Payment maturity tracking |

---

## Implementation Notes

### Vendor Configuration
- `res.partner` must have a **Business Unit** field (selection: Marketing, Production, Logistics, Warehousing)
- This field determines which approval rule applies
- Missing Business Unit should trigger a warning/block on document confirmation

### Notification System
- Email notifications sent at each approval step
- Chatter messages logged for audit trail
- Rejection includes a link back to the document for the responsible user

### Security / Access
- Approvers see Approve/Reject buttons only when it is their turn
- Final posting restricted to specific user groups (Accounting Department for Bills, PO Department for Purchase Orders)
- All approval actions are logged with timestamp and user

### Model Selection in Approval Configuration
The approval model supports selection between:
- `account.move` — for Vendor Bill approvals
- `purchase.order` — for Purchase Order approvals
- Potentially extensible to other models (e.g., `sale.order`) in the future
