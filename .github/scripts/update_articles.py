"""Rewrite the Latest Articles list in README.md from the synepho.com RSS feed."""

import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED_URL = "https://www.synepho.com/feed.xml"
README = Path("README.md")
MAX_POSTS = 4
NEW_WITHIN = timedelta(days=30)
BLOCK = re.compile(
    r"(<!-- BLOG-POSTS:START -->\n).*?(\n<!-- BLOG-POSTS:END -->)", re.DOTALL
)


def fetch_posts() -> list[tuple[str, str, datetime]]:
    with urllib.request.urlopen(FEED_URL, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        if title and link and pub:
            posts.append((title, link, parsedate_to_datetime(pub)))
    posts.sort(key=lambda p: p[2], reverse=True)
    return posts[:MAX_POSTS]


def render(posts: list[tuple[str, str, datetime]]) -> str:
    now = datetime.now(timezone.utc)
    lines = []
    for title, link, date in posts:
        marker = "🆕 " if now - date <= NEW_WITHIN else ""
        lines.append(f"- {marker}[{title}]({link}) - {date:%b} {date.day}, {date.year}")
    return "\n".join(lines)


def main() -> int:
    posts = fetch_posts()
    if not posts:
        print("Feed returned no posts; leaving README untouched", file=sys.stderr)
        return 1
    text = README.read_text(encoding="utf-8")
    if not BLOCK.search(text):
        print("BLOG-POSTS markers not found in README.md", file=sys.stderr)
        return 1
    new_text = BLOCK.sub(lambda m: m.group(1) + render(posts) + m.group(2), text)
    if new_text != text:
        README.write_text(new_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
