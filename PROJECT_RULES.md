# 上品系统项目规则总纲

这份文件是新任务、新同事、Codex 代理进入本项目时的第一入口。任何亚马逊模板填表、自动填表、上传报错修复、Listing 草稿、自检交付，都必须先按这里的规则对齐。

## 必读顺序

开始填表或修表前，先读：

1. `PROJECT_RULES.md`
2. `docs/amazon_template_fill_workflow.md`
3. `data/reference_docs/亚马逊上传表格_通用自检资料.md`
4. `app/template_writer.py`
5. `app/template_validator.py`
6. `app/success_rule_defaults.py`

代码优先级高于文档：实际写入以 `app/template_writer.py` 为准，实际自检以 `app/template_validator.py` 为准，成功样板默认值过滤以 `app/success_rule_defaults.py` 为准。

## 当前默认路线

默认路线统一为父子体路线：

```text
Haul Generic Variation
```

默认行为：

- 生成 1 行 Parent 和多行 Child。
- Parent 行填写 `parentage_level = Parent` 和 `variation_theme`。
- Child 行填写 `parentage_level = Child`、`parent_sku`、`variation_theme`。
- Parent 行不填写价格、包装尺寸、包装重量、主图、颜色、尺寸、Item Condition、Model Number、Model Name、Manufacturer、Part Number、Item Highlight 等子体/报价/可售专属字段。

只有用户明确选择或资料中明确写明时，才走：

- `Haul Generic`：单链接子体，不建立 Parent/Child。
- `Haul Generic Set Bundle`：套装售卖，不建立 Parent/Child，数量字段按套装数量填写。
- `Brand`：品牌路线，Brand / Manufacturer / 文案 / 图片 / 包装必须一致。

## 价格字段规则

当前默认填写：

```text
list_price[marketplace_id=ATVPDKIKX0DER]#1.value
purchasable_offer[marketplace_id=ATVPDKIKX0DER][audience=BZR]#1.our_price#1.schedule#1.value_with_tax
```

项目内字段名：

```text
list_price
haul_price
```

父子体 V4 默认卖方最低价格：

```text
minimum_seller_allowed_price 留空
```

不要默认填写：

```text
maximum_seller_allowed_price
```

最高价字段即使在成功样板中出现，也属于不安全默认字段，不能自动补。最低价默认留空；如用户明确要求或某处理报告验证需要，只允许人工填 `0.1`，不要从成功样板继承其他最低价。

## 基础写入规则

基础字段映射在 `app/template_writer.py` 的 `FIELD_MAP`。当前覆盖：

- SKU、Product Type、Record Action。
- 标题、品牌、Manufacturer、Item Type Keyword。
- Parent/Child 变体字段。
- 描述、五点、材质、颜色、尺寸、件数、包装数量。
- 非 Parent 行 List Price、Haul/BZR Price。
- 商品尺寸、包装尺寸、包装重量及单位。
- 原产国、电池、危险品、Condition。
- 部分类目基础字段，例如 PROTECTIVE_GLOVE 的 glove/coating/palm 字段。

只有模板第 5 行存在对应字段列，且数据或默认值非空时才写入。

## 固定默认值

当前默认值：

```text
record_action = Create or Replace (Full Update)
非 Parent 行 condition_type = New，Parent 行留空
item_package_quantity = set_count 或 1
尺寸单位 = Inches
包装重量单位 = Pounds
country_of_origin = China
batteries_required = No
batteries_included = No
supplier_declared_dg_hz_regulation = Not Applicable
```

Generic 路线：

```text
brand = Generic
manufacturer = Generic
```

## Data Definitions 必填兜底

系统会读取模板的 `Data Definitions`，凡是标记为 `Required` 的字段，会按稳定默认逻辑尝试补齐。

可兜底的字段类型包括：

- Brand / Manufacturer / Model Name / Model Number / Part Number。
- Material、Color Map、数量、Unit Count、Included Components。
- Uses、Theme、Pattern、Style、Care Instructions。
- Country of Origin、电池、危险品、Condition、Product Tax Code。
- 尺寸和重量数值/单位。

