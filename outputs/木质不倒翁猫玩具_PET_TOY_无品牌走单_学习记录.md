# 木质不倒翁猫玩具 PET_TOY 无品牌走单学习记录

## 本次路线

- 产品：木质不倒翁猫玩具，两款独立 SKU：羽毛款、剑麻款。
- 路线：单链接无品牌，不建立父体，不填写 `Parentage Level` / `Parent SKU` / `Variation Theme Name`。
- 命名：第一版按产品名 `_v1`，输出为 `/Users/cc/Desktop/木质不倒翁猫玩具_v1.xlsm`。

## 资料来源

- SKU、尺寸、重量、定价以 `/Users/cc/Desktop/猫玩具不倒翁/木质不倒翁猫玩具_最终价格确认表.xls` 为准。
- 1688 页面用于区分款式：
  - `CA-Pettoy-Feather`：羽毛款，榉木底座。
  - `CA-Pettoy-Sisal`：剑麻款，榉木底座。
- Amazon 竞品页用于英文标题、五点、描述的卖点参考：self-righting wobble、silent play、battery-free、indoor solo play、mental stimulation。

## 字段经验

- PET_TOY 模版品牌下拉默认只有 `WESWOO`，无品牌路线需要把 `Generic` 加入 `PET_TOYbrand...` 定义名范围。
- PET_TOY 材质下拉没有 `Beech Wood` / `Sisal`，本次用模版认可值承载：
  - 羽毛款：`Engineered Wood` + `Polyester`。
  - 剑麻款：`Engineered Wood` + `Jute`。
- 榉木、剑麻等真实材质和卖点放入标题、五点、描述，不强行写入不被下拉支持的材质字段。
- PET_TOY 上传关键字段继续覆盖：`Model Number`、`Model Name`、`Manufacturer`、`Material`、`Pet Toy Type`、`Pet Type`、`尺寸/重量`、`Number of Boxes`、`Directions`、电池、安全、液体字段。

## 图片判断

- 本次 1688 SKU 图大多带中文文案、尺寸线或组合宣传字样。
- 虽然当前用户没有再次强调图片限制，但参考前序“有文字图片会被禁止显示”的经验，本次主图 URL / Location 留空，避免上传带文字图导致展示失败。

## 本次产物

- 成稿：`/Users/cc/Desktop/木质不倒翁猫玩具_v1.xlsm`
- 备份：`/Users/cc/Desktop/猫玩具不倒翁/outputs/木质不倒翁猫玩具_v1.xlsm`
- 自检报告：`/Users/cc/Documents/GitHub/shangpin_system/outputs/木质不倒翁猫玩具_v1_模板自检报告.md`
- 自检结果：0 error。

## v1 上传报错与修正

- 用户反馈 processing summary：错误码 `90220`，两个 SKU 均报 `'Breed Recommendation' is required but missing.`，影响字段为 `Breed Recommendation (BR7/BR8)`。
- 复盘原因：PET_TOY 上传端把 `breed_recommendation#1` 判定为条件必填；本地自检在 v1 时没有覆盖该字段，导致漏拦。
- 修正：v2 在 `Breed Recommendation` 填写 `All Breed Sizes`，不启用父子变体，不改变 SKU / 价格 / 尺寸 / 重量。
- 自检规则已补回：PET_TOY 条件必填字段加入 `Breed Recommendation`。
- 修正版：`/Users/cc/Desktop/木质不倒翁猫玩具_v2.xlsm`
- 修正版备份：`/Users/cc/Desktop/猫玩具不倒翁/outputs/木质不倒翁猫玩具_v2.xlsm`
- 修正版自检报告：`/Users/cc/Documents/GitHub/shangpin_system/outputs/木质不倒翁猫玩具_v2_模板自检报告.md`
