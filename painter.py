import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))


def download_image(url, save_path):
    """下载网络图片并保存到本地（兼容无 requests 环境）。"""
    try:
        import requests

        r = requests.get(url, timeout=10)
        if r.status_code == 0:
            return False
        with open(save_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"下载图片失败: {e}")
        return False


def wrap_text(text, font, max_width):
    """按像素宽度自动换行。"""
    lines = []
    for raw_line in text.split("\n"):
        line = ""
        for char in raw_line:
            test = line + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width and line:
                lines.append(line)
                line = char
            else:
                line = test
        lines.append(line)
    return lines


def combine(
    jrys_data: dict,
    user_id: str,
    fl: int,
    avatar_path: str = None,
    bg_folder: str = None,
    bg_name: str = None,
    font_path: str = None,
) -> str:
    """
    生成今日运势卡片图片，返回图片路径。
    jrys_data: 含 star(等级1-5)、title、text、lucky、lucky_color、lucky_num、avoid
    """
    if bg_folder is None:
        bg_folder = os.path.join(ROOT, "backgroundFolder")
    if font_path is None:
        font_path = os.path.join(ROOT, "font", "MiSans-Medium.ttf")

    bg_files = [f for f in os.listdir(bg_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not bg_files:
        raise FileNotFoundError(f"背景图目录为空: {bg_folder}")
    bg = bg_name if bg_name else random.choice(bg_files)
    bg_path = os.path.join(bg_folder, bg)

    img = Image.open(bg_path).convert("RGBA")
    W, H = img.size

    draw = ImageDraw.Draw(img)

    # 字体
    title_font = ImageFont.truetype(font_path, int(H * 0.045))
    text_font = ImageFont.truetype(font_path, int(H * 0.03))
    small_font = ImageFont.truetype(font_path, int(H * 0.025))
    num_font = ImageFont.truetype(font_path, int(H * 0.02))

    # 头像圆形裁剪
    if avatar_path and os.path.exists(avatar_path):
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize((int(W * 0.14), int(W * 0.14)))
        mask = Image.new("L", avatar.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, *avatar.size), fill=255)
        avatar.putalpha(mask)
        ax = int(W * 0.06)
        ay = int(H * 0.06)
        img.paste(avatar, (ax, ay), avatar)

    # 文本区域
    tx = int(W * 0.24)
    ty = int(H * 0.065)
    line_gap = int(H * 0.05)

    # 用户ID + 运气值
    draw.text((tx, ty), f"用户 {user_id}", font=title_font, fill=(255, 255, 255, 255))
    draw.text((tx, ty + line_gap), f"今日运气: {fl}", font=text_font, fill=(255, 215, 0, 255))

    # 星级
    star = int(jrys_data.get("star", 3))
    star_str = "★" * star + "☆" * (5 - star)
    draw.text((tx, ty + line_gap * 2), star_str, font=text_font, fill=(255, 215, 0, 255))

    # 标题
    draw.text((tx, ty + line_gap * 3), jrys_data.get("title", ""), font=text_font, fill=(255, 255, 255, 255))

    # 正文（换行）
    body = jrys_data.get("text", "")
    body_lines = wrap_text(body, text_font, int(W * 0.7))
    by = ty + line_gap * 4
    for ln in body_lines:
        draw.text((tx, by), ln, font=text_font, fill=(230, 230, 230, 255))
        by += int(H * 0.038)

    # 幸运信息
    info_y = by + int(H * 0.02)
    draw.text((tx, info_y), f"幸运方位: {jrys_data.get('lucky', '')}", font=small_font, fill=(255, 255, 255, 255))
    draw.text(
        (tx, info_y + int(H * 0.035)),
        f"幸运颜色: {jrys_data.get('lucky_color', '')}",
        font=small_font,
        fill=(255, 255, 255, 255),
    )
    draw.text(
        (tx, info_y + int(H * 0.07)),
        f"幸运数字: {jrys_data.get('lucky_num', '')}",
        font=small_font,
        fill=(255, 255, 255, 255),
    )
    draw.text(
        (tx, info_y + int(H * 0.105)),
        f"幸运禁忌: {jrys_data.get('avoid', '')}",
        font=small_font,
        fill=(255, 255, 255, 255),
    )

    out_path = os.path.join(ROOT, "jrys_cache.png")
    img.convert("RGB").save(out_path, "PNG")
    return out_path
