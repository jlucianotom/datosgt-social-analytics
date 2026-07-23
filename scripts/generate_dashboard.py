import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Orden importa: se revisan de arriba a abajo y gana el primer match. Los
# pilares con senales mas especificas/raras van primero para que no los tape
# un pilar generico como B (que comparte vocabulario con casi todo).
PILLAR_KEYWORDS = {
    "F · Historia personal": ["primera vez", "orgullos", "patrocin", "vine a", "aniversario"],
    "G · IA/Tech": ["chatgpt", "openai", "gpt-", " ia ", "inteligencia artificial", "model context protocol", " mcp "],
    "D · Actualidad/deportes": [" vs ", "mundial", "eurocopa", "seleccion", "partido"],
    "A · Habilidad/Carrera": ["python", "sql", "excel", "power bi", "aprend", "curso", "habilidad", "carrera"],
    "B · Datos de negocio": ["margen", "precio", "kpi", "cliente", "venta", "costo", "negocio", "rentab"],
}


def classify(text):
    t = (text or "").lower()
    for pillar, kws in PILLAR_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return pillar
    return "Otro / sin clasificar"


def load_posts():
    path = ROOT / "data" / "instagram_posts.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("posts", [])


def row(p):
    ins = p.get("insights", {})
    reach = ins.get("reach", 0)
    views = ins.get("views", 0)
    likes = ins.get("likes", p.get("like_count") or 0)
    comments = ins.get("comments", p.get("comments_count") or 0)
    saves = ins.get("saved", 0)
    shares = ins.get("shares", 0)
    total = ins.get("total_interactions", likes + comments + saves + shares)
    text = p.get("caption") or ""
    return {
        "id": p["id"],
        "text": text,
        "url": p.get("permalink"),
        "ts": p.get("timestamp"),
        "type": p.get("media_product_type") or p.get("media_type") or "OTHER",
        "pillar": classify(text),
        "reach": reach,
        "er": (total / reach) if reach else 0,
        "likes": likes,
        "comments": comments,
        "saves": saves,
        "shares": shares,
    }


def month_key(ts):
    return ts[:7]  # YYYY-MM


def build_dashboard():
    posts = load_posts()
    rows = [row(p) for p in posts if p.get("timestamp")]
    solid = [r for r in rows if r["reach"] >= 30]

    now = datetime.now()
    last30 = [r for r in solid if r["ts"] >= (now - timedelta(days=30)).isoformat()]
    last90 = [r for r in solid if r["ts"] >= (now - timedelta(days=90)).isoformat()]

    avg_er_30 = statistics.mean([r["er"] for r in last30]) if last30 else 0
    avg_er_90 = statistics.mean([r["er"] for r in last90]) if last90 else 0
    avg_er_all = statistics.mean([r["er"] for r in solid]) if solid else 0

    by_pillar = {}
    for r in solid:
        by_pillar.setdefault(r["pillar"], []).append(r["er"])
    pillar_stats = sorted(
        [(k, statistics.mean(v), len(v)) for k, v in by_pillar.items()],
        key=lambda x: x[1], reverse=True,
    )
    # "Otro / sin clasificar" se muestra en la grafica para transparencia, pero
    # nunca se usa para la recomendacion — no es un pilar accionable.
    classified_pillar_stats = [p for p in pillar_stats if p[0] != "Otro / sin clasificar"]

    by_type = {}
    for r in solid:
        by_type.setdefault(r["type"], []).append(r["er"])
    type_stats = sorted(
        [(k, statistics.mean(v), len(v)) for k, v in by_type.items()],
        key=lambda x: x[1], reverse=True,
    )

    months = {}
    for r in solid:
        months.setdefault(month_key(r["ts"]), []).append(r["er"])
    month_series = sorted(months.items())[-12:]
    month_points = [(m, statistics.mean(v)) for m, v in month_series]

    top5 = sorted(solid, key=lambda r: r["er"], reverse=True)[:5]
    bottom5 = sorted(solid, key=lambda r: r["er"])[:5]

    hours = {}
    for r in solid:
        h = datetime.fromisoformat(r["ts"].replace("Z", "+00:00")).hour
        hours.setdefault(h, []).append(r["er"])
    best_hours = sorted(
        [(h, statistics.mean(v)) for h, v in hours.items()], key=lambda x: x[1], reverse=True
    )[:3]

    best_pillar = classified_pillar_stats[0] if classified_pillar_stats else ("N/A", 0, 0)
    worst_pillar = min(classified_pillar_stats, key=lambda x: x[1]) if classified_pillar_stats else ("N/A", 0, 0)

    trend_delta = avg_er_30 - avg_er_90
    trend_label = "subiendo" if trend_delta > 0.002 else "bajando" if trend_delta < -0.002 else "estable"

    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "total_posts": len(rows),
        "avg_er_30": avg_er_30,
        "avg_er_90": avg_er_90,
        "avg_er_all": avg_er_all,
        "trend_label": trend_label,
        "trend_delta": trend_delta,
        "pillar_stats": pillar_stats,
        "type_stats": type_stats,
        "month_points": month_points,
        "top5": top5,
        "bottom5": bottom5,
        "best_hours": best_hours,
        "best_pillar": best_pillar,
        "worst_pillar": worst_pillar,
        "posts_last_30": len(last30),
    }


