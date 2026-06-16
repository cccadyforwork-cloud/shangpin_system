from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
PROJECTS_DIR = DATA_DIR / "projects"
TEMPLATES_DIR = ROOT / "templates"
OUTPUTS_DIR = ROOT / "outputs"


PROJECT_FOLDERS = [
    "01_采购资料",
    "02_原始图片",
    "03_竞品参考",
    "04_模板原件",
    "05_填表版本",
    "06_处理报告",
    "07_上架备注"
]


def ensure_base_dirs():
    for path in [CONFIG_DIR, DATA_DIR, PROJECTS_DIR, TEMPLATES_DIR, OUTPUTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_name(value):
    cleaned = "".join(ch if ch not in r'\/:*?"<>|' else "_" for ch in value.strip())
    cleaned = "_".join(cleaned.split())
    return cleaned or "unnamed_project"
