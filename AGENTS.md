# Windows / Mac 最新线上源码（2026-10-09）

维护必须完整阅读 `SERVER_SOURCE.md`，从实时最新main前向整合，保留全部编辑；发布前核验 `server-source/source-manifest.json` 声明的真实服务器基线。根目录旧单机入口、历史候选与备份不能直接覆盖线上；本次归档不等于部署。公司数据、其他板块、数据库和密钥不得随源码导出。

上品填表长期规则：生成后续版本时与上一版按 SKU 比较，已存在的父体和子体一律用 `Edit (Partial Update)`，只有本次新增 SKU 用 `Create or Replace (Full Update)`；字段是否变化不影响 Action。所有路线遵循 `PROJECT_RULES.md` 和 `app/listing_action.py`，缺少上一版基准时先补齐，不把旧 SKU 当作新增。

