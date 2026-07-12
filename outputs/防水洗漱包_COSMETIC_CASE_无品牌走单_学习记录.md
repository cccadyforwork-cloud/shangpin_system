# 防水洗漱包 COSMETIC_CASE 无品牌走单学习记录

## 本次产品

- 输出文件：`/Users/cc/Desktop/防水洗漱包_v1.xlsm`
- 模板：`/Users/cc/Desktop/防水eva包/COSMETIC_CASE.xlsm`
- 路线：单链接无品牌，不填 Parentage Level / Parent SKU / Variation Theme Name。
- 最终价格确认表只选中两款：`CA-Washbag-Grey`、`CA-Washbag-White`，不要把 1688 里的全部 7 个 SKU 都上。

## 权威信息

- SKU、定价、尺寸、重量以最终价格确认表为准：
  - `CA-Washbag-Grey`：6.3 x 4.72 x 1.57 in，0.193 lb，4.99
  - `CA-Washbag-White`：6.3 x 4.72 x 1.57 in，0.193 lb，4.99
- 1688 大号颜色图：
  - 透明灰色大号：`O1CN01SU44DB23QYVulE9w4`
  - 透明白色大号：`O1CN01brlVIt23QYVvNzzJ6`

## 模板字段经验

- COSMETIC_CASE 品牌下拉默认只有 `WESWOO`，无品牌路线需要把 `Generic` 加入 `COSMETIC_CASEbrand...` 定义名范围。
- Item Type Keyword 使用更贴切的 `toiletry-bags`，不是 `cosmetic-bags`。
- 材质存在源信息不完全一致：1688 决策属性写 `PVC`，规格写 `质量好的【EVA】`，价格表款式标题写 `EVA`。本次模板填：
  - Material Type = `Ethylene Vinyl Acetate`
  - Material Type.1 = `Polyvinyl Chloride`
- 防水等级可填 `Waterproof`。
- 束口袋闭合方式用 `Drawstring`，不要为了包类习惯误填 `Zipper`，也不要填 Zipper Color。
- 产品本体尺寸使用 `item_length_width_height` 组：
  - `Height base to top`
  - `Height Unit`
  - `Length longer horizontal edge`
  - `Length Unit`
  - `Width shorter horizontal edge`
  - `Width Unit`

## 卖点写法

- 标题/五点/描述突出：waterproof、EVA/PVC、dry wet separation、transparent body、large travel pouch、drawstring closure、gym/swimming/beach/travel/toiletry/makeup storage。
- 不夸大为密封防漏容器，使用 `helps separate damp items` 这类稳妥表达。

## 自检结果

- `/Users/cc/Desktop/防水洗漱包_v1.xlsm` 经工作台模板自检：0 error。
- 下拉值抽查：Generic、Ethylene Vinyl Acetate、Polyvinyl Chloride、Waterproof、Drawstring、Travel/Outdoors/Home、No、Not Applicable 均在合法列表内。
