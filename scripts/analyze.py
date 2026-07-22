import json
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    path = ROOT / "data" / name
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("posts", [])


def _normalize_instagram(posts):
    rows = []
    for p in posts:
        insights = p.get("insights", {})
        reach = insights.get("reach", 0)
        views = insights.get("views", 0)
        likes = insights.get("likes", p.get("like_count") or 0)
        comments = insights.get("comments", p.get("comments_count") or 0)
        saves = insights.get("saved", 0)
        shares = insights.get("shares", 0)
        interactions = insights.get("total_interactions") or (likes + comments + saves + shares)
        rows.append({
            "platform": "instagram",
            "content_type": p.get("media_product_type") or p.get("media_type") or "OTHER",
            "id": p["id"],
            "text": p.get("caption") or "",
            "timestamp": p.get("timestamp"),
            "reach": reach,
            "views": views,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "shares": shares,
            "interactions": interactions,
            "engagement_rate": (interactions / reach) if reach else 0,
            "url": p.get("permalink"),
        })
    return rows


def _normalize_tiktok(posts):
    rows = []
    for p in posts:
        views = p.get("view_count", 0)
        likes = p.get("like_count") or 0
        comments = p.get("comment_count") or 0
        shares = p.get("share_count") or 0
        interactions = likes + comments + shares
        rows.append({
            "platform": "tiktok",
            "content_type": "VIDEO",
            "id": p["id"],
            "text": p.get("video_description") or p.get("title") or "",
            "timestamp": datetime.fromtimestamp(p["create_time"]).isoformat() if p.get("create_time") else None,
            "reach": views,
            "views": views,
            "likes": likes,
            "comments": comments,
            "saves": 0,
            "shares": shares,
            "interactions": interactions,
            "engagement_rate": (interactions / views) if views else 0,
            "url": p.get("share_url"),
        })
    return rows


def _hour_buckets(rows):
    buckets = {}
    for r in rows:
        if not r["timestamp"]:
            continue
        hour = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")).hour
        buckets.setdefault(hour, []).append(r["engagement_rate"])
    return {h: statistics.mean(v) for h, v in buckets.items() if v}


def _length_buckets(rows):
    buckets = {"corto (<50)": [], "medio (50-150)": [], "largo (>150)": []}
    for r in rows:
        n = len(r["text"])
        key = "corto (<50)" if n < 50 else "medio (50-150)" if n <= 150 else "largo (>150)"
        buckets[key].append(r["engagement_rate"])
    return {k: statistics.mean(v) for k, v in buckets.items() if v}


def _avg(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else 0


def _group_stats(rows, key_fn):
    groups = {}
    for r in rows:
        groups.setdefault(key_fn(r), []).append(r)
    stats = {}
    for key, group in groups.items():
        stats[key] = {
            "n": len(group),
            "reach": _avg([g["reach"] for g in group]),
            "views": _avg([g["views"] for g in group]),
            "likes": _avg([g["likes"] for g in group]),
            "comments": _avg([g["comments"] for g in group]),
            "saves": _avg([g["saves"] for g in group]),
            "shares": _avg([g["shares"] for g in group]),
            "engagement_rate": _avg([g["engagement_rate"] for g in group]),
        }
    return stats


def _comparative_table(stats, label_col):
    header = f"| {label_col} | Publicaciones | Alcance prom. | Vistas prom. | Likes prom. | Comentarios prom. | Guardados prom. | Compartidos prom. | Engagement rate |"
    sep = "|---|---|---|---|---|---|---|---|---|"
    lines = [header, sep]
    for key, s in stats.items():
        lines.append(
            f"| {key} | {s['n']} | {s['reach']:.0f} | {s['views']:.0f} | {s['likes']:.0f} | "
            f"{s['comments']:.0f} | {s['saves']:.0f} | {s['shares']:.0f} | {s['engagement_rate']:.2%} |"
        )
    return lines


def analyze():
    ig_rows = _normalize_instagram(_load("instagram_posts.json"))
    tt_rows = _normalize_tiktok(_load("tiktok_posts.json"))
    rows = ig_rows + tt_rows
    if not rows:
        raise SystemExit("No hay datos en data/. Corre fetch_instagram.py y fetch_tiktok.py primero.")

    rows.sort(key=lambda r: r["engagement_rate"], reverse=True)
    top = rows[:5]
    bottom = rows[-5:]
    hour_perf = sorted(_hour_buckets(rows).items(), key=lambda x: x[1], reverse=True)
    length_perf = _length_buckets(rows)

    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# Reporte de analitica cruzada — {today}", ""]

    lines.append("## Comparativa por plataforma")
    platform_stats = _group_stats(rows, lambda r: r["platform"])
    lines += _comparative_table(platform_stats, "Plataforma")
    lines.append("")

    if ig_rows:
        lines.append("## Comparativa por tipo de contenido (Instagram: Reels vs Feed)")
        content_stats = _group_stats(ig_rows, lambda r: r["content_type"])
        lines += _comparative_table(content_stats, "Tipo")
        lines.append("")

    lines.append("## Top 5 contenido (mayor engagement rate)")
    for r in top:
        lines.append(
            f"- [{r['platform']}/{r['content_type']}] {r['engagement_rate']:.2%} "
            f"(alcance {r['reach']:.0f}, likes {r['likes']:.0f}, comentarios {r['comments']:.0f}) "
            f"— \"{r['text'][:80]}\" — {r['url']}"
        )
    lines.append("")

    lines.append("## Bottom 5 contenido (menor engagement rate)")
    for r in bottom:
        lines.append(
            f"- [{r['platform']}/{r['content_type']}] {r['engagement_rate']:.2%} "
            f"(alcance {r['reach']:.0f}, likes {r['likes']:.0f}, comentarios {r['comments']:.0f}) "
            f"— \"{r['text'][:80]}\" — {r['url']}"
        )
    lines.append("")

    lines.append("## Mejores horas para publicar (promedio engagement rate)")
    for hour, rate in hour_perf[:5]:
        lines.append(f"- {hour:02d}:00 — {rate:.2%}")
    lines.append("")

    lines.append("## Longitud de texto vs engagement")
    for bucket, rate in length_perf.items():
        lines.append(f"- {bucket}: {rate:.2%}")
    lines.append("")

    lines.append("## Recomendaciones para el proximo guion")
    if length_perf:
        best_length = max(length_perf, key=length_perf.get)
        lines.append(f"- Prioriza duracion de texto/guion tipo **{best_length}**, es la que mejor convierte para ti.")
    if hour_perf:
        lines.append(f"- Publica cerca de las **{hour_perf[0][0]:02d}:00**, es tu franja de mejor desempeno.")
    if ig_rows:
        content_stats = _group_stats(ig_rows, lambda r: r["content_type"])
        if content_stats:
            best_type = max(content_stats, key=lambda k: content_stats[k]["engagement_rate"])
            lines.append(f"- Prioriza formato **{best_type}**, es el que mejor convierte en tu cuenta.")
    if top:
        lines.append(f"- Replica el angulo/formato del top 1: \"{top[0]['text'][:120]}\"")
    lines.append("- Guia general de guiones (frameworks, hooks, timing): ver `reports/guia_guiones.md`")
    lines.append("")

    report_path = ROOT / "reports" / f"report_{today}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    path = analyze()
    print(f"Reporte generado: {path}")
