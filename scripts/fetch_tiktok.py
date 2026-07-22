import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
FIELDS = "id,title,video_description,create_time,cover_image_url,share_url,view_count,like_count,comment_count,share_count"


def fetch():
    token = os.environ["TIKTOK_ACCESS_TOKEN"]

    videos = []
    cursor = 0
    has_more = True
    while has_more:
        resp = requests.post(
            f"{VIDEO_LIST_URL}?fields={FIELDS}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"max_count": 20, "cursor": cursor},
        )
        resp.raise_for_status()
        body = resp.json().get("data", {})
        videos.extend(body.get("videos", []))
        has_more = body.get("has_more", False)
        cursor = body.get("cursor", 0)

    out_path = ROOT / "data" / "tiktok_posts.json"
    out_path.write_text(json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat(), "posts": videos}, indent=2))
    return videos


if __name__ == "__main__":
    fetch()
