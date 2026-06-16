# 上品自动填表 MVP 存档状态

存档日期：2026-06-17

## 当前能力

- 创建产品项目目录和产品资料表。
- 从采购资料、竞品资料、PDF、HTML、Excel、文本文件中生成产品资料草稿。
- 将产品资料草稿写入 Amazon 上传模板的 `Template` 页。
- 对已填写模板执行上传前自检。
- 解析 processing-summary 常见错误。
- 将上传报错沉淀到复盘库。
- 通过 `project_status.json` 记录每个项目的流程状态。
- 通过 `auto-fill` 命令串联自动提炼、写模板和模板自检。

## 已验证样品

- 花园艺手套：用户确认已成功上传。
- 花束卡片夹：用户确认已成功上传。
- 瑜伽砖：用户确认已成功上传。

## 当前项目状态

- `data/projects/20260606_花园艺手套/project_status.json`：`uploaded_success`
- `data/projects/20260604_花束卡片夹/project_status.json`：`uploaded_success`
- `data/projects/20260530_瑜伽砖/project_status.json`：`uploaded_success`
- `data/projects/20260530_厨房硅胶刮刀/project_status.json`：`blocked`，缺 Amazon 模板

## 常用命令

```bash
python3 run.py list-projects
python3 run.py auto-fill "data/projects/项目目录"
python3 run.py auto-fill "data/projects/项目目录" --force
python3 run.py check-template "路径/已填写模板.xlsx"
python3 run.py learn-report "路径/processing-summary.xlsx" --product "产品名"
```

## 下一步建议

1. 给 `list-projects` 增加项目状态汇总显示。
2. 给成功上传后的项目增加 `mark-uploaded` 命令，减少手动编辑 JSON。
3. 根据三款成功上传样品继续固化 product type 专属字段规则。
4. 增加基础测试，覆盖 `auto-fill`、状态读写和模板自检。
