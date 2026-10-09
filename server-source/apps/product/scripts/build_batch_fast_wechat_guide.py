from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "批量快速上品路线_微信长图V3.png"
FONT_MEDIUM = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"

SCREEN_GIT = Path(
    "/var/folders/wt/_hvgy0b97qs6n_brjc39mdkh0000gn/T/TemporaryItems/"
    "NSIRD_screencaptureui_A8CvhF/截屏2026-09-01 07.04.08.png"
)
SCREEN_CODEX_1 = Path("/Users/admin/Downloads/截屏2026-09-01 07.02.13.png")
SCREEN_CODEX_2 = Path("/Users/admin/Downloads/截屏2026-09-01 07.02.28.png")
SCREEN_OPEN_WITH = Path("/Users/admin/Downloads/截屏2026-09-01 07.02.41.png")
SCREEN_WORKBENCH = Path(
    "/var/folders/wt/_hvgy0b97qs6n_brjc39mdkh0000gn/T/TemporaryItems/"
    "NSIRD_screencaptureui_cHTDPt/截屏2026-09-01 07.07.45.png"
)

W = 1242
CANVAS_H = 9000
MARGIN = 66
CONTENT_W = W - MARGIN * 2

BG = "#F3F7FA"
INK = "#152331"
MUTED = "#617080"
BLUE = "#2F6FED"
BLUE_DARK = "#123A72"
TEAL = "#14A982"
PALE_BLUE = "#EAF2FF"
PALE_TEAL = "#E8F8F3"
LINE = "#D9E2EA"
WHITE = "#FFFFFF"
NAVY = "#0B1830"


def font(size, medium=False):
    return ImageFont.truetype(FONT_MEDIUM if medium else FONT_LIGHT, size=size)


F_TITLE = font(66, True)
F_SUBTITLE = font(31)
F_SECTION = font(39, True)
F_BODY = font(29)
F_BODY_BOLD = font(29, True)
F_SMALL = font(24)
F_TINY = font(21)
F_STEP = font(26, True)
F_CODE = font(26, True)


canvas = Image.new("RGB", (W, CANVAS_H), BG)
draw = ImageDraw.Draw(canvas)
y = 0


def rounded_box(x, top, width, height, fill=WHITE, outline=None, radius=28, shadow=True):
    if shadow:
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(layer)
        shadow_draw.rounded_rectangle(
            (x + 3, top + 10, x + width + 3, top + height + 10),
            radius=radius,
            fill=(17, 41, 64, 22),
        )
        layer = layer.filter(ImageFilter.GaussianBlur(11))
        canvas.paste(layer, (0, 0), layer)
    draw.rounded_rectangle(
        (x, top, x + width, top + height),
        radius=radius,
        fill=fill,
        outline=outline,
        width=2 if outline else 1,
    )


