import os
from pathlib import Path

from dotenv import load_dotenv

from fetch_instagram import fetch as fetch_instagram
from fetch_tiktok import fetch as fetch_tiktok
from analyze import analyze

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

if __name__ == "__main__":
    fetch_instagram()
    print("Instagram: datos actualizados.")

    if os.environ.get("TIKTOK_ACCESS_TOKEN"):
        fetch_tiktok()
        print("TikTok: datos actualizados.")
    else:
        print("TikTok: sin token configurado todavia, se omite (correlo con tiktok_oauth_helper.py cuando este listo).")

    path = analyze()
    print(f"Loop diario completo. Reporte: {path}")
