import feedparser, hashlib, os, requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASS = os.getenv("WP_PASS")

HEADERS = {'Content-Type': 'application/json'}
AUTH = (WP_USER, WP_PASS)

with open("feeds.txt") as f:
    feeds = [line.strip() for line in f if line.strip()]

if os.path.exists("published_hashes.txt"):
    with open("published_hashes.txt") as f:
        published_hashes = set(f.read().splitlines())
else:
    published_hashes = set()

def is_duplicate(title):
    h = hashlib.md5(title.encode()).hexdigest()
    return h in published_hashes, h

def save_hash(h):
    with open("published_hashes.txt", "a") as f:
        f.write(h + "\n")

def publish_to_wp(title, link, source):
    content = f"<p>#<strong>{source}</strong><br><a href='{link}' target='_blank' rel='noopener'>Citește articolul original</a></p>"
    data = {
        "title": title,
        "status": "publish",
        "content": content
    }
    r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", auth=AUTH, headers=HEADERS, json=data)
    print(f"[+] Publicat: {title}" if r.status_code == 201 else f"[-] Eroare: {r.text}")

for feed_url in feeds:
    d = feedparser.parse(feed_url)
    for entry in d.entries:
        if hasattr(entry, 'published_parsed'):
            published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - published_dt > timedelta(minutes=10):
                continue
            title = entry.title.strip()
            link = entry.link
            source = feed_url.split("//")[1].split("/")[0]
            duplicate, hash_val = is_duplicate(title)
            if duplicate:
                continue
            publish_to_wp(title, link, source)
            save_hash(hash_val)