def wrap_lines(text, chosen_font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            trial = current + char
            if draw.textlength(trial, font=chosen_font) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def text_block(x, top, text, chosen_font=F_BODY, fill=INK, max_width=CONTENT_W, spacing=14):
    lines = wrap_lines(text, chosen_font, max_width)
    line_h = chosen_font.size + spacing
    for index, line in enumerate(lines):
        draw.text((x, top + index * line_h), line, font=chosen_font, fill=fill)
    return top + len(lines) * line_h


def step_header(number, title, top):
    draw.rounded_rectangle((MARGIN, top, MARGIN + 126, top + 52), radius=26, fill=BLUE)
    draw.text((MARGIN + 16, top + 10), f"STEP {number}", font=F_STEP, fill=WHITE)
    draw.text((MARGIN + 148, top + 3), title, font=F_SECTION, fill=INK)
    return top + 76


def bullet(x, top, text, color=TEAL, max_width=970):
    draw.ellipse((x, top + 12, x + 14, top + 26), fill=color)
    return text_block(x + 30, top, text, F_BODY, INK, max_width=max_width, spacing=13)


def code_box(top, text, height=None):
    lines = wrap_lines(text, F_CODE, CONTENT_W - 92)
    line_h = F_CODE.size + 16
    box_h = height or (len(lines) * line_h + 52)
    rounded_box(MARGIN, top, CONTENT_W, box_h, fill=NAVY, radius=23, shadow=False)
    draw.rounded_rectangle((MARGIN + 24, top + 23, MARGIN + 34, top + box_h - 23), radius=5, fill=TEAL)
    for index, line in enumerate(lines):
        draw.text((MARGIN + 54, top + 24 + index * line_h), line, font=F_CODE, fill=WHITE)
    return top + box_h


def screenshot(path, top, max_width=CONTENT_W, crop=None, caption=None, align="center"):
    image = Image.open(path).convert("RGB")
    if crop:
        image = image.crop(crop)
    ratio = min(max_width / image.width, 1.7)
    image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    frame_pad = 14
    frame_w = image.width + frame_pad * 2
    frame_h = image.height + frame_pad * 2
    x = MARGIN if align == "left" else (W - frame_w) // 2
    rounded_box(x, top, frame_w, frame_h, fill=WHITE, outline=LINE, radius=24, shadow=True)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius=14, fill=255)
    canvas.paste(image, (x + frame_pad, top + frame_pad), mask)
    bottom = top + frame_h
    if caption:
        draw.text((MARGIN, bottom + 16), caption, font=F_TINY, fill=MUTED)
        bottom += 52
    return bottom


# Header
draw.rectangle((0, 0, W, 610), fill=NAVY)
draw.rounded_rectangle((MARGIN, 66, MARGIN + 260, 116), radius=25, fill="#18315A")
draw.text((MARGIN + 26, 78), "团队操作手册 · V3", font=F_SMALL, fill="#AFCBFF")
draw.text((MARGIN, 164), "批量快速上品路线", font=F_TITLE, fill=WHITE)
draw.text((MARGIN, 258), "从模板准备到 Amazon 上传，一张图走完整个流程", font=F_SUBTITLE, fill="#C7D5EA")

flow_y = 354
flow_items = ["更新 Git", "打开工作台", "上传模板", "生成 V1", "报错改 V2"]
box_w = 190
gap = 22
for index, label in enumerate(flow_items):
    x = MARGIN + index * (box_w + gap)
    draw.rounded_rectangle((x, flow_y, x + box_w, flow_y + 72), radius=22, fill="#152A4C")
    draw.text((x + 28, flow_y + 19), label, font=F_SMALL, fill=WHITE)
    if index < len(flow_items) - 1:
        draw.text((x + box_w + 3, flow_y + 20), "→", font=F_SMALL, fill="#62D8B9")

y = 650
rounded_box(MARGIN, y, CONTENT_W, 235, fill=PALE_TEAL, outline="#BFEBDD", radius=30, shadow=False)
draw.text((MARGIN + 36, y + 32), "先理解：工作台就是一个记录本", font=F_SECTION, fill="#0A6B55")
y2 = text_block(
    MARGIN + 36,
    y + 94,
    "左边 Codex 对话负责接收指令、生成文件和处理报错；右边工作台负责记录竞品页面、原始模板、输出版本和上传状态。",
    F_BODY,
    INK,
    max_width=CONTENT_W - 72,
)
draw.text((MARGIN + 36, y2 + 8), "在对话中生成的填表文件，会自动同步到右侧工作台。", font=F_BODY_BOLD, fill="#0A6B55")

y = 930
y = step_header(1, "更新 Git 中的「上品系统」项目", y)
y = bullet(MARGIN + 10, y, "打开 GitHub Desktop，确认 Current Repository 是 shangpin_system，分支为 main。") + 16
y = bullet(MARGIN + 10, y, "点击 Fetch origin / Pull origin，拉取最新规则、工作台程序和共享业务数据。") + 26
y = screenshot(SCREEN_GIT, y, max_width=920, caption="确认仓库与分支后，再开始当天的上品工作。") + 50

