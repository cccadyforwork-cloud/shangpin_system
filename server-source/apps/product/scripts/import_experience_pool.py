import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.experience_pool import POOL_PATH, import_package, statistics


def main():
    parser = argparse.ArgumentParser(description="把历史上品经验包导入私有上品经验池")
    parser.add_argument("packages", nargs="+", help="一个或多个 zip 经验包")
    parser.add_argument("--pool", default=str(POOL_PATH), help="经验池 sqlite3 文件")
    args = parser.parse_args()
    for package in args.packages:
        print(json.dumps(import_package(package, args.pool), ensure_ascii=False))
    print(json.dumps({"pool": args.pool, **statistics(args.pool)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
