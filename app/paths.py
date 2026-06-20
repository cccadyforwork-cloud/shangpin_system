from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
PROJECTS_DIR = DATA_DIR / "projects"
TEMPLATES_DIR = ROOT / "templates"
OUTPUTS_DIR = ROOT / "outputs"


PROJECT_FOLDERS = [
    "01_采购资料",
    "02_产品包装和定价",
    "03_产品详情页",
    "04_竞品参考",
    "05_模版原件"
]

PURCHASE_DIR = "01_采购资料"
PACKAGING_PRICING_DIR = "02_产品包装和定价"
PRODUCT_DETAIL_DIR = "03_产品详情页"
COMPETITOR_DIR = "04_竞品参考"
TEMPLATE_SOURCE_DIR = "05_模版原件"

LEGACY_COMPETITOR_DIR = "03_竞品参考"
LEGACY_TEMPLATE_SOURCE_DIR = "04_模板原件"
LEGACY_FILLED_TEMPLATE_DIR = "05_填表版本"
LEGACY_REMARKS_DIR = "07_上架备注"

DRAFT_DIRS = [PRODUCT_DETAIL_DIR, LEGACY_REMARKS_DIR]
TEMPLATE_DIRS = [TEMPLATE_SOURCE_DIR, LEGACY_TEMPLATE_SOURCE_DIR, LEGACY_FILLED_TEMPLATE_DIR]


def ensure_base_dirs():
    for path in [CONFIG_DIR, DATA_DIR, PROJECTS_DIR, TEMPLATES_DIR, OUTPUTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value):
    cleaned = "".join(ch if ch not in r'\/:*?"<>|' else "_" for ch in value.strip())
    cleaned = "_".join(cleaned.split())
    return cleaned or "unnamed_project"
