import pandas as pd
import feedparser
import os, json, hashlib, logging, time as time_module
from datetime import datetime, time
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
from gemini_api import generate_content, GeminiConfig   # <- your Gemini wrapper

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------- CONFIG ---------------- #
@dataclass
class ScrapingConfig:
    rss_file: str = "rss.xlsx"
    output_dir: str = "output"
    max_articles: int = 15
    max_articles_per_feed: int = 6
    timezone: str = "Asia/Kolkata"
    start_hour: int = 0
    end_hour: int = 19
    request_delay: float = 0.3


# ---------------- DATETIME HANDLING ---------------- #
class DateTimeHandler:
    def __init__(self, tz="Asia/Kolkata"):
        self.tz = ZoneInfo(tz)

    def get_today_range(self, start=0, end=19):
        now = datetime.now(self.tz)
        today = now.date()
        return (
            datetime.combine(today, time(start, 0)).replace(tzinfo=self.tz),
            datetime.combine(today, time(end, 0)).replace(tzinfo=self.tz),
        )

    def parse_date(self, ds: str) -> Optional[datetime]:
        if not ds:
            return None
        ds = ds.replace(" GMT", " +0000").replace(" UTC", " +0000")
        fmts = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S %z",
        ]
        for f in fmts:
            try:
                return datetime.strptime(ds, f).astimezone(self.tz)
            except:
                continue
        return None


# ---------------- FILTERING ---------------- #
class ArticleFilter:
    def __init__(self):
        self.titles, self.links, self.hashes = set(), set(), set()

    def norm(self, t): 
        return t.lower().strip()

    def hsh(self, a): 
        return hashlib.md5((a["title"][:100] + a["summary"][:200]).encode()).hexdigest()

    def seen(self, a):
        return (
            self.norm(a["title"]) in self.titles
            or (a["link"] and a["link"] in self.links)
            or self.hsh(a) in self.hashes
        )

    def add(self, a):
        self.titles.add(self.norm(a["title"]))
        if a["link"]:
            self.links.add(a["link"])
        self.hashes.add(self.hsh(a))


# ---------------- RSS SCRAPER ---------------- #
class RSSFeedScraper:
    def __init__(self, cfg: ScrapingConfig):
        self.cfg, self.filter, self.dt = cfg, ArticleFilter(), DateTimeHandler(cfg.timezone)

    def load(self) -> List[str]:
        try:
            df = pd.read_excel(self.cfg.rss_file)
            return df["RSS Feed URL"].dropna().tolist()
        except Exception as e:
            logger.error(f"❌ RSS file error: {e}")
            return []

    def scrape_feed(self, url, ignore_time=False):
        entries, (start, end) = [], self.dt.get_today_range(self.cfg.start_hour, self.cfg.end_hour)
        feed = feedparser.parse(url)
        for e in feed.entries[: self.cfg.max_articles_per_feed]:
            art = {
                "title": e.get("title", "").strip(),
                "summary": e.get("summary", e.get("description", "")).strip(),
                "link": e.get("link", "").strip(),
                "published": e.get("published", ""),
            }
            if not art["title"]: 
                continue
            pd = self.dt.parse_date(art["published"])
            art["published_datetime"] = pd
            if not ignore_time and pd and not (start <= pd <= end):
                continue
            if self.filter.seen(art): 
                continue
            self.filter.add(art)
            entries.append(art)
        return entries

    def run(self) -> List[Dict]:
        feeds = self.load()
        all_articles = []

        # First pass: today's articles
        for i, u in enumerate(feeds):
            all_articles += self.scrape_feed(u)
            if i < len(feeds) - 1:
                time_module.sleep(self.cfg.request_delay)

        # Sort by date descending
        all_articles.sort(
            key=lambda a: a.get("published_datetime", datetime.min), reverse=True
        )

        # Guarantee at least 10
        if len(all_articles) < 10:
            logger.warning(f"⚠️ Only {len(all_articles)} fresh articles found. Filling with older ones...")
            for u in feeds:
                extras = self.scrape_feed(u, ignore_time=True)
                for ex in extras:
                    if len(all_articles) >= 10:
                        break
                    all_articles.append(ex)
                if len(all_articles) >= 10:
                    break

        return all_articles[:10]  # Always 10


# ---------------- THREAD FORMATTER ---------------- #
def build_thread_format(items: List[Dict]) -> Dict:
    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y")
    threads = []

    # Build index post
    index_lines = []
    for i in range(10):
        if i < len(items):
            headline = items[i].get("heading", f"Article {i+1}")
            index_lines.append(f"{i+1}. {headline}")
        else:
            index_lines.append(f"{i+1}. (No article available)")
    index_text = f"🚀 Top 10 Tech/AI News of the Day ({today})\n\n" + "\n".join(index_lines)
    threads.append({"heading": "Top 10 Index", "summary": index_text})

    # Build detail posts
    for i in range(10):
        if i < len(items):
            a = items[i]
            heading = a.get("heading", f"Article {i+1}")
            summary = a.get("summary", "No summary available")
            link = a.get("link", "")
        else:
            heading = f"Article {i+1}"
            summary = "(No summary available)"
            link = ""

        txt = f"📰 {i+1}/10: {heading}\n\n{summary}"
        if link:
            txt += f"\n\n🔗 {link}"

        threads.append({"heading": heading, "summary": txt})

    return {
        "twitter": {"threads": threads},
        "linkedin": {"threads": threads},
        "instagram": {"threads": threads},
    }


# ---------------- MAIN ---------------- #
def main():
    logger.info("🚀 Starting RSS scraping...")
    cfg = ScrapingConfig()
    scraper = RSSFeedScraper(cfg)
    articles = scraper.run()
    if not articles:
        return logger.error("❌ No articles scraped")

    # Add stable IDs
    for i, art in enumerate(articles, 1):
        art["id"] = i

    # Gemini config
    gem_cfg = GeminiConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        batch_size=10,
        max_retries=1,
        retry_delay=1.0,
    )

    logger.info(f"📝 Sending {len(articles)} articles to Gemini...")
    start = time_module.time()
    results = generate_content(articles, gem_cfg)
    logger.info(f"✅ Gemini done in {time_module.time()-start:.1f}s")

    if not results:
        return logger.error("❌ No Gemini results")

    # Merge Gemini results with original links
    merged = []
    for art, res in zip(articles, results):
        merged.append({
            "id": art["id"],
            "heading": res.get("heading", art.get("title", f"Article {art['id']}")),
            "summary": res.get("summary", art.get("summary", "No summary available")),
            "link": art.get("link", ""),   # ✅ Always preserve link from RSS
        })

    # Build content format
    content = build_thread_format(merged)

    out = Path(cfg.output_dir)
    out.mkdir(exist_ok=True)
    (out / "content.json").write_text(json.dumps(content, indent=2, ensure_ascii=False))
    (out / "scraped_articles.json").write_text(json.dumps(articles, indent=2, default=str))
    logger.info("🎉 Saved to output/content.json")


if __name__ == "__main__":
    main()