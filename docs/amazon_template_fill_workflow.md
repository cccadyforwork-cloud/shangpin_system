# Amazon Template Fill Workflow

这份文档用于下次在新设备或新对话里快速复用“亚马逊模板填表”流程。目标是：少走弯路、优先用项目已有经验、避免慢速全量渲染、避开中文路径和文件锁问题。

## 新对话启动提示

可以直接把下面这段发给 Codex：

```text
我要填亚马逊模板表格。请优先使用项目里现有的填表经验和字段映射，不要先用通用表格引擎全量导入/渲染模板。

流程要求：
1. 先读取最终价格表，确认 SKU、父体 SKU、子体 SKU、价格、尺寸、重量。
2. 读取 Amazon 模板的 Data Definitions 和 Template 第 5 行字段名，确认必填字段。
3. 读取 1688 详情和 Amazon 竞品详情，提炼标题、五点、描述、材质、颜色、卖点。
4. 优先使用 WPS 表格 COM 或 Excel/WPS 自动化接口写入 Template 页；如果不可用，再用 openpyxl 复制模板并只写目标字段。
5. 只做字段级校验：父子体、必填字段、价格尺寸、重量、五点描述 5 个单元格、危险品/电池/原产国。
6. 不要做大范围图片渲染，不要用慢速通用表格引擎处理整本 Amazon 模板，除非我明确要求视觉预览。
7. 中文路径容易出问题，请把工作副本放到短 ASCII 临时目录，例如 C:\sp_work\当前产品，再把最终文件复制回目标中文文件夹。
8. 输出文件保存在产品资料文件夹里。
```

## 推荐执行顺序

1. 准备文件

把每个产品的资料放在同一个文件夹：

- Amazon 模板 `.xlsm`
- 最终价格确认表 `.xls` / `.xlsx`
- 1688 商品详情 HTML
- Amazon 竞品详情 HTML
- 需要时加入图片 URL 或图片文件

2. 建立短路径工作区

中文路径可读性好，但自动化工具容易在命令行编码里变成 `????`。建议执行前复制到短英文路径：

```powershell
New-Item -ItemType Directory -Path C:\sp_work\phone_grip -Force
Copy-Item -LiteralPath "D:\dpan\桌面\手机握把\*" -Destination C:\sp_work\phone_grip -Force
```

填完后再复制最终文件回中文目录。

3. 读取模板结构

必须读取：

- `Template` 页第 5 行：字段名
- `Data Definitions`：必填字段
- `Valid Values` / `Browse Data`：Product Type、Item Type Keyword、有效值

本项目已有经验：

- `app/template_inspector.py`：扫描模板字段和必填项
- `app/template_writer.py`：已有字段映射 `FIELD_MAP`
- `app/success_rule_defaults.py`：成功模板里沉淀的安全默认值
- `data/success_template_rules.json`：成功模板规则

4. 生成产品资料行

字段来源优先级：

- SKU、价格、尺寸、重量：最终价格确认表
- Product Type、Browse / Item Type Keyword：模板本身
- 标题、五点、描述：1688 + Amazon 竞品参考后重写
- Brand / Manufacturer：无品牌路线填 `Generic`
- Country of Origin：通常填 `China`
- Batteries Required：无电池填 `No`
- Dangerous Goods Regulations：普通无危险品填 `Not Applicable`

5. 写入方式优先级

最快且最贴近实际打开状态：

```powershell
$app = New-Object -ComObject KET.Application
$wb = $app.Workbooks.Open("C:\sp_work\phone_grip\template.xlsm")
$ws = $wb.Worksheets.Item("Template")
# 按第 5 行字段名定位列，写第 7 行以后数据
$wb.SaveAs("C:\sp_work\phone_grip\output.xlsx", 51)
$wb.Close($false)
$app.Quit()
```

WPS 表格常见 COM 名称：

- `KET.Application`：WPS 表格
- `Excel.Application`：Microsoft Excel

如果 WPS COM 不可用，再退回 `openpyxl`：

- 复制原模板
- 只清空 `Template` 页数据行
- 按字段名写目标单元格
- 不要全量重建工作簿

避免作为首选：

- 通用表格渲染/导入引擎
- 大范围 `A1:HG10` 图片预览
- 整本 workbook 视觉渲染

这些会非常慢，而且对 Amazon 模板不一定更稳。

## 必填字段检查

每次交付前至少检查这些字段。

模板必填字段通常包括：