不能稳定判断的字段不硬填，交给自检报告或人工确认。

## Product Type 条件字段

类目条件字段在 `app/template_validator.py` 的 `PRODUCT_TYPE_CONDITIONAL_FIELDS`。

当前覆盖：

- `ANIMAL_COLLAR`
- `BOTTLE`
- `COSMETIC_CASE`
- `CLEANING_BRUSH`
- `PET_TOY`
- `TOWEL`
- `PROTECTIVE_GLOVE`

这些规则只对对应 Product Type 生效，不能泛化到所有模板。

## 成功样板规则

成功样板来源：

```text
data/success_template_rules.json
```

写入前必须经过 `app/success_rule_defaults.py` 的安全过滤。

以下字段属于不安全默认，不能因为历史成功样板出现过就自动填：

- SKU、标题、描述、五点。
- 图片 URL。
- 价格字段，包括 `list_price`、`our_price`、`maximum_seller_allowed_price`，以及非项目固定值的 `minimum_seller_allowed_price`。
- 颜色、尺寸、变体字段。
- 包装尺寸/重量数值。
- `skip_offer`。

## 文案规则

Listing 文案必须英文填写。

标题：

- 100-125 字符，尽量贴近 125 字符但不能超。
- 核心关键词靠前，并覆盖更多相关关键词、长尾词、用途、场景和款式信息。
- 不堆砌关键词，不全大写。
- Generic 路线不出现供应商品牌/公司名。
- 标题按 100-125 字符时，不填写 `Item Highlight` / `title_differentiation`。Amazon 报错 100476 已确认：只要填写 Item Highlight，Item Name 必须 75 字符以内。

五点：

- 尽量 5 条全部填写。
- 每条以 3-5 个英文词卖点开头，格式为 `Keyword Phrase: ...`。
- 每条末尾用英文句号。
- 不使用分号。

描述：

- 商务英语。
- 通常 4 段。
- 不写无法证明的承诺。

风险词：

- 避免侵权品牌词、医疗/杀菌/防护承诺、儿童/孕妇相关描述、绝对化表达。
- 项目历史风险词包括 `durable`、`Elegant`、`Apple`、`Samsung`、`Velcro`、`Breathable`、`magnetic`、`antibacterial`、`anti-odor`、`UV protection` 等。

## 自检规则

交付填好的 Amazon 模板前必须跑模板自检。

最低检查：

- 非 Parent 行 `Item Condition = New`，Parent 行可留空。
- `Skip Offer` 留空。
- 非 Parent 行 `List Price` 和 Haul/BZR `our_price` 已填写；`minimum_seller_allowed_price` 默认留空，若人工填写只允许 `0.1`。
- 标题超过 75 字符时，`Item Highlight` / `title_differentiation` 必须留空。
- 尺寸数值和单位成对填写。
- Parent 行不填 Parent SKU；Child 行必须填 Parent SKU。
- Parent/Child 行必须有 Variation Theme。
- 标题、描述、五点不能含中文。
- `Data Definitions` 标 Required 的字段非空。
- 当前 Product Type 的条件字段非空。
- TOWEL 当前不允许的合规字段保持空。

常用命令：

```bash
python3 run.py auto-fill "data/projects/日期_产品名" --write-reports
python3 run.py check-template "data/projects/日期_产品名/05_填表版本/产品名_v1.xlsx"
python3 run.py parse-report "processing-summary.xlsm"
```

## 报错复盘规则

拿到 processing-summary 后：

- 先记录错误码、错误字段、受影响 SKU。
- 不直接修改 processing-summary 当上传文件。
- 回到源模板修字段。
- 修复后的规则若属于某 Product Type 或某路线，必须补入整体自检或自动填表规则。
- 单品特殊情况只保留在单品学习记录，不泛化。

## 新任务开场要求

新开任务时，如果内容涉及填表或修表，先说明已经读取项目规则，再开始操作。没有读取上述规则时，不要直接填 Amazon 表格。
