from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from charts import chart_facturado_vs_real, chart_margen_por_producto, chart_antes_despues, chart_pestanas_inconsistentes

OUT = Path(__file__).resolve().parent / "carrusel_historia_q42000"
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
TOTAL = 5


def wrap_runs(draw, runs, font, max_width):
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


def runs_from(text, default=TEXT, gold_words=()):
    gold_set = {w.strip(",.").lower() for w in gold_words}
    return [(w, GOLD if w.strip(",.").lower() in gold_set else default) for w in text.split()]


def make_bg(seed):
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

    rng = np.random.default_rng(seed)
    grain = (rng.random((H, W)) * 6 - 3).astype(np.int16)
    arr2 = np.array(img).astype(np.int16)
    arr2 += grain[:, :, None]
    arr2 = np.clip(arr2, 0, 255).astype(np.uint8)
    return Image.fromarray(arr2, mode="RGB")


def ghost_text(img, text, cx, cy, size, alpha=18):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    font = f_black(size)
    bbox = ld.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ld.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=font, fill=(255, 255, 255, alpha))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def eyebrow(d, label):
    d.rectangle([(MARGIN, 118), (MARGIN + 56, 123)], fill=GOLD)
    d.text((MARGIN, 140), label, font=f_black(23), fill=GOLD)


def footer(d, index):
    d.line([(MARGIN, H - 100), (W - MARGIN, H - 100)], fill=(255, 255, 255, 25), width=1)
    d.ellipse([(MARGIN, H - 78), (MARGIN + 8, H - 70)], fill=GOLD)
    d.text((MARGIN + 20, H - 84), "DATOSGT", font=f_black(21), fill=(220, 220, 220))
    tag = f"{index} / {TOTAL}"
    tw = d.textlength(tag, font=f_reg(21))
    d.text((W - MARGIN - tw, H - 84), tag, font=f_reg(21), fill=MUTED)


def icon_warning(d, x, y, s, color):
    d.polygon([(x + s / 2, y), (x, y + s), (x + s, y + s)], outline=color, width=6)
    d.line([x + s / 2, y + s * 0.38, x + s / 2, y + s * 0.68], fill=color, width=6)
    d.ellipse([x + s / 2 - 4, y + s * 0.78, x + s / 2 + 4, y + s * 0.78 + 8], fill=color)


def icon_layers(d, x, y, s, color):
    w, h = s, s * 0.4
    for off in [0, s * 0.28, s * 0.56]:
        pts = [(x, y + off + h / 2), (x + w / 2, y + off), (x + w, y + off + h / 2), (x + w / 2, y + off + h)]
        d.polygon(pts, outline=color, width=5)


def icon_check(d, x, y, s, color, width=14):
    d.line([x, y + s * 0.55, x + s * 0.38, y + s * 0.9, x + s, y + s * 0.15], fill=color, width=width, joint="curve")


def icon_download(d, cx, cy, s, color):
    d.line([cx, cy - s * 0.5, cx, cy + s * 0.15], fill=color, width=6)
    d.line([cx - s * 0.3, cy - s * 0.1, cx, cy + s * 0.15, cx + s * 0.3, cy - s * 0.1], fill=color, width=6, joint="curve")
    d.line([cx - s * 0.45, cy + s * 0.5, cx + s * 0.45, cy + s * 0.5], fill=color, width=6)


def headline_block(d, y, runs, font, max_w=W - 2 * MARGIN):
    lines = wrap_runs(d, runs, font, max_w)
    for ln in lines:
        draw_runs_line(d, MARGIN, y, ln, font)
        y += int(font.size * 1.14)
    return y


def body_block(d, y, text, font=None, color=MUTED, max_w=W - 2 * MARGIN, leading=1.28):
    font = font or f_reg(38)
    lines = wrap_runs(d, [(w, color) for w in text.split()], font, max_w)
    for ln in lines:
        draw_runs_line(d, MARGIN, y, ln, font)
        y += int(font.size * leading)
    return y


def paste_chart(img, chart_rgba, x, y):
    img.paste(chart_rgba, (x, y), chart_rgba)


CHART_TOP = 800
CHART_BOTTOM = H - 130
CHART_W = W - 2 * MARGIN


# ── SLIDE 1 — BEFORE ──
img = make_bg(1)
d = ImageDraw.Draw(img)
eyebrow(d, "MARZO · EL MEJOR MES DEL AÑO (EN PAPEL)")
y = body_block(d, 250, "Q42,000", font=f_black(120), color=GOLD, leading=1.0)
y += 24
y = body_block(d, y, "en ventas. Pero en la cuenta del negocio no había ni la mitad de eso.", font=f_reg(42), color=TEXT)
y += 10
body_block(d, y, "Algo no cuadraba, y nadie sabía qué.", font=f_reg(42), color=MUTED)

