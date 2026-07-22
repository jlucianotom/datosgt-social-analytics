import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

GRAPH_URL = "https://graph.facebook.com/v21.0"

MEDIA_FIELDS = "id,caption,media_type,media_product_type,media_url,permalink,timestamp,like_count,comments_count"
REEL_METRICS = "views,reach,likes,comments,shares,saved,total_interactions"
POST_METRICS = "reach,saved,total_interactions"


def fetch_media_insights(media_id, media_product_type, token):
    metrics = REEL_METRICS if media_product_type == "REELS" else POST_METRICS
    resp = requests.get(
        f"{GRAPH_URL}/{media_id}/insights",
        params={"metric": metrics, "access_token": token},
    )
    if resp.status_code != 200:
        return {}
    return {item["name"]: item["values"][0]["value"] for item in resp.json().get("data", [])}


def fetch_all_media(account_id, token):
    posts = []
    url = f"{GRAPH_URL}/{account_id}/media"
    params = {"fields": MEDIA_FIELDS, "access_token": token, "limit": 100}
    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        body = resp.json()
        posts.extend(body.get("data", []))
        url = body.get("paging", {}).get("next")
        params = None  # next URL already includes all query params
    return posts


def fetch():
    token = os.environ["IG_ACCESS_TOKEN"]
    account_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]

    posts = fetch_all_media(account_id, token)

    for i, post in enumerate(posts, 1):
        post["insights"] = fetch_media_insights(post["id"], post.get("media_product_type"), token)
        print(f"  {i}/{len(posts)} — {post['id']}")

    out_path = ROOT / "data" / "instagram_posts.json"
    out_path.write_text(json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat(), "posts": posts}, indent=2))
    return posts


if __name__ == "__main__":
    fetch()