- `contribution_sku#1.value`
- `product_type#1.value`
- `item_name[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value`
- `brand[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value`
- `product_description[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value`
- `bullet_point[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value`
- `country_of_origin[marketplace_id=ATVPDKIKX0DER]#1.value`
- `batteries_required[marketplace_id=ATVPDKIKX0DER]#1.value`
- `supplier_declared_dg_hz_regulation[marketplace_id=ATVPDKIKX0DER]#1.value`

即使模板只标了 Bullet Point #1 必填，也建议五点全部填：

- `bullet_point...#1.value`
- `bullet_point...#2.value`
- `bullet_point...#3.value`
- `bullet_point...#4.value`
- `bullet_point...#5.value`

## 父子体检查

父体行：

- SKU：父体 SKU
- Parentage Level：`Parent`
- Variation Theme：例如 `Color`
- Brand：`Generic`
- Item Name：可不带具体颜色
- 通常不填 Parent SKU

子体行：

- SKU：子体 SKU
- Parentage Level：`Child`
- Parent SKU：父体 SKU
- Child Relationship Type：`Variation`
- Variation Theme：例如 `Color`
- Title Differentiation：例如 `Black`
- Color：例如 `Black`
- 价格、尺寸、重量按最终价格表填写

## Google Drive 怎么加速

Google Drive 插件主要加速“找资料”和“复用资料”，不直接替代 WPS 填表。

适合放到 Drive 的内容：

- 成功上传过的模板文件
- 每个 Product Type 的成功案例
- 1688 / Amazon 详情源文件
- 最终价格确认表
- 规则说明和历史报错修复记录

推荐用法：

- 新设备上先从 Google Drive 搜索产品文件夹或成功模板
- 下载/导出到本地短路径，例如 `C:\sp_work\产品名`
- 本地用 WPS COM 写表
- 输出完成后再上传或同步回 Drive

这样速度会更快，因为 Codex 不需要在本地到处找历史模板，也不用重新推断成功经验。

Google Drive 不适合直接做的事：

- 直接在线编辑 Amazon `.xlsm` 宏模板
- 依赖 Google Sheets 打开 Amazon 上传模板
- 保留复杂 Excel 数据验证和隐藏结构

Amazon 模板还是本地 WPS/Excel 写入最稳。

## 中文路径优化

推荐策略：

1. 用户资料可以继续放中文文件夹，方便人工管理。
2. 自动化处理时复制到短英文路径。
3. 脚本里不要硬编码中文文件名，优先用枚举匹配：

```python
files = os.listdir(".")
template = [f for f in files if f.endswith(".xlsm") and not f.startswith("~$")][0]
price = [f for f in files if "价格" in f and f.endswith((".xls", ".xlsx")) and not f.startswith("~$")][0]
```

4. PowerShell 操作文件时用 `-LiteralPath`，不要让特殊字符参与通配匹配：

```powershell
Copy-Item -LiteralPath "D:\dpan\桌面\手机握把\手机握把-v1.xlsx" -Destination "C:\sp_work\phone_grip\手机握把-v1.xlsx"
```

5. 过滤 WPS/Excel 临时锁文件：

```text
忽略 ~$ 开头的文件
```

6. 如果要覆盖文件，先检查是否被打开：

```powershell
Get-ChildItem -Force | Where-Object { $_.Name -like '~$*' }
```

看到 `~$文件名.xlsx` 时，说明文件大概率还在 WPS/Excel 中打开，覆盖会失败。

## 交付前最小校验

不要做慢速大范围渲染。交付前只校验关键字段：

- 文件能被 WPS/Excel 打开
- `Template` 页第 7 行起有数据
- 父体 SKU / 子体 SKU 正确
- 子体 Parent SKU 指向父体
- Product Type 正确
- Brand / Manufacturer 是 `Generic`
- 价格、尺寸、重量与最终价格表一致
- 必填字段非空
- 五点描述 5 个单元格非空
- `Country of Origin = China`
- `Batteries Required = No`
- `Dangerous Goods Regulations = Not Applicable`

## 速度目标

正常单产品：

- 资料齐全、模板未锁：3 到 8 分钟
- 有 Drive 成功模板可复用：更快
- 需要新增类目字段规则：10 到 20 分钟
- 文件被锁、路径异常、模板损坏：另算

如果超过 10 分钟，应该先停下来检查：

- 是否误用了全量渲染
- 是否在中文路径里硬编码文件名
- 是否有 `~$` 锁文件
- 是否在用 Google Sheets 处理复杂 Excel 模板
- 是否没有复用项目里的 `FIELD_MAP` 和成功模板规则
