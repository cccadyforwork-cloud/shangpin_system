import base64
import html
import io
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageCms, ImageOps

from .batch_fast_workbench import load_ledger, save_ledger
from .paths import ROOT, safe_name


API_KEY_ENV = "GRSAI_API_KEY"
API_KEY_KEYCHAIN_SERVICE = "shangpin-system-grsai-api-key"
API_BASE_ENV = "GRSAI_API_BASE_URL"
MODEL_ENV = "GRSAI_IMAGE_MODEL"
DEFAULT_API_BASE = "https://grsai.dakka.com.cn"
DEFAULT_MODEL = "gpt-image-2.5-sunburst"
FALLBACK_MODELS = ("gpt-image-2.5-flare", "gpt-image-2.5", "gpt-image-2")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCE_IMAGES = 10
AMAZON_UPLOAD_TARGET_BYTES = 4_500_000
AMAZON_MIN_IMAGE_SIDE = 500
AMAZON_MAX_IMAGE_SIDE = 10_000
DESKTOP_BATCH_SIZE = 10
DESKTOP_BATCH_PATTERN = re.compile(r"^本轮第(\d+)批_(进行中|10组)$")
_JOBS = {}
_LOCK = threading.Lock()


def _srgb_profile_bytes():
    try:
        return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    except Exception:
        return None


_SRGB_PROFILE = _srgb_profile_bytes()


def prepare_amazon_upload_image(source_path, target_path=None):
    """Convert a generated image to a high-quality, upload-safe RGB JPEG."""
    source = Path(source_path)
    target = Path(target_path) if target_path else source.with_suffix(".jpg")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.stem}.upload-ready{target.suffix}")

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        longest_side = max(image.size)
        if longest_side < AMAZON_MIN_IMAGE_SIDE or longest_side > AMAZON_MAX_IMAGE_SIDE:
            raise ValueError(
                f"图片尺寸 {image.width}×{image.height} 不在亚马逊允许的 "
                f"{AMAZON_MIN_IMAGE_SIDE}–{AMAZON_MAX_IMAGE_SIDE} 像素范围内。"
            )
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, "white")
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb = image.convert("RGB")

        save_options = {
            "format": "JPEG",
            "optimize": True,
            "progressive": False,
            "dpi": (72, 72),
        }
        if _SRGB_PROFILE:
            save_options["icc_profile"] = _SRGB_PROFILE

        # Keep the highest JPEG quality that stays safely below the 5 MB uploader cap.
        for quality in (95, 93, 91, 89, 87, 85, 82, 80, 77, 74):
            rgb.save(temp, quality=quality, **save_options)
            if temp.stat().st_size <= AMAZON_UPLOAD_TARGET_BYTES:
                break
        else:
            temp.unlink(missing_ok=True)
            raise ValueError("图片在保持原始像素尺寸时无法压缩到 4.5 MB 以下。")

    with Image.open(temp) as checked:
        checked.verify()
    if temp.stat().st_size > AMAZON_UPLOAD_TARGET_BYTES:
        temp.unlink(missing_ok=True)
        raise ValueError("图片压缩后仍超过 4.5 MB。")
    temp.replace(target)
    if source.resolve() != target.resolve():
        source.unlink(missing_ok=True)
    return target


def load_api_key():
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if api_key:
        return api_key
    if os.name != "posix" or not shutil.which("security"):
        return ""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", API_KEY_KEYCHAIN_SERVICE, "-w"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _resolve(path_value):
    path = Path(str(path_value or "")).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _store(path_value):
    path = _resolve(path_value)
    try:
        return path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _find_row(data, batch_id, row_id):
    batch = next((item for item in data.get("batches", []) if item.get("id") == batch_id), None)
    if batch is None:
        raise ValueError("找不到批次。")
    row = next((item for item in batch.get("rows", []) if item.get("id") == row_id), None)
    if row is None:
        raise ValueError("找不到产品行。")
    return batch, row


def _group_entry(row, group_key):
    key = str(group_key or "default").strip() or "default"
    groups = row.setdefault("image_groups", {})
    return key, groups.setdefault(key, {})


