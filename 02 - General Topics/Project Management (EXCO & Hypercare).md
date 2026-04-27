# Project Management — EXCO & Hypercare (installed)

> **Meta-module, not a Kebony business process.** This page is a
> pointer. The EXCO portfolio dashboard and Hypercare ticketing are
> provided by a VVF module (`vvf_pm_ticketing`) installed on the Kebony
> Odoo to let the CEO manage strategic initiatives and support tickets.
> The architecture and rules belong to the VVF side.

## What's installed

| Layer                 | What it does (Kebony-side impact)                                  |
|-----------------------|--------------------------------------------------------------------|
| **EXCO Portfolio**    | CEO dashboard + kanban + Gantt for projects flagged EXCO           |
| **Execution**         | Project owners see a 3-stage task lifecycle on EXCO projects       |
| **Hypercare**         | Per-project flag flips tasks into 4-stage tickets (Bug / Feature / Training / Other) |

**CEO view is filtered to EXCO projects only** (`vvf_is_exco_project =
True`). BAU / non-strategic projects stay invisible to the CEO
dashboard.

**Hypercare is a per-project toggle** (`vvf_hypercare`). Flip it ON
at go-live; tasks become tickets; maturity pivot shows the
Bug → Training → Feature shift over time.

## User guide

**[[exco_ceo_user_guide.html]]** in `06 - Slide Decks/` — 7 chapters
walking Tom through the dashboard, kanban, project creation, Gantt,
and the daily/weekly routine.

## Full architecture

Lives in the VVF-consulting vault:
`/Users/oeb/Documents/VVF Consulting/Project Management/VVF PM & Ticketing - Module Specification.md`

Covers: portfolio stages, auto-transition rules, hypercare stage set,
typology signals, maturity reporting, security groups, menu structure,
deployment model.

## Module reference (for Claude / devs)

`addons/vvf_pm_ticketing/CLAUDE.md` — always-current snapshot of models,
fields, stages, version.