chart1 = chart_facturado_vs_real(CHART_W, CHART_BOTTOM - CHART_TOP)
paste_chart(img, chart1, MARGIN, CHART_TOP + (CHART_BOTTOM - CHART_TOP - chart1.height) // 2)

footer(d, 1)
img.save(OUT / "slide_1_before.png")

# ── SLIDE 2 — TENSION ──
img = make_bg(2)
d = ImageDraw.Draw(img)
eyebrow(d, "LA BÚSQUEDA")
icon_layers(d, MARGIN, 250, 64, GOLD)
y = 340
y = headline_block(d, y, runs_from("14 pestañas de Excel.", gold_words=["14"]), f_black(64))
y += 26
y = body_block(d, y, "Cada una con una versión distinta del mismo número.", font=f_reg(40), color=TEXT)
y += 10
body_block(d, y, "3 meses decidiendo “a ojo” porque sacar un reporte real tomaba un día entero.", font=f_reg(40), color=MUTED)

chart2 = chart_pestanas_inconsistentes(CHART_W, CHART_BOTTOM - CHART_TOP)
paste_chart(img, chart2, MARGIN, CHART_TOP + (CHART_BOTTOM - CHART_TOP - chart2.height) // 2)

footer(d, 2)
img.save(OUT / "slide_2_tension.png")

# ── SLIDE 3 — BRIDGE (EL HALLAZGO) ──
img = make_bg(3)
d = ImageDraw.Draw(img)
eyebrow(d, "EL HALLAZGO")
icon_warning(d, MARGIN, 250, 64, GOLD)
y = 340
y = headline_block(d, y, runs_from("3 productos se vendían por debajo del costo.", gold_words=["3", "costo."]), f_black(56))
y += 26
y = body_block(d, y, "Un dashboard cruzando ventas, costos y descuentos por producto lo dejó ver.", font=f_reg(40), color=TEXT)
y += 10
body_block(d, y, "Error de hace 6 meses en la lista de precios que nadie había notado.", font=f_reg(40), color=MUTED)

chart3 = chart_margen_por_producto(CHART_W, CHART_BOTTOM - CHART_TOP)
paste_chart(img, chart3, MARGIN, CHART_TOP + (CHART_BOTTOM - CHART_TOP - chart3.height) // 2)

footer(d, 3)
img.save(OUT / "slide_3_bridge.png")

# ── SLIDE 4 — AFTER ──
img = make_bg(4)
d = ImageDraw.Draw(img)
eyebrow(d, "8 SEMANAS DESPUÉS")
icon_check(d, MARGIN, 250, 60, GOLD, width=10)
y = 340
y = headline_block(d, y, runs_from("Margen recuperado.", gold_words=["recuperado."]), f_black(72))
y += 30
y = body_block(d, y, "No necesitaban vender más.", font=f_reg(42), color=TEXT)
y += 6
body_block(d, y, "Necesitaban ver lo que ya tenían enfrente.", font=f_reg(42), color=MUTED)

chart4 = chart_antes_despues(CHART_W, CHART_BOTTOM - CHART_TOP)
paste_chart(img, chart4, MARGIN, CHART_TOP + (CHART_BOTTOM - CHART_TOP - chart4.height) // 2)

footer(d, 4)
img.save(OUT / "slide_4_after.png")

# ── SLIDE 5 — CTA ──
img = make_bg(5)
d = ImageDraw.Draw(img)
eyebrow(d, "¿TE SUENA FAMILIAR?")
y = headline_block(d, 250, runs_from("Encuentra lo que tus números ya te están diciendo.", gold_words=["números"]), f_black(60))
y += 26
y = body_block(d, y, "Antes de que te cueste más.", font=f_reg(38), color=MUTED)
y += 10
y = body_block(d, y, "¿Te ha pasado algo parecido? Cuéntame en los comentarios.", font=f_reg(38), color=MUTED)

badge_y = y + 50
badge_w = 280
d.rounded_rectangle([MARGIN, badge_y, MARGIN + badge_w, badge_y + 76], radius=38, fill=GOLD)
btxt = "Guardar"
btw = d.textlength(btxt, font=f_black(28))
icon_download(d, MARGIN + badge_w - 46, badge_y + 38, 34, (10, 10, 10))
d.text((MARGIN + (badge_w - 34) / 2 - btw / 2, badge_y + 24), btxt, font=f_black(28), fill=(10, 10, 10))

# recap de la historia en 3 cifras
recap_y = badge_y + 150
d.line([(MARGIN, recap_y - 40), (W - MARGIN, recap_y - 40)], fill=(255, 255, 255, 25), width=1)
d.text((MARGIN, recap_y - 26), "LA HISTORIA EN 3 CIFRAS", font=f_black(20), fill=GOLD)

stats = [("Q42,000", "facturados"), ("3", "productos con pérdida"), ("8", "semanas para corregirlo")]
col_w = (W - 2 * MARGIN) / 3
for i, (num, label) in enumerate(stats):
    x = MARGIN + i * col_w
    d.text((x, recap_y + 20), num, font=f_black(46), fill=TEXT)
    lines = wrap_runs(d, [(w, MUTED) for w in label.split()], f_reg(24), col_w - 20)
    ly = recap_y + 90
    for ln in lines:
        draw_runs_line(d, x, ly, ln, f_reg(24))
        ly += 30

disclaimer = "* Caso ilustrativo (compuesto), no un cliente real todavía."
d.text((MARGIN, H - 150), disclaimer, font=f_light(22), fill=(90, 90, 90))

footer(d, 5)
img.save(OUT / "slide_5_cta.png")

print("Listo:", sorted(p.name for p in OUT.glob("*.png")))
