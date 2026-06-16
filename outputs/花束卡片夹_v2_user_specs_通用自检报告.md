# 花束卡片夹 v2 通用自检报告

- 检查文件：/Users/admin/Desktop/上品模版填写上传/shangpin_system/data/projects/20260604_花束卡片夹/05_填表版本/花束卡片夹_v2_user_specs.xlsx
- SKU 行数：5
- Error：0
- Warning：1

## 核验摘要

- 未发现阻断上传的结构/必填/单位/品牌路线错误。
- 存在 Warning，需要人工确认。

## SKU 明细

- 行 7: CardPick-Circle-10 | Round | 10 Pack | List 2.99 | Haul 2.99 | 13.78 x 3.54 x 0.59 inches | 0.15 pounds
- 行 8: CardPick-Stars-10 | Star | 10 Pack | List 2.99 | Haul 2.99 | 13.78 x 3.54 x 0.59 inches | 0.15 pounds
- 行 9: CardPick-Heart-10 | Heart | 10 Pack | List 2.99 | Haul 2.99 | 13.78 x 3.54 x 0.59 inches | 0.15 pounds
- 行 10: CardPick-Circle-Pink-10 | Pink Round | 10 Pack | List 3.29 | Haul 3.29 | 14.17 x 3.54 x 0.59 inches | 0.15 pounds
- 行 11: CardPick-Bear-Gold-10 | Gold Bear | 10 Pack | List 3.29 | Haul 3.29 | 13.78 x 3.54 x 0.59 inches | 0.15 pounds

## 问题清单

- [WARNING] 类目匹配: 当前模板为 BOOK_DOCUMENT_STAND / cookbook-stands。该类目看起来更像书架/食谱架，和花束卡片夹可能不匹配，建议上传前确认类目模板。

## 已通过项

- SKU 不为空且唯一
- SKU 不含中文、空格或特殊符号
- 独立 SKU 的 Parentage / Parent SKU / Variation Theme 为空
- Brand / Manufacturer 均为 Generic
- List Price 与 Haul Price 均为数字且一致
- Haul Price 均低于 20 阈值
- 包装尺寸数值和单位成对填写，单位为 inches
- 包装重量数值和单位成对填写，单位为 pounds
- 非电池产品字段为 batteries_required=No / batteries_included=No
- 危险品字段为 Not Applicable
- 主图 URL 留空，未误填本地路径/竞品/1688 链接
- 未发现供应商名或竞品品牌进入标题/描述/卖点