def bar_chart_svg(data, width=640, bar_h=34, gap=14, accent="#c9a84c", max_val=None):
    if not data:
        return "<p class='empty'>Sin datos suficientes todavia.</p>"
    max_val = max_val or max(v for _, v, *_ in data) or 1
    label_w = 190
    chart_w = width - label_w - 60
    rows_svg = []
    y = 0
    for item in data:
        name, val = item[0], item[1]
        n = item[2] if len(item) > 2 else None
        w = max(4, (val / max_val) * chart_w)
        pct = f"{val*100:.1f}%"
        rows_svg.append(f'''
        <g transform="translate(0,{y})" class="bar-row">
          <text x="{label_w - 12}" y="{bar_h/2}" text-anchor="end" dominant-baseline="middle" class="bar-label">{name}</text>
          <rect x="{label_w}" y="{bar_h*0.22}" width="{chart_w}" height="{bar_h*0.56}" rx="4" class="bar-track"/>
          <rect x="{label_w}" y="{bar_h*0.22}" width="{w}" height="{bar_h*0.56}" rx="4" fill="{accent}" class="bar-fill">
            <title>{name}: {pct}{f" (n={n})" if n else ""}</title>
          </rect>
          <text x="{label_w + w + 10}" y="{bar_h/2}" dominant-baseline="middle" class="bar-value">{pct}</text>
        </g>''')
        y += bar_h + gap
    total_h = y
    return f'<svg viewBox="0 0 {width} {total_h}" class="bar-chart" role="img" aria-label="grafico de barras">{"".join(rows_svg)}</svg>'


