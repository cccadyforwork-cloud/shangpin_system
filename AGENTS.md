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
- The competitor-only batch fast-prelisting route is opt-in and isolated. Invoke it only when the user explicitly asks for `批量快速上品路线`, using `python3 run.py batch-fast-prelist <manifest.json>`. It reuses the existing writer and validator without changing `auto-fill`, keeps image fields blank, defaults to Haul Generic Variation, applies logistics tiers from `config/logistics_tiers.json`, isolates failures per task, and produces no reports by default. After writing, it evaluates the template's conditional-format formulas per populated Parent/Child row and blocks delivery when a currently triggered red-border field remains. A zero-red result is accepted only when every encountered formula is supported; unsupported formulas produce `needs_wps`, and new Product Types, template changes, or backend errors still require WPS/Excel fallback recalculation. When one saved competitor HTML contains a complete single `color_name` twister and the manifest does not explicitly provide `variants`, extract every color and generate one Parent plus all Children; never write competitor ASINs into the new template. Explicit `variants` take precedence, `expand_competitor_variants: false` opts out, and multi-dimension twisters require explicit variants. Read `docs/batch_fast_prelisting.md` for its manifest schema.
- For batch-fast titles, when `base_title` is omitted, use the saved competitor page Product Title as the source, preserve its front and middle keyword order, and alter only 3–5 English words at the end by addition or deletion. An explicit `base_title` remains an override, and existing title length, restricted-term, and variation checks still apply. Do not change formal `auto-fill` title behavior.
- For that batch-fast route only, default price to the competitor page's current `priceToPay` when the manifest omits `price`; an explicit manifest price remains an override. When `copy_reference` is available, compare rows by SKU: keep `Create or Replace (Full Update)` for new SKUs, set the exact Valid Value `Edit (Partial Update)` only for existing SKUs whose fields changed, and do not change the action when no fields changed. Do not change the formal `auto-fill` action default.
- The batch-fast workbench keeps lightweight output version history per product. V1 is the normal current output; when Codex generates and synchronizes a corrected V2/V3, the highest version becomes current and earlier files remain available only as old-version downloads. The UI must not ask the user to upload output files or corrected versions; source-template upload remains user-facing. Do not store processing-summary reports in this workbench. Batch ZIP downloads include only each product's current latest output.
- Batch-fast workbench business data is Git-shareable under `data/batch_fast_workbench/`. Ledger paths stored inside the repository must remain repository-relative. Before committing newly referenced external files, run `python3 run.py package-batch-workbench-data`; do not deliver or commit when it reports missing references. A colleague who pulls the same commit must be able to open the shared ledger and files without the original user's Desktop paths.

If these instructions conflict with a direct user instruction in the current conversation, follow the user instruction, but explicitly call out the deviation from the project default.
