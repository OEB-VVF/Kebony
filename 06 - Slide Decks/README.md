# Slide Decks

> **Purpose**: Auto-generated HTML presentation decks derived from Obsidian vault documents.
>
> **Rule**: Never edit the HTML files directly. They are regenerated from the source markdown.
> To update a slide deck, update the source document in the vault, then regenerate.

## How It Works

1. **Source**: Each deck references one or more Obsidian documents via frontmatter
2. **Annotations**: `<!-- slide -->` markers in the source docs define slide boundaries
3. **Generation**: Run `generate_slides.py` or ask Claude to regenerate from the current doc
4. **Output**: HTML files in this folder, ready to open in browser and print to PDF

## Decks

| Deck | Source Document(s) | Audience | Status |
|------|--------------------|----------|--------|
| `budget_performance.html` | [[Budget & Performance Architecture]] | CFO / Finance | Active |
| `candidate_briefing.html` | Standalone (recruitment) | HR / Hiring | Active |
| `costing_architecture.html` | [[Costing Architecture & COGS Decomposition]] | CFO / Finance | Generated 2026-03-09 |
| `electronic_signatures.html` | [[Electronic Signatures]] | All Users | Active |
| `manufacturing_costing_architecture.html` | [[Costing Architecture & COGS Decomposition]] (mfg focus) | COO / Production | Active |
| `marketing_tools_benchmark.html` | Standalone (marketing) | Marketing | Active |
| `product_master_data.html` | [[Product Master Data]] | Operations / Sales | Active |
| `replenishment_mps.html` | [[RAP MPS - Current Replenishment Logic]] | Supply Chain | Active |
| `reporting_strategy.html` | Standalone (reporting) | Management | Active |
| `security_architecture.html` | Standalone (IT security) | IT / Management | Active |
| `sign_training_guide.html` | [[Electronic Signatures]] (user guide) | All Users | Active |
| `spec_approvals.html` | [[Spec Approvals]] | Operations | Active |
| `steerco_approval_flow.html` | SteerCo series | Board / SteerCo | Active |
| `steerco_costing_model.html` | SteerCo series | Board / SteerCo | Active |
| `steerco_manufacturing.html` | SteerCo series | Board / SteerCo | Active |
| `steerco_reporting.html` | SteerCo series | Board / SteerCo | Active |
| `steerco_summary.html` | SteerCo series | Board / SteerCo | Active |
| `us_accruals_cost_capture.html` | [[Accounting & Margin Architecture]] | CFO / Finance (US) | Active |
| `vvf_budget.html` | Standalone (budget data) | Board / Management | Generated 2026-03-09 |
| `vvf_it_opex.html` | Standalone (IT run rate data) | Board / Management | Generated 2026-03-09 |

## Convention for Slide-Ready Docs

When writing in Obsidian, you can add optional annotations to help slide generation:

```markdown
<!-- slide: title -->
## Section Title
Content that becomes the slide title and subtitle

<!-- slide: diagram -->
```mermaid
...
```

<!-- slide: table -->
| Col A | Col B |
...

<!-- slide: key-message -->
> **Key takeaway**: One-liner that becomes a callout card
```

These annotations are invisible in Obsidian's reading view but guide the HTML generation.
