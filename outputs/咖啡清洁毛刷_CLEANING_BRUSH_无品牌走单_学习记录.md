# 咖啡清洁毛刷 CLEANING_BRUSH 无品牌走单学习记录

## 本次产品

- 输出文件：`/Users/cc/Desktop/咖啡清洁毛刷_v1.xlsm`
- 模板：`/Users/cc/Desktop/咖啡毛刷/CLEANING_BRUSH.xlsm`
- 路线：单链接无品牌，不填 Parentage Level / Parent SKU / Variation Theme Name。
- 两款：黑檀木、花梨木。

## 权威信息

- SKU、定价、包裹尺寸、包裹重量以最终价格确认表为准：
  - `CA-Coffeebrush-Blackwood`：7.09 x 1.57 x 0.59 in，0.066 lb，2.49
  - `CA-Coffeebrush-Pearwood`：7.09 x 1.57 x 0.59 in，0.066 lb，2.49

## 图片规则

- 本次用户明确要求：图片只能使用无文字的白底主图。
- 已检查 1688 SKU 图和主图候选：
  - SKU 图带中文款式标签。
  - 主图带中文/英文宣传文字。
- 因不符合要求，`Main Image URL`、`Main Image Location`、`Swatch Image URL` 全部留空。

## 模板字段经验

- CLEANING_BRUSH 品牌下拉默认只有 `WESWOO`，无品牌路线需要把 `Generic` 加入 `CLEANING_BRUSHbrand...` 定义名范围。
- Item Type Keyword 使用 `cleaning-brushes`。
- 材质建议按源信息“实木 黄铜”加刷毛填写：
  - Material = `Wood`
  - Material.1 = `Copper`
  - Material.2 = `Pig Hair`
- Handle Material 按款式区分：
  - 黑檀木：`Ebony Wood`
  - 花梨木：`Pearwood`
- 刷子合规字段需要补齐：
  - Compliance - Brush Intended Use = `Cleaning`
  - Compliance - Is Motorized = `No`
  - Compliance - Is Mechanical = `No`
  - Compliance - Bristle Material = `Other`
  - Compliance - Is Hand-Operated = `Yes`
- Product Compliance Certificate 可填 `Not Applicable`。
- 本体尺寸字段至少补齐 `item_length_width_height` 组，同时补 `Item Length / Item Width` 组。

## 自检结果

- `/Users/cc/Desktop/咖啡清洁毛刷_v1.xlsm` 经工作台模板自检：0 error。
- 下拉值抽查：Generic、Wood、Copper、Pig Hair、Ebony Wood、Pearwood、Cleaning、Not Applicable、No、Other 等均在合法列表内。
