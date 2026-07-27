# Agent Instructions

This repository has project-specific Amazon template filling rules. Do not fill Amazon upload templates from general marketplace knowledge alone.

Before any task involving Amazon template filling, auto-fill, listing drafts, SKU route decisions, processing-summary fixes, or upload self-checks, read these files in this order:

1. `PROJECT_RULES.md`
2. `docs/amazon_template_fill_workflow.md`
3. `data/reference_docs/亚马逊上传表格_通用自检资料.md`
4. `app/template_writer.py`
5. `app/template_validator.py`
6. `app/success_rule_defaults.py`

Treat `app/template_writer.py` and `app/template_validator.py` as the source of truth for what is actually written and checked. Treat docs as workflow and policy guidance. If a task asks for current rules, inspect the code again instead of answering from memory.

Current high-level defaults:

- Default route is `Haul Generic Variation` parent/child variation unless the user explicitly selects single-link or set-bundle.
- Fill `List Price`, Haul/BZR `our_price`, and non-parent row `minimum_seller_allowed_price = 0.1`; do not default-fill `maximum_seller_allowed_price`.
- `Skip Offer` should remain blank.
- New item condition is `New`.
- Generic route uses `Brand = Generic` and `Manufacturer = Generic`.
- Dimensions use `Inches`; package weight uses `Pounds`.
- Ordinary non-battery / non-dangerous goods products use `batteries_required = No`, `batteries_included = No`, and `supplier_declared_dg_hz_regulation = Not Applicable`.
- Always run the project template self-check before delivery when a filled template is produced.

If these instructions conflict with a direct user instruction in the current conversation, follow the user instruction, but explicitly call out the deviation from the project default.
