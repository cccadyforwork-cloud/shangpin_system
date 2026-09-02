# 批量快速上品路线

这是一条独立、显式触发的竞品参考路线，目标是快速生成可进入人工复核的 Amazon V1 模板。它不会改变现有 `auto-fill`、单品正式上品路线或成功样板规则。

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
- `price`：可选人工覆盖。未填写时先取竞品 HTML 的当前 `priceToPay`。HTML 缺价时先打开 Amazon 在线页面核对，页面有价时填入 `online_price`；在线页面也缺货或无价时才填入 `estimated_price`。系统按 `price` → HTML `priceToPay` → `online_price` → `estimated_price` 的顺序决定 List Price 和 Haul/BZR Price，不把 discount 金额或推荐商品价格当成当前售价。
- `weight_grams` 或 `logistics_tier`：页面重量或指定物流档位。
- `parent_sku`、`child_sku`：推荐显式提供，保持团队短 SKU 规则稳定。
- `color`、`size`、`material`、`set_count`：已知的基础属性。
- `variation_theme`：建议按当前模板 Valid Values 显式填写。
- `base_title`：可选人工覆盖。不填写时，系统读取竞品页面 Product Title，保留前部和中部关键词顺序，仅在末尾添加或删除 3–5 个英文单词；随后继续应用 100–125 字符、禁用词和父子体变体标题规则。显式填写时应是不含具体颜色和尺寸的英文标题骨架。

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

- `ready_for_review`：项目模板自检为 0，且程序计算出的当前红框字段为 0，可进入人工复核。
- `needs_manual_fix`：已生成文件，但项目模板自检有问题，或仍存在已触发的红框字段。
- `needs_wps`：模板包含扫描器尚未支持的条件格式公式，需要用 WPS/Excel 兜底复核。
- `failed`：输入、模板或文件结构错误；不会阻断其他任务。

默认不生成写入报告、模板自检报告或资料提炼报告。

快速工作台按商品保存轻量输出版本记录。首次输出为 V1；少量报错商品生成 V2/V3 后，由系统自动同步并将最高版本设为当前输出，页面不提供人工上传输出文档的入口。旧版仅保留下载入口，不在工作台记录 processing summary。批量下载每款商品只打包当前最新版。

工作台的共享台账与业务文件位于 `data/batch_fast_workbench/`，台账只保存仓库相对路径。准备通过 Git 交给同事前，运行 `python3 run.py package-batch-workbench-data`，将外部清单、竞品 HTML、源模板和全部输出版本复制到该目录。命令出现缺失引用时不要提交；同事拉取相同提交后即可直接查看这些数据。

也可以单独扫描一份已填模板：

```bash
python3 run.py check-red-fields path/to/filled-template.xlsm
```

扫描器按每个实际 Parent/Child 数据行计算模板条件格式的优先级和联动条件，不会把所有空白字段都当成必填。补入一个字段可能触发下一层条件，因此每次写入后都应重新扫描，直到红框为 0。当前支持快速路线模板使用的 `AND`、`OR`、`NOT`、`IF`、`COUNTIF`、`LEN` 和 `ISNUMBER` 条件；无法计算的公式不会被当作通过，而会将任务标记为 `needs_wps`。

## 物流档位

物流档位的项目内唯一配置位于 `config/logistics_tiers.json`：

- ≤4 oz：10 × 10 × 2 cm，100 g。
- 4–8 oz：15 × 10 × 4 cm，200 g。
- 8–12 oz：18 × 12 × 5 cm，300 g。
- 12–16 oz：22 × 15 × 6 cm，430 g。
- 1–1.25 lb：24 × 15 × 7 cm，510 g。

输出统一换算为 `Inches` 和 `Pounds`。超过当前最高档位时任务失败，不自动猜测更大的包装。

## 交付前

状态为 `ready_for_review` 时仍应逐个：

1. 人工抽查标题、五点、描述、价格、SKU、父子关系以及无法从竞品确认的实物属性。
2. 确认程序输出同时为项目自检 0、红框 0、未支持公式 0。
3. 新 Product Type、模板结构变化、程序提示 `needs_wps`，或 Amazon 后台报错时，再用 WPS/Excel 打开 Template 页重算条件格式。
4. 修正后覆盖同一个 V1，再运行 `check-template` 和 `check-red-fields`，确认均通过后上传。
