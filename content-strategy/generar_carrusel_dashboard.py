from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent / "carrusel_dashboard_3senales"
OUT.mkdir(exist_ok=True)

W, H = 1080, 1350
BLACK = (0, 0, 0)
NEAR_BLACK = (10, 9, 7)
TEXT = (255, 255, 255)
MUTED = (140, 140, 140)
GOLD = (201, 168, 76)
GOLD_DIM = (110, 92, 42)

FONTS = Path("C:/Windows/Fonts")
f_black = lambda size: ImageFont.truetype(str(FONTS / "segoeuib.ttf"), size)
f_reg = lambda size: ImageFont.truetype(str(FONTS / "segoeui.ttf"), size)
f_light = lambda size: ImageFont.truetype(str(FONTS / "segoeuil.ttf"), size)

MARGIN = 88


def wrap_runs(draw, runs, font, max_width):
    """runs: list of (word, color). Returns list of lines, each a list of (word, color)."""
    lines, cur, cur_w = [], [], 0
    space_w = draw.textlength(" ", font=font)
    for word, color in runs:
        ww = draw.textlength(word, font=font)
        added = ww if not cur else space_w + ww
        if cur and cur_w + added > max_width:
            lines.append(cur)
            cur, cur_w = [(word, color)], ww
        else:
            cur.append((word, color))
            cur_w += added
    if cur:
        lines.append(cur)
    return lines


def draw_runs_line(draw, x, y, line, font):
    cx = x
    space_w = draw.textlength(" ", font=font)
    for word, color in line:
        draw.text((cx, y), word, font=font, fill=color)
        cx += draw.textlength(word, font=font) + space_w


def make_bg():
    """Vertical near-black gradient + soft warm glow behind the upper-left content."""
    top = np.array(NEAR_BLACK, dtype=np.float32)
    bottom = np.array(BLACK, dtype=np.float32)
    ramp = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    grad = top[None, :] * (1 - ramp[:, None, 0][:, :, None]) + bottom[None, :] * ramp[:, None, 0][:, :, None]
    arr = np.repeat(grad, W, axis=1).astype(np.uint8)
    img = Image.fromarray(arr, mode="RGB")

    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.35, -H * 0.25, W * 1.35, H * 0.55], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    gold_layer = Image.new("RGB", (W, H), GOLD)
    img = Image.composite(gold_layer, img, glow.point(lambda p: int(p * 0.22)))

    grain = (np.random.rand(H, W) * 6 - 3).astype(np.int16)
    arr2 = np.array(img).astype(np.int16)
    arr2 += grain[:, :, None]
    arr2 = np.clip(arr2, 0, 255).astype(np.uint8)
    return Image.fromarray(arr2, mode="RGB")


def ghost_number(img, text, cx, cy, size):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    font = f_black(size)
    bbox = ld.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ld.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=font, fill=(255, 255, 255, 18))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def ghost_check(img, x, y, s):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.line([x, y + s * 0.55, x + s * 0.38, y + s * 0.9, x + s, y + s * 0.15],
             fill=(255, 255, 255, 22), width=int(s * 0.09), joint="curve")
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def eyebrow(d, label):
    d.rectangle([(MARGIN, 118), (MARGIN + 56, 123)], fill=GOLD)
    d.text((MARGIN, 140), label, font=f_black(23), fill=GOLD)


def footer(d, index, accent_word):
    d.line([(MARGIN, H - 100), (W - MARGIN, H - 100)], fill=(255, 255, 255, 25), width=1)
    d.ellipse([(MARGIN, H - 78), (MARGIN + 8, H - 70)], fill=GOLD)
    d.text((MARGIN + 20, H - 84), "DATOSGT", font=f_black(21), fill=(220, 220, 220))
    tag = f"{index} / 3"
    tw = d.textlength(tag, font=f_reg(21))
    d.text((W - MARGIN - tw, H - 84), tag, font=f_reg(21), fill=MUTED)


def icon_clock(d, x, y, s, color):
    d.ellipse([x, y, x + s, y + s], outline=color, width=6)
    cx, cy = x + s / 2, y + s / 2
    d.line([cx, cy, cx, cy - s * 0.32], fill=color, width=6)
    d.line([cx, cy, cx + s * 0.22, cy], fill=color, width=6)


def icon_warning(d, x, y, s, color):
    d.polygon([(x + s / 2, y), (x, y + s), (x + s, y + s)], outline=color, width=6)
    d.line([x + s / 2, y + s * 0.38, x + s / 2, y + s * 0.68], fill=color, width=6)
    d.ellipse([x + s / 2 - 4, y + s * 0.78, x + s / 2 + 4, y + s * 0.78 + 8], fill=color)


def icon_layers(d, x, y, s, color):
    w, h = s, s * 0.4
    for i, off in enumerate([0, s * 0.28, s * 0.56]):
        pts = [(x, y + off + h / 2), (x + w / 2, y + off), (x + w, y + off + h / 2), (x + w / 2, y + off + h)]
        d.polygon(pts, outline=color, width=5)


