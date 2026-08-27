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

When changing any persistent Amazon template filling default, validation rule, or reporting behavior, update this `AGENTS.md` summary in the same change so new Codex tasks do not start from stale defaults.

Current high-level defaults:

- Default route is `Haul Generic Variation` parent/child variation unless the user explicitly selects single-link or set-bundle.
- Parent SKU should use the base SKU directly; do not append `Parent`, `-Parent`, or similar parent labels unless the user explicitly provides that format.
- Fill `List Price` and Haul/BZR `our_price`; leave `minimum_seller_allowed_price` blank by default and do not default-fill `maximum_seller_allowed_price`.
- `Skip Offer` should remain blank.
- New item condition is `New`.
- Generic route uses `Brand = Generic` and `Manufacturer = Generic`.
- Dimensions use `Inches`; package weight uses `Pounds`.
- Ordinary non-battery / non-dangerous goods products use `batteries_required = No`, `batteries_included = No`, and `supplier_declared_dg_hz_regulation = Not Applicable`.
- Filled Amazon upload files use Chinese product name plus variant/color plus version with no separator before the version label, for example `卷纸切割器黑色V1.xlsx`; corrected versions continue as `V2`, `V3`, etc.
- For `PLANTER`, fill conditionally required `Model Name`, `Special Features`, `Mounting Type`, and `Product Compliance Certificate`; clear non-applicable `item_length_width_height` fields when Amazon ignores them.
- For `PET_TOY`, fill conditionally required `Subject Character`; for ordinary cat toys use the product subject such as `Cat`.
- For `GARLAND`, fill the child-row dynamic required fields `Model Name`, `Included Components`, and `Required Assembly`; after generating V1, open the workbook in a spreadsheet app so its conditional formatting recalculates, then fill any newly red required cells and overwrite the same V1 rather than creating V2.
- For `SPORT_RACKET`, fill sport-racket conditionally required defaults for racket grip/overgrip items, including Department Name, Style, Material, Frame Material, Pattern, Skill Level, Unit Count, Included Components, Sport Type, Grip Size, Grip Type, Hand Orientation, Racket Performance Specialty, Import Designation, Warranty Description, item/package weight, package dimensions, batteries, and dangerous goods fields; do not broadly fill unrelated conditional fields such as battery chemistry, SDS, California Proposition 65, or government contract fields for ordinary non-battery grip tape. For ordinary grip tape with no warranty promise, use `Warranty Description = No Warranty`.
- Controlled enum fields must match the template `Valid Values` exactly, including case and slash formatting. Check fields such as `variation_theme#1.name`, `parentage_level`, and relationship type against the current template before delivery; for example, a PET_TOY template may require `COLOR`, not `Color`.
- Variation theme choices must consider buyer-facing display, not only upload validity. Per Amazon Seller Central help `G7UJDST28Q5Y7PWY`, variation dimensions are customer choices; visual dimensions such as color/pattern can affect images, non-visual dimensions such as size usually do not, most non-apparel categories show the best-selling child by default, and child order is Amazon-controlled. When the desired customer option is one combined label like style plus size, prefer a supported single text dimension such as `SET_NAME` and write values like `WARNING Print 1.97 in x 118.11 in`; use combined dimensions like `SIZE/SET_NAME` only when separate customer selectors are intended.
- Title self-checks now enforce Amazon-facing character and structure risks in addition to the project 100-125 character target: block prohibited/decorative characters, repeated punctuation, HTML/noise, promotional or logistics claims, medical/cleaning/protection result claims, ingestion wording such as `Flavor`, absolute ingredient claims such as `Natural`, and sensitive material/compliance claims such as `Food Grade`, `BPA Free`, or `Eco Friendly` in titles. Use `Scent` for non-food scent attributes. Ordinary verifiable materials such as `Velvet`, `Plastic`, or `Silicone` may appear in titles when useful.
- Always run the project template self-check before delivery when a filled template is produced, but do not generate or send self-check report files unless explicitly requested.

If these instructions conflict with a direct user instruction in the current conversation, follow the user instruction, but explicitly call out the deviation from the project default.