def _legacy_group(row):
    return {
        "reference_files": list(row.get("image_reference_files", []) or []),
        "generated_files": list(row.get("generated_image_files", []) or []),
        "zip": row.get("image_zip", ""),
        "status": row.get("image_generation_status", ""),
        "error": row.get("image_generation_error", ""),
        "generated_at": row.get("image_generated_at", ""),
    }


def attach_reference_screenshot(
    batch_id,
    row_id,
    filename,
    source,
    ledger_path,
    files_dir,
    image_group_key="default",
    group_label="",
):
    suffix = Path(filename or "").suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise ValueError("参考截图只支持 PNG、JPG、JPEG、WEBP。")
    data = load_ledger(ledger_path)
    _batch, row = _find_row(data, batch_id, row_id)
    group_key, group = _group_entry(row, image_group_key)
    target_dir = (
        Path(files_dir)
        / safe_name(batch_id)
        / safe_name(row_id)
        / "image_groups"
        / safe_name(group_key)
        / "image_references"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    index = len([path for path in target_dir.iterdir() if path.is_file()]) + 1
    target = target_dir / f"{index:02d}_{safe_name(Path(filename).name)}"
    with target.open("wb") as output:
        if hasattr(source, "read"):
            shutil.copyfileobj(source, output)
        else:
            output.write(bytes(source))
    references = [
        _store(path)
        for path in sorted(target_dir.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    group["label"] = group_label or group.get("label", "")
    group["reference_files"] = references
    group["status"] = "待生成"
    group["error"] = ""
    save_ledger(data, ledger_path)
    return target, row


def fetch_reference_images(
    batch_id,
    row_id,
    source_urls,
    ledger_path,
    files_dir,
    image_group_key="default",
    group_label="",
    product_name_override="",
):
    urls = [str(value or "").strip() for value in source_urls if str(value or "").strip()]
    if not urls:
        raise ValueError("这个图组没有可用的亚马逊原链接。")

    galleries = [_amazon_gallery_urls(url) for url in urls]
    selected = []
    seen = set()
    # 组合商品优先保留每个来源的主图，再按画廊顺序轮流补充辅图。
    for index in range(max((len(items) for items in galleries), default=0)):
        for gallery in galleries:
            if index >= len(gallery):
                continue
            image_url = gallery[index]
            identity = re.sub(r"\._[^/]+_(?=\.[a-zA-Z]+$)", "", image_url)
            if identity in seen:
                continue
            seen.add(identity)
            selected.append(image_url)
            if len(selected) >= MAX_REFERENCE_IMAGES:
                break
        if len(selected) >= MAX_REFERENCE_IMAGES:
            break
    if not selected:
        raise ValueError("没有从亚马逊商品页读取到原产品图片。")

    downloaded = [_download_amazon_image(url, urls[0]) for url in selected]
    data = load_ledger(ledger_path)
    _batch, row = _find_row(data, batch_id, row_id)
    group_key, group = _group_entry(row, image_group_key)
    target_dir = (
        Path(files_dir)
        / safe_name(batch_id)
        / safe_name(row_id)
        / "image_groups"
        / safe_name(group_key)
        / "image_references"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    for existing in target_dir.iterdir():
        if existing.is_file() and existing.suffix.lower() in IMAGE_SUFFIXES:
            existing.unlink()
    display_name = product_name_override or row.get("product_name") or row.get("asin") or row_id
    if group_label:
        display_name = f"{display_name}-{group_label}"
    references = []
    for index, (content, suffix) in enumerate(downloaded, start=1):
        target = target_dir / f"{safe_name(display_name)}-{index:02d}{suffix}"
        target.write_bytes(content)
        references.append(_store(target))

    group["label"] = group_label or group.get("label", "")
    group["reference_files"] = references
    group["generated_files"] = []
    group["zip"] = ""
    group["status"] = "待生成"
    group["error"] = ""
    group["fetched_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    save_ledger(data, ledger_path)
    return {"ok": True, "status": "待生成", "count": len(references)}


def _amazon_gallery_urls(source_url):
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not (
        hostname == "a.co"
        or hostname == "amzn.to"
        or hostname.startswith("www.amazon.")
        or hostname.startswith("amazon.")
    ):
        raise ValueError("原产品链接不是受支持的亚马逊商品地址。")
    page, final_url = _fetch_amazon_page(
        source_url,
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
        ),
    )
    gallery = _extract_amazon_gallery_urls(page)
    if gallery:
        return gallery

    asin_match = re.search(r"/(?:dp|gp/(?:product|aw/d))/([A-Z0-9]{10})(?:[/?]|$)", final_url, re.I)
    if asin_match:
        mobile_url = f"https://www.amazon.com/gp/aw/d/{asin_match.group(1).upper()}"
        page, _final_url = _fetch_amazon_page(
            mobile_url,
            (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                "AppleWebKit/605.1.15 Version/17.5 Mobile/15E148 Safari/604.1"
            ),
        )
        gallery = _extract_amazon_gallery_urls(page)
    return gallery


def _fetch_amazon_page(url, user_agent):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", "replace")
        return page, response.geturl()


def _extract_amazon_gallery_urls(page):
    urls = []
    match = re.search(
        r"['\"]colorImages['\"]\s*:\s*\{\s*['\"]initial['\"]\s*:\s*A\.\$\.parseJSON\('(.*?)'\)",
        page,
        re.DOTALL,
    )
    if match:
        serialized = html.unescape(match.group(1)).replace("\\'", "'")
        try:
            items = json.loads(serialized)
        except json.JSONDecodeError:
            items = []
        for item in items:
            image_url = str(item.get("hiRes") or item.get("large") or "").strip()
            if image_url:
                urls.append(image_url)
    if not urls:
        urls.extend(re.findall(r"['\"]hiRes['\"]\s*:\s*['\"](https://[^'\"]+)['\"]", page))
    if not urls:
        mobile_block = page
        block_start = page.find('id="image-block"')
        if block_start >= 0:
            mobile_block = page[block_start:]
        urls.extend(
            re.findall(
                r'data-a-hires="(https://m\.media-amazon\.com/images/I/[^\"]+)"',
                mobile_block,
            )
        )
    return list(dict.fromkeys(html.unescape(url) for url in urls))


def _download_amazon_image(image_url, referer):
    parsed = urlparse(image_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        hostname == "m.media-amazon.com" or hostname.endswith(".ssl-images-amazon.com")
    ):
        raise ValueError("亚马逊画廊返回了不受支持的图片地址。")
    request = urllib.request.Request(
        image_url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": referer},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
        content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].lower()
    if not content:
        raise ValueError("亚马逊原产品图片下载结果为空。")
    suffix = {
        "image/png": ".png",
        "image/webp": ".webp",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
    }.get(content_type, Path(parsed.path).suffix.lower())
    if suffix not in IMAGE_SUFFIXES:
        suffix = ".jpg"
    return content, suffix


def enrich_payload(data, ledger_path):
    for batch in data.get("batches", []):
        for row in batch.get("rows", []):
            specs = row.get("image_group_specs") or [{"key": "default", "label": ""}]
            stored_groups = row.get("image_groups", {}) or {}
            legacy = _legacy_group(row)
            rendered_groups = []
            for index, spec in enumerate(specs):
                key = str(spec.get("key") or "default")
                stored = stored_groups.get(key)
                if stored is None and spec.get("use_legacy", index == 0):
                    stored = legacy
                stored = stored or {}
                references = []
                for raw in stored.get("reference_files", []) or []:
                    path = _resolve(raw)
                    if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                        references.append({"path": str(path), "name": path.name})
                generated = []
                for raw in stored.get("generated_files", []) or []:
                    path = _resolve(raw)
                    if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                        generated.append({"path": str(path), "name": path.name})
                zip_path = _resolve(stored.get("zip", "")) if stored.get("zip") else None
                rendered_groups.append({
                    "key": key,
                    "label": spec.get("label") or stored.get("label", "") or "图组",
                    "source_url": spec.get("source_url", ""),
                    "source_row_id": spec.get("source_row_id", ""),
                    "status": stored.get("status") or ("待生成" if references else "待截图"),
                    "error": stored.get("error", ""),
                    "reference_count": len(references),
                    "generated_count": len(generated),
                    "references": references,
                    "zip": {
                        "path": str(zip_path) if zip_path else "",
                        "name": zip_path.name if zip_path else "",
                        "exists": bool(zip_path and zip_path.is_file()),
                    },
                })
            row["image_groups"] = rendered_groups
            row["image_group"] = rendered_groups[0]
            row["all_image_groups_ready"] = len(rendered_groups) > 1 and all(
                group["zip"]["exists"] for group in rendered_groups
            )
    data["image_api_configured"] = bool(load_api_key())
    return data


def referenced_image_file(path_value, ledger_path):
    candidate = _resolve(path_value)
    data = load_ledger(ledger_path)
    allowed = set()
    for batch in data.get("batches", []):
        for row in batch.get("rows", []):
            for raw in row.get("image_reference_files", []) or []:
                allowed.add(str(_resolve(raw)))
            if row.get("image_zip"):
                allowed.add(str(_resolve(row["image_zip"])))
            for group in (row.get("image_groups", {}) or {}).values():
                for raw in group.get("reference_files", []) or []:
                    allowed.add(str(_resolve(raw)))
                for raw in group.get("generated_files", []) or []:
                    allowed.add(str(_resolve(raw)))
                if group.get("zip"):
                    allowed.add(str(_resolve(group["zip"])))
    return candidate if str(candidate) in allowed else None


def start_generation(
    batch_id,
    row_id,
    ledger_path,
    files_dir,
    image_group_key="default",
    group_label="",
    product_name_override="",
):
    api_key = load_api_key()
    if not api_key:
        raise ValueError(f"尚未配置 {API_KEY_ENV}，无法调用生图接口。")
    data = load_ledger(ledger_path)
    _batch, row = _find_row(data, batch_id, row_id)
    group_key, group = _group_entry(row, image_group_key)
    references = [_resolve(path) for path in group.get("reference_files", []) or []]
    references = [path for path in references if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
    if not references:
        raise ValueError("这个产品还没有内置浏览器参考截图。")
    job_key = f"{batch_id}:{row_id}:{group_key}"
    with _LOCK:
        running = _JOBS.get(job_key)
        if running and running.is_alive():
            return {"ok": True, "status": "生成中"}
        group["label"] = group_label or group.get("label", "")
        group["status"] = "生成中"
        group["error"] = ""
        save_ledger(data, ledger_path)
        thread = threading.Thread(
            target=_generate_worker,
            args=(
                batch_id,
                row_id,
                group_key,
                group_label,
                product_name_override,
                references,
                ledger_path,
                files_dir,
                api_key,
                job_key,
            ),
            daemon=True,
        )
        _JOBS[job_key] = thread
        thread.start()
    return {"ok": True, "status": "生成中"}


def export_generated_images_to_desktop(
    batch_id,
    row_id,
    ledger_path,
    image_group_key="default",
    group_label="",
    product_name_override="",
    desktop_dir=None,
):
    data = load_ledger(ledger_path)
    _batch, row = _find_row(data, batch_id, row_id)
    group_key, group = _group_entry(row, image_group_key)
    generated = [_resolve(path) for path in group.get("generated_files", []) or []]
    generated = [path for path in generated if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
    if not generated:
        raise ValueError("这个图组还没有可下载的生成图片。")

    product_name = product_name_override or row.get("product_name") or row.get("asin") or row_id
    display_name = f"{product_name}-{group_label}" if group_label else product_name
    desktop_root = Path(desktop_dir) if desktop_dir else Path.home() / "Desktop"
    export_root = desktop_root / "退货翻新新图组"
    export_root.mkdir(parents=True, exist_ok=True)
    folder_name = safe_name(display_name)

    with _LOCK:
        # Refresh an already exported group in place, including historical batch folders.
        candidates = [export_root / folder_name]
        candidates.extend(
            container / folder_name
            for container in export_root.iterdir()
            if container.is_dir()
        )
        target_dir = next((path for path in candidates if path.is_dir()), None)
        current_batch = None
        batch_index = None
        if target_dir is None:
            batch_entries = []
            for container in export_root.iterdir():
                if not container.is_dir():
                    continue
                match = DESKTOP_BATCH_PATTERN.match(container.name)
                if match:
                    batch_entries.append((int(match.group(1)), match.group(2), container))
            in_progress = [item for item in batch_entries if item[1] == "进行中"]
            if in_progress:
                batch_index, _state, current_batch = max(in_progress, key=lambda item: item[0])
            else:
                batch_index = max((item[0] for item in batch_entries), default=0) + 1
                current_batch = export_root / f"本轮第{batch_index:02d}批_进行中"
                current_batch.mkdir(parents=True, exist_ok=True)
            target_dir = current_batch / folder_name

        target_dir.mkdir(parents=True, exist_ok=True)
        for existing in target_dir.iterdir():
            if existing.is_file() and existing.suffix.lower() in IMAGE_SUFFIXES:
                existing.unlink()
        copied = []
        for source in generated:
            target = target_dir / source.name
            shutil.copy2(source, target)
            copied.append(target)

        if current_batch is not None:
            group_count = sum(1 for path in current_batch.iterdir() if path.is_dir())
            if group_count >= DESKTOP_BATCH_SIZE:
                completed_batch = export_root / f"本轮第{batch_index:02d}批_10组"
                if not completed_batch.exists():
                    current_batch.rename(completed_batch)
                    target_dir = completed_batch / folder_name
    return {
        "ok": True,
        "path": str(target_dir),
        "count": len(copied),
        "image_group_key": group_key,
    }


def _generate_worker(
    batch_id,
    row_id,
    group_key,
    group_label,
    product_name_override,
    references,
    ledger_path,
    files_dir,
    api_key,
    job_key,
):
    try:
        data = load_ledger(ledger_path)
        batch, row = _find_row(data, batch_id, row_id)
        product_name = product_name_override or row.get("product_name") or row.get("asin") or row_id
        display_name = f"{product_name}-{group_label}" if group_label else product_name
        target_dir = (
            Path(files_dir)
            / safe_name(batch_id)
            / safe_name(row_id)
            / "image_groups"
            / safe_name(group_key)
            / "generated_images"
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        for index, reference in enumerate(references, start=1):
            prompt = _generation_prompt(product_name, index == 1)
            image_bytes = _call_api(reference, prompt, api_key)
            raw_target = target_dir / f"{safe_name(display_name)}-{index}.png"
            raw_target.write_bytes(image_bytes)
            target = prepare_amazon_upload_image(
                raw_target,
                target_dir / f"{safe_name(display_name)}-{index}.jpg",
            )
            outputs.append(target)
        zip_path = target_dir.parent / f"{safe_name(display_name)}_新图组.zip"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for output in outputs:
                archive.write(output, arcname=output.name)
        zip_path.write_bytes(buffer.getvalue())
        data = load_ledger(ledger_path)
        _batch, row = _find_row(data, batch_id, row_id)
        with _LOCK:
            data = load_ledger(ledger_path)
            _batch, row = _find_row(data, batch_id, row_id)
            _key, group = _group_entry(row, group_key)
            group["label"] = group_label or group.get("label", "")
            group["zip"] = _store(zip_path)
            group["generated_files"] = [_store(path) for path in outputs]
            group["status"] = "已生成"
            group["error"] = ""
            group["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
            save_ledger(data, ledger_path)
    except Exception as exc:
        data = load_ledger(ledger_path)
        try:
            with _LOCK:
                data = load_ledger(ledger_path)
                _batch, row = _find_row(data, batch_id, row_id)
                _key, group = _group_entry(row, group_key)
                group["status"] = "生成失败"
                group["error"] = str(exc)[:500]
                save_ledger(data, ledger_path)
        except Exception:
            pass
    finally:
        with _LOCK:
            _JOBS.pop(job_key, None)


def _generation_prompt(product_name, is_main):
    shared = (
        f"参考图来自 {product_name} 的亚马逊商品页截图。只重绘截图中的原始商品图片，忽略并移除浏览器界面、"
        "亚马逊页面元素、按钮、缩略图、边框和光标。严格保持商品外形、结构、比例、颜色、纹理、数量、"
        "配件、摆放关系和原图表达，不增加或删除任何零件，不添加品牌、徽标或未经支持的卖点。"
    )
    if is_main:
        return shared + (
            "这是场景化主图：必须沿用参考图原有的真实使用场景、拍摄角度、商品状态和主体位置，"
            "只允许对环境陈设、背景虚化、光线、色调和画面细节做轻微变化，以形成一张新的相似场景图。"
            "商品本身必须与参考图完全一致，尤其不得改变商品的外形、结构、开口、手柄、材质、比例、"
            "颜色、使用方式以及商品与手、食物、容器之间的关系。不要改成白底，不要把商品单独抠出，"
            "不要增加文字、尺寸线、徽标、卖点标签或无关物品。输出干净的正方形电商场景主图。"
        )
    return shared + (
        "这是辅图：高保真复刻原图的构图、场景、信息层级和视觉关系；如果截图内原图包含文字，保持其含义和位置，"
        "无法准确还原的文字区域宁可留空，不要编造内容。输出干净的正方形电商图片。"
    )


def _call_api(reference_path, prompt, api_key):
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(reference_path.suffix.lower(), "image/png")
    encoded = base64.b64encode(reference_path.read_bytes()).decode("ascii")
    base_url = os.environ.get(API_BASE_ENV, DEFAULT_API_BASE).rstrip("/")
    configured_model = os.environ.get(MODEL_ENV, DEFAULT_MODEL).strip() or DEFAULT_MODEL
    models = tuple(dict.fromkeys((configured_model, *FALLBACK_MODELS)))
    last_error = "生图接口没有可用模型。"
    result = None
    for model in models:
        large_model = model.endswith(("-sunburst", "-flare", "-vip"))
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [f"data:{mime};base64,{encoded}"],
            "aspectRatio": "2048x2048" if large_model else "1024x1024",
            "quality": "high" if large_model else "auto",
            "replyType": "async",
        }
        request = urllib.request.Request(
            f"{base_url}/v1/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                submitted = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            body = getattr(exc, "read", lambda: b"")()
            try:
                submitted = json.loads(body.decode("utf-8"))
            except Exception:
                submitted = {"error": str(exc)}
        if submitted.get("status") == "succeeded" and submitted.get("results"):
            result = submitted
            break
        task_id = str(submitted.get("id") or "").strip()
        if submitted.get("status") == "running" and task_id:
            result = _poll_result(base_url, task_id, api_key)
            if result.get("status") == "succeeded" and result.get("results"):
                break
        last_error = submitted.get("error") or (result or {}).get("error") or f"{model} 生成失败"
        result = None
    if not result:
        raise RuntimeError(last_error)
    image_url = str(result["results"][0].get("url") or "").strip()
    if not image_url.startswith(("https://", "http://")):
        raise RuntimeError("生图接口没有返回可下载的图片地址。")
    with urllib.request.urlopen(image_url, timeout=180) as response:
        content = response.read()
    if not content:
        raise RuntimeError("生成图片下载结果为空。")
    return content


def _poll_result(base_url, task_id, api_key, timeout_seconds=900):
    deadline = time.monotonic() + timeout_seconds
    result = {"status": "running"}
    while time.monotonic() < deadline:
        request = urllib.request.Request(
            f"{base_url}/v1/api/result?id={task_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        if result.get("status") != "running":
            return result
        time.sleep(4)
    return {"status": "failed", "error": "生图接口等待结果超时。"}