def line_chart_svg(points, width=680, height=220, accent="#c9a84c"):
    if len(points) < 2:
        return "<p class='empty'>Necesitas mas meses de datos para ver una tendencia.</p>"
    pad_l, pad_r, pad_t, pad_b = 50, 20, 20, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    vals = [v for _, v in points]
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        vmax = vmin + 0.01
    n = len(points)
    coords = []
    for i, (label, v) in enumerate(points):
        x = pad_l + (i / (n - 1)) * plot_w
        y = pad_t + (1 - (v - vmin) / (vmax - vmin)) * plot_h
        coords.append((x, y, label, v))

    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in coords)
    area_d = path_d + f" L {coords[-1][0]:.1f},{pad_t+plot_h} L {coords[0][0]:.1f},{pad_t+plot_h} Z"

    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{accent}" class="line-dot"><title>{lbl}: {v*100:.1f}%</title></circle>'
        for x, y, lbl, v in coords
    )
    labels = "".join(
        f'<text x="{x:.1f}" y="{height-8}" text-anchor="middle" class="axis-label">{lbl[5:]}</text>'
        for i, (x, y, lbl, v) in enumerate(coords) if i % max(1, n // 6) == 0
    )
    gridlines = "".join(
        f'<line x1="{pad_l}" y1="{pad_t + f*plot_h}" x2="{width-pad_r}" y2="{pad_t + f*plot_h}" class="gridline"/>'
        for f in (0, 0.5, 1)
    )

    return f'''<svg viewBox="0 0 {width} {height}" class="line-chart" role="img" aria-label="tendencia de engagement">
      {gridlines}
      <path d="{area_d}" class="line-area" fill="{accent}" opacity="0.12"/>
      <path d="{path_d}" fill="none" stroke="{accent}" stroke-width="2.5" class="line-path"/>
      {dots}
      {labels}
    </svg>'''


def post_card(r, kind):
    text = (r["text"] or "").replace(chr(10), " ")[:90]
    pct = f"{r['er']*100:.1f}%"
    cls = "good" if kind == "top" else "bad"
    return f'''<a href="{r['url']}" target="_blank" class="post-card {cls}">
      <div class="post-pct">{pct}</div>
      <div class="post-meta">{r['pillar']} · alcance {r['reach']}</div>
      <div class="post-text">{text}</div>
    </a>'''


def render_html(d):
    trend_arrow = {"subiendo": "&#8593;", "bajando": "&#8595;", "estable": "&#8594;"}[d["trend_label"]]
    trend_class = {"subiendo": "good", "bajando": "bad", "estable": "neutral"}[d["trend_label"]]

    pillar_bars = bar_chart_svg([(k, v, n) for k, v, n in d["pillar_stats"]])
    type_bars = bar_chart_svg([(k, v, n) for k, v, n in d["type_stats"]], accent="#8a8a8a")
    trend_line = line_chart_svg(d["month_points"])

    top_cards = "".join(post_card(r, "top") for r in d["top5"])
    bottom_cards = "".join(post_card(r, "bottom") for r in d["bottom5"])

    hours_txt = " · ".join(f"{h:02d}:00 ({v*100:.1f}%)" for h, v in d["best_hours"])

    recommendation = (
        f"Prioriza el pilar <strong>{d['best_pillar'][0]}</strong> "
        f"({d['best_pillar'][1]*100:.1f}% ER) y reduce o replantea "
        f"<strong>{d['worst_pillar'][0]}</strong> ({d['worst_pillar'][1]*100:.1f}% ER). "
        f"Publica cerca de las <strong>{d['best_hours'][0][0]:02d}:00</strong>."
        if d["pillar_stats"] else "Necesitas mas datos clasificados para una recomendacion certera."
    )

    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Dashboard DatosGT — Contenido</title>
<style>
  :root {{
    --bg: #000000; --bg2: #0d0d0c; --bg3: #161615;
    --border: rgba(255,255,255,.10); --text: #f5f4f1; --muted: #93918a;
    --accent: #c9a84c; --good: #4caf7d; --bad: #d9694f;
  }}
  :root[data-theme="light"] {{
    --bg: #faf9f6; --bg2: #f1efe9; --bg3: #e8e5dc;
    --border: rgba(0,0,0,.12); --text: #16150f; --muted: #6b6759;
    --accent: #a6842f; --good: #2f8f5c; --bad: #b8452e;
  }}
  @media (prefers-color-scheme: light) {{
    :root:not([data-theme="dark"]) {{
      --bg: #faf9f6; --bg2: #f1efe9; --bg3: #e8e5dc;
      --border: rgba(0,0,0,.12); --text: #16150f; --muted: #6b6759;
      --accent: #a6842f; --good: #2f8f5c; --bad: #b8452e;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,"Segoe UI",Arial,sans-serif; line-height:1.5; }}
  .wrap {{ max-width: 920px; margin: 0 auto; padding: 48px 24px 100px; }}
  .eyebrow {{ font-family: ui-monospace, Consolas, monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin:0 0 10px; }}
  h1 {{ font-size: clamp(1.6rem, 4vw, 2.2rem); font-weight:800; margin:0 0 6px; letter-spacing:-.01em; }}
  .subtitle {{ color: var(--muted); font-size:.9rem; margin: 0 0 32px; }}

  .stat-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:36px; }}
  .stat-tile {{ background:var(--bg2); border:1px solid var(--border); border-radius:10px; padding:18px 20px; }}
  .stat-tile .label {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:8px; }}
  .stat-tile .value {{ font-size:1.7rem; font-weight:800; font-variant-numeric: tabular-nums; }}
  .stat-tile .value.good {{ color: var(--good); }}
  .stat-tile .value.bad {{ color: var(--bad); }}
  .stat-tile .value.neutral {{ color: var(--text); }}
  .stat-tile .sub {{ font-size:.76rem; color:var(--muted); margin-top:4px; }}

  .rec-box {{ background: color-mix(in srgb, var(--accent) 12%, var(--bg2)); border:1px solid color-mix(in srgb, var(--accent) 45%, transparent); border-radius:10px; padding:18px 22px; margin-bottom:36px; font-size:.94rem; }}
  .rec-box .rl {{ font-family: ui-monospace, Consolas, monospace; font-size:.68rem; text-transform:uppercase; letter-spacing:.1em; color:var(--accent); display:block; margin-bottom:8px; }}

  section {{ margin-bottom:40px; }}
  h2 {{ font-size:1.05rem; font-weight:700; margin:0 0 4px; }}
  .section-sub {{ font-size:.82rem; color:var(--muted); margin:0 0 18px; }}

  .bar-chart, .line-chart {{ width:100%; height:auto; overflow: visible; }}
  .bar-label {{ font-size:12px; fill:var(--muted); }}
  .bar-value {{ font-size:12px; fill:var(--text); font-variant-numeric: tabular-nums; }}
  .bar-track {{ fill: var(--bg3); }}
  .bar-fill {{ transition: opacity .15s; }}
  .bar-row:hover .bar-fill {{ opacity:.85; }}
  .gridline {{ stroke: var(--border); stroke-width:1; }}
  .axis-label {{ font-size:11px; fill:var(--muted); }}
  .line-dot {{ cursor:pointer; }}
  .empty {{ color:var(--muted); font-size:.85rem; }}

  .card-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }}
  .post-card {{ display:block; background:var(--bg2); border:1px solid var(--border); border-left:3px solid var(--good); border-radius:0 8px 8px 0; padding:14px 16px; text-decoration:none; color:var(--text); }}
  .post-card.bad {{ border-left-color: var(--bad); }}
  .post-card .post-pct {{ font-size:1.2rem; font-weight:800; font-variant-numeric: tabular-nums; }}
  .post-card.good .post-pct {{ color: var(--good); }}
  .post-card.bad .post-pct {{ color: var(--bad); }}
  .post-card .post-meta {{ font-size:.72rem; color:var(--muted); margin: 4px 0 8px; }}
  .post-card .post-text {{ font-size:.84rem; opacity:.9; }}

  .hours-line {{ font-size:.9rem; color:var(--text); font-variant-numeric: tabular-nums; }}
  footer {{ color:var(--muted); font-family: ui-monospace, Consolas, monospace; font-size:.72rem; margin-top: 50px; }}