y = step_header(2, "进入 Codex 后，先发送第一条指令", y)
y = text_block(MARGIN, y, "进入 Codex 的「上品系统」项目，第一条指令输入：", F_BODY, MUTED) + 18
y = code_box(
    y,
    "我在 Git 中更新了上品系统项目，请重新读取一下项目规则。",
) + 24
y = screenshot(
    SCREEN_CODEX_1,
    y,
    max_width=CONTENT_W,
    crop=(70, 35, 1600, 1230),
    caption="先让 Codex 重新读取 Git 更新后的项目规则，再明确启用批量快速上品路线。",
) + 24
y = step_header(3, "确认读取完成，再发送第二条指令", y)
y = text_block(MARGIN, y, "看到 Codex 确认已读取最新规则后，再输入：", F_BODY, MUTED) + 18
y = code_box(
    y,
    "好了，这是默认路线。我要使用新增的批量快速上品路线，并把工作台发给我。",
) + 24
y = text_block(
    MARGIN,
    y,
    "Codex 会启动工作台并给出“网页预览”。点击「打开方式」→「ChatGPT」，推荐使用 Codex 内置浏览器打开。",
    F_BODY_BOLD,
    INK,
) + 24

# Side-by-side crops: preview link and Open With menu.
left = Image.open(SCREEN_CODEX_2).convert("RGB").crop((80, 500, 1590, 1135))
right = Image.open(SCREEN_OPEN_WITH).convert("RGB").crop((235, 15, 680, 580))
left.thumbnail((680, 420), Image.Resampling.LANCZOS)
right.thumbnail((350, 420), Image.Resampling.LANCZOS)
panel_h = max(left.height, right.height) + 36
rounded_box(MARGIN, y, CONTENT_W, panel_h, fill=WHITE, outline=LINE, radius=28, shadow=True)
canvas.paste(left, (MARGIN + 20, y + 18))
canvas.paste(right, (MARGIN + CONTENT_W - right.width - 20, y + 18))
y += panel_h + 25
y = text_block(MARGIN, y, "这样可以左边保留 Codex 对话，右边显示工作台，沟通和文件同步都更方便。", F_BODY_BOLD, BLUE_DARK) + 48

y = screenshot(SCREEN_WORKBENCH, y, max_width=CONTENT_W, caption="推荐布局：左侧对话下指令，右侧工作台看进度与下载文件。") + 54

y = step_header(4, "准备要生成的 ASIN 与原始模板", y)
y = text_block(
    MARGIN,
    y,
    "假设本次要生成当前批次前 5 个 ASIN 的上传表格：",
    F_BODY_BOLD,
    INK,
) + 20
for item in (
    "在工作台中找到前 5 个 ASIN，逐个点击打开商品链接或竞品 HTML。",
    "复制商品标题，到 Amazon 模板下载页面获取对应类目的原始上传模板。",
    "回到工作台，把每个模板上传到对应商品的「原始模板」栏。",
    "确认 5 个商品的原始模板都已显示文件名，再回到 Codex 对话。",
):
    y = bullet(MARGIN + 10, y, item) + 15
y += 6
y = code_box(y, "前 5 个 ASIN 的原始模板已经上传好，可以开始填写表格了。") + 42

rounded_box(MARGIN, y, CONTENT_W, 292, fill=PALE_BLUE, outline="#C8D9FF", radius=28, shadow=False)
draw.text((MARGIN + 34, y + 28), "可选：同时告诉 Codex 你的 SKU 编写规则", font=F_SECTION, fill=BLUE_DARK)
sku_y = text_block(
    MARGIN + 34,
    y + 92,
    "例如：SKU 按 TTCA-产品名-变体属性；产品名控制在 2 个英文单词以内，整体尽量短。",
    F_BODY_BOLD,
    INK,
    max_width=CONTENT_W - 68,
)
text_block(
    MARGIN + 34,
    sku_y + 12,
    "不同店铺可以换成自己的固定前缀与格式。没有指定时，Codex 会按当前项目规则生成。",
    F_BODY,
    MUTED,
    max_width=CONTENT_W - 68,
)
y += 340

