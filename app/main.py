import argparse
from pathlib import Path

from .analyzer import analyze_project
from .auto_fill import auto_fill_project
from .error_learning import learn_reports
from .paths import TEMPLATES_DIR, ensure_base_dirs
from .project_manager import create_project, list_projects
from .report_parser import parse_processing_summary
from .template_inspector import inspect_template
from .template_validator import validate_template_file
from .template_writer import fill_template
from .validator import validate_intake, write_validation_report
from .workbook_io import create_intake_workbook


def cmd_init(_args):
    ensure_base_dirs()
    template_path = TEMPLATES_DIR / "产品资料模板.xlsx"
    create_intake_workbook(template_path)
    print(f"已初始化上品系统：{Path(__file__).resolve().parents[1]}")
    print(f"资料表模板：{template_path}")


def cmd_new_project(args):
    project_dir, intake_path = create_project(args.name)
    print(f"已创建项目：{project_dir}")
    print(f"产品资料表：{intake_path}")


def cmd_list_projects(_args):
    projects = list_projects()
    if not projects:
        print("还没有项目。")
        return
    for project in projects:
        print(project)


def cmd_validate(args):
    findings = validate_intake(args.intake)
    output = write_validation_report(args.intake, findings, args.output)
    print(f"自检完成：{output}")
    print(f"发现 {len(findings)} 个提示。")
    error_count = sum(1 for item in findings if item["severity"] == "error")
    if error_count:
        print(f"其中 {error_count} 个 Error 建议上传前先处理。")


def cmd_analyze_project(args):
    draft_path, report_path = analyze_project(args.project_dir, args.output)
    print(f"自动提炼草稿：{draft_path}")
    print(f"资料提炼报告：{report_path}")
    print("请先人工确认草稿里的价格、类目、item_type_keyword、品牌路线、图片 URL 和尺寸重量。")


def cmd_parse_report(args):
    findings = parse_processing_summary(args.report)
    if not findings:
        print("没有识别到已配置的常见错误码。")
        return
    for item in findings:
        print(f"[{item['code']}] {item['type']}")
        print(f"含义：{item['meaning']}")
        print(f"建议：{item['fix']}")
        print(f"原文：{item['source'][:240]}")
        print("")


def cmd_inspect_template(args):
    findings, output_path = inspect_template(args.template, args.output)
    print(f"模板扫描完成：{output_path}")
    print(f"Product Type：{findings['product_type'] or '未识别'}")
    print(f"Browse Node / Item Type Keyword：{findings['browse_node'] or '未识别'}")
    print(f"必填字段数：{len(findings['required_fields'])}")


def cmd_fill_template(args):
    output_path, draft_path, template_path, written_fields = fill_template(
        args.project_dir,
        draft_path=args.draft,
        template_path=args.template,
        output_path=args.output
    )
    print(f"已写入模板：{output_path}")
    print(f"使用草稿：{draft_path}")
    print(f"使用模板：{template_path}")
    print(f"写入字段数：{len(written_fields)}")


def cmd_learn_report(args):
    added, json_path, report_path = learn_reports(args.reports, product_name=args.product, note=args.note or "")
    print(f"新增复盘记录：{len(added)}")
    print(f"结构化记录：{json_path}")
    print(f"复盘报告：{report_path}")


def cmd_check_template(args):
    findings, output_path = validate_template_file(args.template, args.output)
    print(f"模板自检完成：{output_path}")
    print(f"发现 {len(findings)} 个问题。")


def cmd_auto_fill(args):
    result = auto_fill_project(
        args.project_dir,
        draft_path=args.draft,
        template_path=args.template,
        output_path=args.output,
        force=args.force,
    )
    if result["skipped"]:
        status = result["status"]
        print("项目已标记为上传成功，默认跳过自动填表。")
        print(f"项目：{result['project_dir']}")
        print(f"最新模板：{status.get('latest_template', '未记录')}")
        print("如需重新生成，请加 --force。")
        return

    if result.get("blocked"):
        print("自动填表暂停：项目资料还不完整。")
        print(f"项目：{result['project_dir']}")
        print(f"原因：{result['reason']}")
        print(f"项目状态：{result['status_path']}")
        return

    print(f"自动填表完成：{result['filled_path']}")
    print(f"使用草稿：{result['draft_path']}")
    print(f"使用模板：{result['template_path']}")
    print(f"自检报告：{result['report_path']}")
    print(f"项目状态：{result['status_path']}")
    print(f"SKU 数：{result['sku_count']}")
    print(f"写入字段数：{result['written_field_count']}")
    print(f"模板 Error：{result['error_count']}")
    if result["status"] == "ready_for_upload":
        print("结论：本地模板自检通过，可进入人工上传。")
    else:
        print("结论：还需要先处理自检报告里的字段。")