</style>
</head>
<body>
  <div class="wrap">
    <p class="eyebrow">DatosGT · Dashboard de contenido</p>
    <h1>Que subir y que mejorar</h1>
    <p class="subtitle">Actualizado automaticamente cada dia · {d['generated_at']} · {d['total_posts']} publicaciones analizadas</p>

    <div class="stat-row">
      <div class="stat-tile">
        <div class="label">Engagement 30 dias</div>
        <div class="value">{d['avg_er_30']*100:.1f}%</div>
        <div class="sub">{d['posts_last_30']} posts recientes</div>
      </div>
      <div class="stat-tile">
        <div class="label">Tendencia (30 vs 90 dias)</div>
        <div class="value {trend_class}">{trend_arrow} {d['trend_label']}</div>
        <div class="sub">{d['trend_delta']*100:+.1f} puntos</div>
      </div>
      <div class="stat-tile">
        <div class="label">Mejor pilar</div>
        <div class="value good" style="font-size:1.1rem">{d['best_pillar'][0]}</div>
        <div class="sub">{d['best_pillar'][1]*100:.1f}% ER</div>
      </div>
      <div class="stat-tile">
        <div class="label">Mejor horario</div>
        <div class="value neutral" style="font-size:1.3rem">{d['best_hours'][0][0]:02d}:00</div>
        <div class="sub">{hours_txt}</div>
      </div>
    </div>

    <div class="rec-box">
      <span class="rl">Recomendacion de hoy</span>
      {recommendation}
    </div>

    <section>
      <h2>Engagement por pilar de contenido</h2>
      <p class="section-sub">Clasificado automaticamente segun el texto de cada post</p>
      {pillar_bars}
    </section>

    <section>
      <h2>Engagement por formato</h2>
      <p class="section-sub">Reels vs Feed/Carrusel</p>
      {type_bars}
    </section>

    <section>
      <h2>Tendencia mensual</h2>
      <p class="section-sub">Engagement rate promedio, ultimos 12 meses</p>
      {trend_line}
    </section>

    <section>
      <h2>Top 5 — replica este angulo</h2>
      <div class="card-grid">{top_cards}</div>
    </section>

    <section>
      <h2>Bottom 5 — evita este patron</h2>
      <div class="card-grid">{bottom_cards}</div>
    </section>

    <footer>Generado automaticamente por GitHub Actions · datosgt-social-analytics</footer>
  </div>
</body>
</html>'''


def generate():
    d = build_dashboard()
    html = render_html(d)
    out_dir = ROOT / "docs"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Dashboard generado: {out_dir / 'index.html'}")


if __name__ == "__main__":
    generate()
