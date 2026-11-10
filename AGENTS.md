# Windows / Mac 最新线上源码（2026-10-09）

维护必须完整阅读 `SERVER_SOURCE.md`，从实时最新main前向整合，保留全部编辑；发布前核验 `server-source/source-manifest.json` 声明的真实服务器基线。根目录旧单机入口、历史候选与备份不能直接覆盖线上；本次归档不等于部署。公司数据、其他板块、数据库和密钥不得随源码导出。

上品填表长期规则：上传报错后的修正版，父体和全部子体一律用 `Create or Replace (Full Update)`；普通后续版本才按上一版 SKU 比较，已存在 SKU 用 `Edit (Partial Update)`，新增 SKU 用 `Create or Replace (Full Update)`。所有路线遵循 `PROJECT_RULES.md` 和 `app/listing_action.py`；缺少上一版基准时先补齐。

SQUEEGEE 上传反馈确认子体必填 Generic Keyword、Handle Material、Blade Material、Product Compliance Certificate；填写材质须对应实际选款，不能套用其他手柄款。上传前按 `app/template_validator.py` 自检。
WATER_PURIFICATION_UNIT 上传反馈确认子体需填写 Special Features、Capacity 及单位、Purification Method、Container Type，以及商品本体长、宽、高三组数值及单位（V2 的 99022 确认不能只补长度）；须用实际产品资料，明确区分过滤寿命与容器容量、商品本体与包装尺寸。Container Type 应取模板有效值，并记录分类选择与套装实际包含物。

Listing 文案新规则：Item Name 不超过 75 字符，Item Highlight 不超过 125 字符；父体可填写概括全部子体的亮点，父体标题不强制写“多色可选”或“多款式可选”。

新建上品 SKU 统一规则：1店使用 `TTCA-`，2店及其他店铺使用 `CA-`；英文品名段最多两个词、各词首字母大写并直接拼接；父体不加 `-P`/`-PARENT`；子体在同一品名段后追加变体，数量使用 `2P`/`4P`、计量单位小写、混色直接拼接。正式 `auto-fill` 与批量快速路线共用 `app/sku_rules.py`。已有、供应商明确提供或已上传 SKU 不自动改名。