def icon_check(d, x, y, s, color, width=14):
    d.line([x, y + s * 0.55, x + s * 0.38, y + s * 0.9, x + s, y + s * 0.15], fill=color, width=width, joint="curve")


def icon_download(d, cx, cy, s, color):
    d.line([cx, cy - s * 0.5, cx, cy + s * 0.15], fill=color, width=6)
    d.line([cx - s * 0.3, cy - s * 0.1, cx, cy + s * 0.15, cx + s * 0.3, cy - s * 0.1], fill=color, width=6, joint="curve")
    d.line([cx - s * 0.45, cy + s * 0.5, cx + s * 0.45, cy + s * 0.5], fill=color, width=6)


# ── SLIDE 1 — PORTADA ──
img = make_bg()
ghost_number(img, "01", W - 240, H - 210, 460)
d = ImageDraw.Draw(img)
eyebrow(d, "TU NEGOCIO Y TUS NÚMEROS")

runs = [(w, TEXT) for w in "3 señales de que tu negocio necesita un".split()] + [("dashboard", GOLD)]
lines = wrap_runs(d, runs, f_black(82), W - 2 * MARGIN)
y = 250
for ln in lines:
    draw_runs_line(d, MARGIN, y, ln, f_black(82))
    y += 92

y += 22
d.text((MARGIN, y), "(y ya no un Excel manual)", font=f_light(38), fill=MUTED)

# small icon row as visual anchor
icon_y = y + 130
icon_clock(d, MARGIN, icon_y, 46, GOLD_DIM)
icon_warning(d, MARGIN + 80, icon_y, 46, GOLD_DIM)
icon_layers(d, MARGIN + 160, icon_y, 46, GOLD_DIM)

footer(d, 1, "dashboard")
img.save(OUT / "slide_1_portada.png")

# ── SLIDE 2 — CUERPO ──
img = make_bg()
ghost_number(img, "3", W - 250, 120, 640)
d = ImageDraw.Draw(img)
eyebrow(d, "LAS 3 SEÑALES")

points = [
    (icon_clock, [("Actualizas", GOLD), ("el", TEXT), ("mismo", TEXT), ("reporte", TEXT), ("a", TEXT), ("mano", TEXT), ("cada", TEXT), ("semana.", TEXT)]),
    (icon_warning, [("Te", TEXT), ("enteras", TEXT), ("de", TEXT), ("un", TEXT), ("problema", GOLD), ("semanas", TEXT), ("después.", TEXT)]),
    (icon_layers, [("Tu", TEXT), ("Excel", GOLD), ("ya", TEXT), ("tiene", TEXT), ("tantas", TEXT), ("pestañas", TEXT), ("que", TEXT), ("ni", TEXT), ("tú", TEXT), ("lo", TEXT), ("entiendes.", TEXT)]),
]

y = 250
icon_s = 58
text_x = MARGIN + icon_s + 34
text_w = W - MARGIN - text_x
for icon_fn, runs in points:
    icon_fn(d, MARGIN, y + 6, icon_s, GOLD)
    lines = wrap_runs(d, runs, f_reg(44), text_w)
    ty = y
    for ln in lines:
        draw_runs_line(d, text_x, ty, ln, f_reg(44))
        ty += 56
    y = max(y + icon_s + 20, ty) + 46
    d.line([(MARGIN, y - 24), (W - MARGIN, y - 24)], fill=(255, 255, 255, 15), width=1)

footer(d, 2, "")
img.save(OUT / "slide_2_cuerpo.png")

# ── SLIDE 3 — CIERRE ──
img = make_bg()
ghost_check(img, W - 420, H - 560, 340)
d = ImageDraw.Draw(img)
eyebrow(d, "¿TE IDENTIFICASTE?")

runs = [("Si", TEXT), ("marcaste", TEXT), ("1", GOLD), ("o", TEXT), ("más,", TEXT), ("ya", TEXT), ("es", TEXT), ("momento.", GOLD)]
lines = wrap_runs(d, runs, f_black(74), W - 2 * MARGIN)
y = 250
for ln in lines:
    draw_runs_line(d, MARGIN, y, ln, f_black(74))
    y += 86

y += 28
cta = "Guarda este carrusel y escríbeme si quieres ver cómo se vería el tuyo."
lines2 = wrap_runs(d, [(w, MUTED) for w in cta.split()], f_reg(36), W - 2 * MARGIN)
for ln in lines2:
    draw_runs_line(d, MARGIN, y, ln, f_reg(36))
    y += 46

# CTA badge
badge_y = y + 60
badge_w = 280
d.rounded_rectangle([MARGIN, badge_y, MARGIN + badge_w, badge_y + 76], radius=38, fill=GOLD)
btxt = "Guardar"
btw = d.textlength(btxt, font=f_black(28))
icon_download(d, MARGIN + badge_w - 46, badge_y + 38, 34, (10, 10, 10))
d.text((MARGIN + (badge_w - 34) / 2 - btw / 2, badge_y + 24), btxt, font=f_black(28), fill=(10, 10, 10))

footer(d, 3, "")
img.save(OUT / "slide_3_cierre.png")

print("Listo:", [p.name for p in OUT.glob("*.png")])
