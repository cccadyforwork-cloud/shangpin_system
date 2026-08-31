# 批量快速上品路线

这是一条独立、显式触发的竞品参考路线，目标是快速生成可进入 WPS 复核的 Amazon V1 模板。它不会改变现有 `auto-fill`、单品正式上品路线或成功样板规则。

## 适用范围

- 暂时没有 1688 或供应商资料，只参考 Amazon 竞品。
- 先上品、后采购，接受属性准确度低于正式路线。
- 默认走 `Haul Generic Variation`。
- 图片字段全部留空。
- 没有实测包装数据时使用项目物流档位。
- 目标是项目模板自检通过；Amazon 后台仍可能返回模板无法预知的类目或账号错误。

## 准备批量清单

复制 `templates/批量快速上品任务清单.example.json`，每个商品放在 `tasks` 中。相对路径以清单文件所在目录为基准。

每个任务至少填写：

- `name`：中文任务名。
- `product_name`：用于生成英文 Listing 的简短英文商品名。
- `template`：Amazon 原始 `.xlsx` / `.xlsm` 模板。
- `competitor` 或 `competitors`：一个或多个竞品 HTML。
- `price`：可选。显式填写时作为人工覆盖；留空时从竞品 HTML 的当前 `priceToPay` 提取 List Price 和 Haul/BZR Price。不把 Amazon discount 金额当成售价。
- `weight_grams` 或 `logistics_tier`：页面重量或指定物流档位。
- `parent_sku`、`child_sku`：推荐显式提供，保持团队短 SKU 规则稳定。
- `color`、`size`、`material`、`set_count`：已知的基础属性。
- `variation_theme`：建议按当前模板 Valid Values 显式填写。
- `base_title`：不含具体颜色和尺寸的英文标题骨架，建议 100–125 字符范围内；系统会追加子体属性。

如果标题、五点或四段描述缺失或不符合项目长度，快速路线会使用保守的通用英文文案兜底。该兜底以上传自检通过为优先，不代表已核实产品精确属性。

默认会先检查竞品 HTML 中的变体选择器。当页面包含完整的单一颜色维度 `color_name` 时，系统会自动提取所有颜色，生成 1 个 Parent 和全部 Child；竞品 ASIN 只用于识别变体，不写入新模板。明显的页面拼写错误会按项目已知映射规范化，例如 `Llight Blue` 处理为 `Light Blue`。

如果清单显式提供 `variants` 数组，以清单为准。每个变体可覆盖 `sku`、`color`、`size`、`material`、`set_count` 和 `price`。需要只上当前页面子体时，可设置 `expand_competitor_variants: false`。多维变体不自动展开，必须在清单中明确提供 `variants`。

如果提供 `copy_reference`，批量快速路线会按 SKU 对比新旧表格。新增 SKU 保持 `Create or Replace (Full Update)`；已存在且字段发生变化的 SKU 写入 `Edit (Partial Update)`；已存在但字段没有变化时不改 Action。`Edit (Partial Update)` 是当前 Amazon 模板中 `Edit` 的完整 Valid Value。

如果已有一份同类已填模板，可用 `copy_reference` 复用其五点和描述。该字段只用于加速同类商品，不会复制图片、SKU、价格或包装数据。

## 执行

```bash
python3 run.py batch-fast-prelist path/to/batch.json
```

也可以临时覆盖输出目录：

```bash
python3 run.py batch-fast-prelist path/to/batch.json --output-dir outputs/本次批量
```

每个任务独立处理：

- `ready_for_wps`：项目模板自检为 0，下一步用 WPS 打开 Template 页重算条件格式。
- `needs_manual_fix`：已生成文件，但项目模板自检仍有问题。
- `failed`：输入、模板或文件结构错误；不会阻断其他任务。

默认不生成写入报告、模板自检报告或资料提炼报告。

## 物流档位

物流档位的项目内唯一配置位于 `config/logistics_tiers.json`：

- ≤4 oz：10 × 10 × 2 cm，100 g。
- 4–8 oz：15 × 10 × 4 cm，200 g。
- 8–12 oz：18 × 12 × 5 cm，300 g。
- 12–16 oz：22 × 15 × 6 cm，430 g。
- 1–1.25 lb：24 × 15 × 7 cm，510 g。

输出统一换算为 `Inches` 和 `Pounds`。超过当前最高档位时任务失败，不自动猜测更大的包装。

## 交付前

即使状态为 `ready_for_wps`，仍必须逐个：

1. 用 WPS/Excel 打开输出文件。
2. 进入 Template 页等待条件格式重算。
3. 补齐新出现的 Child 红色必填格并覆盖同一个 V1。
4. 再运行项目 `check-template`，确认 0 个问题后上传。
