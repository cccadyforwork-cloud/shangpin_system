# Windows / Mac 最新线上源码（2026-10-09）

维护必须完整阅读 `SERVER_SOURCE.md`，从实时最新main前向整合，保留全部编辑；发布前核验 `server-source/source-manifest.json` 声明的真实服务器基线。根目录旧单机入口、历史候选与备份不能直接覆盖线上；本次归档不等于部署。公司数据、其他板块、数据库和密钥不得随源码导出。

上品填表长期规则：上传报错后的修正版，父体和全部子体一律用 `Create or Replace (Full Update)`；普通后续版本才按上一版 SKU 比较，已存在 SKU 用 `Edit (Partial Update)`，新增 SKU 用 `Create or Replace (Full Update)`。所有路线遵循 `PROJECT_RULES.md` 和 `app/listing_action.py`；缺少上一版基准时先补齐。

SQUEEGEE 上传反馈确认子体必填 Generic Keyword、Handle Material、Blade Material、Product Compliance Certificate；填写材质须对应实际选款，不能套用其他手柄款。上传前按 `app/template_validator.py` 自检。