y = step_header(5, "等待 Codex 生成 V1，并在工作台下载", y)
y = bullet(MARGIN + 10, y, "Codex 会读取竞品页面与原始模板，按快速上品路线批量填表并执行本地自检。") + 15
y = bullet(MARGIN + 10, y, "生成完成后，文件会自动出现在工作台的「当前输出文档」栏，无需手动上传输出文件。") + 15
y = bullet(MARGIN + 10, y, "逐个下载，或使用顶部「批量下载输出」一次打包当前批次的最新版本。") + 24
rounded_box(MARGIN, y, CONTENT_W, 118, fill=NAVY, radius=25, shadow=False)
draw.text((MARGIN + 34, y + 28), "V1 = 首次生成版本", font=F_BODY_BOLD, fill="#72E0C2")
draw.text((MARGIN + 330, y + 28), "V2 / V3 = 根据 Amazon 报错修正后的版本", font=F_BODY_BOLD, fill=WHITE)
draw.text((MARGIN + 34, y + 72), "工作台始终把最高版本设为当前输出；批量 ZIP 只包含每款商品的最新版。", font=F_SMALL, fill="#C7D5EA")
y += 168

y = step_header(6, "上传 Amazon；有报错就回到对话处理", y)
y = bullet(MARGIN + 10, y, "下载 V1，进入 Amazon 后台上传。") + 14
y = bullet(MARGIN + 10, y, "上传成功：把工作台状态改为「已上传」。") + 14
y = bullet(MARGIN + 10, y, "出现报错：把状态改为「需修正」，并把 processing summary / 报错报告发回 Codex 对话。") + 20
y = code_box(y, "ASIN B0XXXXXXXX 上传报错，这是后台报错报告，请按报告修改并生成 V2。") + 22
y = text_block(
    MARGIN,
    y,
    "Codex 修改后会生成 V2，并自动同步到工作台。直接下载 V2 重新上传即可；极少数仍有问题的商品，再按同样方式生成 V3。",
    F_BODY_BOLD,
    BLUE_DARK,
) + 18
y = text_block(MARGIN, y, "注意：不需要把修正版手动上传回工作台。", F_BODY_BOLD, "#C64A42") + 54

# Final summary
rounded_box(MARGIN, y, CONTENT_W, 330, fill=NAVY, radius=34, shadow=True)
draw.text((MARGIN + 42, y + 36), "一句话记住", font=F_SMALL, fill="#72E0C2")
draw.text((MARGIN + 42, y + 88), "右边工作台记文件，左边对话让 Codex 干活。", font=F_SECTION, fill=WHITE)
draw.line((MARGIN + 42, y + 160, MARGIN + CONTENT_W - 42, y + 160), fill="#2D4262", width=2)
text_block(
    MARGIN + 42,
    y + 192,
    "更新 Git → 打开工作台 → 上传原始模板 → 告诉 Codex 开始 → 下载 V1 → 报错改 V2 → 成功后标记已上传",
    F_BODY_BOLD,
    "#DDE8F7",
    max_width=CONTENT_W - 84,
)
y += 390

draw.text((MARGIN, y), "批量快速上品路线 · 团队内部使用", font=F_TINY, fill="#8794A2")
draw.text((W - MARGIN - 150, y), "2026.09", font=F_TINY, fill="#8794A2")
y += 72

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.crop((0, 0, W, y)).save(OUTPUT, optimize=True)
print(OUTPUT)
print(f"{W}x{y}")
