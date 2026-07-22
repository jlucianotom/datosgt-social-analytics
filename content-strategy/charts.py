import io

import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

matplotlib.use("Agg")

GOLD = "#c9a84c"
GOLD_DIM = "#6e5c2a"
RED = "#b0564f"
TEXT = "#f4f4f2"
MUTED = "#8f8f8f"
GRID = "#2a2a28"

plt.rcParams["font.family"] = "Segoe UI"
plt.rcParams["text.color"] = TEXT
plt.rcParams["axes.edgecolor"] = GRID
plt.rcParams["axes.labelcolor"] = MUTED
plt.rcParams["xtick.color"] = MUTED
plt.rcParams["ytick.color"] = MUTED


def _fig_to_rgba(fig, w_px, h_px, dpi=200):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    img.thumbnail((w_px, h_px), Image.LANCZOS)
    return img


def chart_facturado_vs_real(w_px, h_px):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    labels = ["Facturado", "En la cuenta"]
    values = [42000, 18400]
    colors = [GOLD, RED]
    bars = ax.bar(labels, values, color=colors, width=0.5, zorder=3)

    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1200, f"Q{v:,.0f}", ha="center",
                 fontsize=20, fontweight="bold", color=TEXT)

    ax.set_ylim(0, 50000)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.tick_params(axis="x", labelsize=19, length=0)
    ax.grid(False)
    return _fig_to_rgba(fig, w_px, h_px)


def chart_margen_por_producto(w_px, h_px):
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    labels = [f"P{i}" for i in range(1, 7)]
    values = [18, 12, -6, 9, -4, -8]
    colors = [GOLD if v >= 0 else RED for v in values]
    ax.bar(labels, values, color=colors, width=0.55, zorder=3)
    ax.axhline(0, color=MUTED, linewidth=1.2, zorder=2)

    ax.text(5.6, 21, "margen positivo", fontsize=13, color=MUTED, ha="right")
    ax.text(5.6, -16, "vendido con pérdida", fontsize=13, color=RED, ha="right")

    ax.set_ylim(-20, 24)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.tick_params(axis="x", labelsize=17, length=0)
    ax.grid(False)
    return _fig_to_rgba(fig, w_px, h_px)


def chart_pestanas_inconsistentes(w_px, h_px):
    import random
    rng = random.Random(7)

    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    n = 14
    values = [18400 + rng.randint(-3800, 4600) for _ in range(n)]
    colors = [GOLD if abs(v - 18400) < 900 else GOLD_DIM for v in values]
    ax.bar(range(n), values, color=colors, width=0.62, zorder=3)
    ax.axhline(18400, color=TEXT, linewidth=1.2, linestyle=(0, (5, 4)), zorder=2, alpha=0.6)
    ax.text(n - 1, 18400 + 900, "¿cuál es el número real?", fontsize=13, color=MUTED, ha="right")

    ax.set_xticks([])
    ax.set_ylim(12000, 25000)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.grid(False)
    return _fig_to_rgba(fig, w_px, h_px)


def chart_antes_despues(w_px, h_px):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    labels = ["Antes", "8 semanas después"]
    values = [4.2, 11.8]
    colors = [GOLD_DIM, GOLD]
    bars = ax.bar(labels, values, color=colors, width=0.5, zorder=3)

    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%", ha="center",
                 fontsize=20, fontweight="bold", color=TEXT)

    ax.set_ylim(0, 14)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.tick_params(axis="x", labelsize=19, length=0)
    ax.grid(False)
    return _fig_to_rgba(fig, w_px, h_px)