def build_parser():
    parser = argparse.ArgumentParser(description="上品流程本地 MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="初始化目录并生成产品资料模板")
    init.set_defaults(func=cmd_init)

    new_project = subparsers.add_parser("new-project", help="创建一个产品项目")
    new_project.add_argument("name", help="项目名，例如：黑色收纳袋")
    new_project.set_defaults(func=cmd_new_project)

    list_cmd = subparsers.add_parser("list-projects", help="列出已有项目")
    list_cmd.set_defaults(func=cmd_list_projects)

    validate = subparsers.add_parser("validate", help="读取产品资料表并生成上传前自检报告")
    validate.add_argument("intake", help="产品资料 xlsx 路径")
    validate.add_argument("-o", "--output", help="自检报告输出路径")
    validate.set_defaults(func=cmd_validate)

    analyze = subparsers.add_parser("analyze-project", help="扫描项目资料并生成产品资料草稿")
    analyze.add_argument("project_dir", help="项目文件夹路径")
    analyze.add_argument("-o", "--output", help="草稿产品资料表输出路径")
    analyze.set_defaults(func=cmd_analyze_project)

    report = subparsers.add_parser("parse-report", help="解析 processing-summary 常见错误码")
    report.add_argument("report", help="processing-summary 文件路径，支持 xlsx/csv/tsv/txt")
    report.set_defaults(func=cmd_parse_report)

    inspect = subparsers.add_parser("inspect-template", help="扫描亚马逊模板字段和必填项")
    inspect.add_argument("template", help="亚马逊模板 xlsx/xlsm 路径")
    inspect.add_argument("-o", "--output", help="模板扫描报告输出路径")
    inspect.set_defaults(func=cmd_inspect_template)

    fill = subparsers.add_parser("fill-template", help="把自动提炼草稿写入亚马逊模板 Template 页")
    fill.add_argument("project_dir", help="项目文件夹路径")
    fill.add_argument("--draft", help="指定自动提炼草稿 xlsx 路径")
    fill.add_argument("--template", help="指定亚马逊模板 xlsx/xlsm 路径")
    fill.add_argument("-o", "--output", help="输出填好后的模板路径")
    fill.set_defaults(func=cmd_fill_template)

    learn = subparsers.add_parser("learn-report", help="把 processing-summary 报错沉淀到复盘库")
    learn.add_argument("reports", nargs="+", help="一个或多个 processing-summary 文件路径")
    learn.add_argument("--product", help="商品名，用于复盘归档")
    learn.add_argument("--note", help="本次修复备注")
    learn.set_defaults(func=cmd_learn_report)

    check_template = subparsers.add_parser("check-template", help="检查已填好的上传模板")
    check_template.add_argument("template", help="已填好的 xlsx/xlsm 上传模板")
    check_template.add_argument("-o", "--output", help="自检报告输出路径")
    check_template.set_defaults(func=cmd_check_template)

    auto_fill = subparsers.add_parser("auto-fill", help="自动提炼草稿、写入模板并执行模板自检")
    auto_fill.add_argument("project_dir", help="项目文件夹路径")
    auto_fill.add_argument("--draft", help="指定产品资料草稿 xlsx 路径")
    auto_fill.add_argument("--template", help="指定亚马逊模板 xlsx/xlsm 路径")
    auto_fill.add_argument("-o", "--output", help="输出填好后的模板路径")
    auto_fill.add_argument("--force", action="store_true", help="即使项目已标记上传成功也重新生成")
    auto_fill.set_defaults(func=cmd_auto_fill)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
