# 上品流程本地 MVP

这是把“选品建档 -> 路线判断 -> 资料整理 -> 上传前自检 -> 报告解析”落地成可运行项目的第一版。

## 初始化

```bash
cd /Users/admin/Desktop/上品模版填写上传/shangpin_system
python3 run.py init
```

初始化后会生成：

- `templates/产品资料模板.xlsx`
- `data/projects/`
- `outputs/`

## 创建一个产品项目

```bash
python3 run.py new-project "黑色收纳袋"
```

每个项目会自动生成：

- `01_采购资料`
- `02_原始图片`
- `03_竞品参考`
- `04_模板原件`
- `05_填表版本`
- `06_处理报告`
- `07_上架备注`

产品资料表会放在 `07_上架备注` 里。

## 上传前自检

```bash
python3 run.py validate "/完整路径/产品资料.xlsx"
```

系统会检查：

- 核心字段是否缺失
- Generic/品牌路线是否冲突
- Haul 价格是否超过配置上限
- 包装尺寸重量是否完整且大于 0
- List Price / Haul Price 是否冲突
- 文案是否出现高风险宣称词
- 高风险类目关键词

自检报告默认输出到 `outputs/`。

## 自动提炼项目资料

先创建项目：

```bash
python3 run.py new-project "厨房硅胶刮刀"
```

然后把资料放进项目文件夹：

- `01_采购资料`：采购单、报价表、供应商参数表
- `03_竞品参考`：竞品链接、标题、五点、截图备注
- `07_上架备注`：你自己的补充说明

目前支持读取：

- `.xlsx`
- `.xlsm`
- `.pdf`
- `.html`
- `.htm`
- `.csv`
- `.tsv`
- `.txt`
- `.md`

运行：

```bash
python3 run.py analyze-project "/完整路径/data/projects/日期_厨房硅胶刮刀"
```

系统会生成：

- `07_上架备注/..._自动提炼草稿.xlsx`
- `outputs/..._资料提炼报告.md`

草稿会尽量提取：

- 产品名
- SKU
- 颜色
- 尺寸
- 材质
- 成本/价格
- 包装尺寸重量，并换算成 inches / pounds
- 供应商链接
- 竞品链接
- Generic 或品牌路线建议
- 标题、五点、描述草稿

注意：这一版是“提炼草稿”，不是最终上传文件。价格、类目、`item_type_keyword`、品牌路线、主图 URL、尺寸重量仍建议人工确认。

## 解析 processing-summary

```bash
python3 run.py parse-report "/完整路径/processing-summary.xlsx"
```

目前内置识别：

- `90041`
- `90220`
- `100643`
- `18320`
- `8541`
- `13013`
- `5887`
- `5882`
- `100521`

## 沉淀报错复盘库

每次上传失败后，把 `processing-summary` 加入复盘库：

```bash
python3 run.py learn-report "/完整路径/processing-summary.xlsm" --product "产品名" --note "本次修复备注"
```

也可以一次学习多个报告：

```bash
python3 run.py learn-report "/路径/v1-processing-summary.xlsm" "/路径/v2-processing-summary.xlsm" --product "彩色瑜伽砖"
```

系统会生成：

- `data/error_learnings.json`
- `outputs/上传报错复盘库.md`

复盘库会累计：

- 错误码
- 错误字段
- 受影响 SKU
- 原始报错信息
- 归纳出的上传前自检规则

注意区分规则作用范围：

- 通用规则：例如 `Brand = Generic`、普通非危险品 `Dangerous Goods Regulations = Not Applicable`。
- 模板字段规则：只有模板存在对应字段时才检查，例如 `item_depth_width_height` 的数值和单位配套。
- Product Type 规则：只对相同或相近 `product_type` 生效，不要直接套用到所有类目。

## 成功上传模板样板库

桌面 `亚马逊上传表格存档` 里的成功上传文件已整理到：

```bash
data/success_templates/
```

这些文件用于：

- 对照不同 Product Type 的真实成功字段。
- 提炼字段默认值、条件必填字段和类目差异。
- 作为后续自动填表逻辑的回归样本。

注意：这些是成功样板，不建议直接覆盖业务项目里的填表版本。新增产品仍应放到 `data/projects/` 下运行自动填表。

## 后续扩展方向

1. 从 `data/success_templates/` 提炼成功模板规则，反哺字段映射和自检。
2. 增加 Data Definitions/数据定义 解析，自动判断条件必填。
3. 增加图片 URL 检查。
4. 增加英文标题、五点、描述生成。
5. 做一个本地网页界面，减少命令行操作。
