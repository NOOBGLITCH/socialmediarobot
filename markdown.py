import os, json, logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Tweet:
    text: str
    article_link: Optional[str] = None

class MarkdownPoster:
    MAX_TWEET_LENGTH = 280
    TWITTER_LINK_LENGTH = 23
    MAX_NEWS_ITEMS = 10   # 🚀 Always produce exactly 10 detail posts
    
    def __init__(self):
        pass

    def format_index_tweet(self, threads: List[Dict]) -> str:
        """Create the index/top post with a clean Top 10 list"""
        today = datetime.now().strftime("%d-%m-%Y")
        header = f"🚀 Top {self.MAX_NEWS_ITEMS} Tech/AI News Of The Day - {today}:\n\n"
        items = []
        for i, item in enumerate(threads[:self.MAX_NEWS_ITEMS]):
            heading = item.get('heading', '').strip()
            if heading:
                items.append(f"{i+1}. {heading}")
        return header + '\n'.join(items) if items else header.strip()

    def format_news_tweet(self, item: Dict, article: Dict, idx: int, total: int) -> Tweet:
        """Cleanly formats a detail post, ensures no duplicate 📰 prefixes"""
        heading = item.get('heading', '').strip()
        summary = item.get('summary', '').strip()
        link = (article.get('link') or article.get('url', '')) if article else ''
        
        if not heading:
            return Tweet(text="")
        
        # 🧹 Clean rogue Gemini numbering like "📰 2/10..." inside the summary
        cleaned_lines = []
        for line in summary.splitlines():
            if line.strip().startswith("📰"):
                continue
            cleaned_lines.append(line)
        summary = " ".join(cleaned_lines).strip()

        base = f"📰 {idx}/{total}: {heading}"
        space_left = self.MAX_TWEET_LENGTH - len(base) - (self.TWITTER_LINK_LENGTH + 4 if link else 0) - 4

        text = base
        if summary and space_left > 20:
            words = summary.split()
            truncated = []
            for word in words:
                if len(" ".join(truncated + [word])) <= space_left:
                    truncated.append(word)
                else:
                    break
            text += f"\n\n{' '.join(truncated)}" + ("..." if len(truncated) < len(words) else "")

        if link:
            text += f"\n\n🔗 {link}"

        return Tweet(text=text, article_link=link)

    def run(self, content_path: Path) -> bool:
        try:
            if not content_path.exists():
                logger.error(f"❌ Content file not found: {content_path}")
                return False
                
            with open(content_path) as f: 
                content = json.load(f)

            # strip out any Gemini-provided Top 10 Index entry
            all_threads = content.get("twitter", {}).get("threads", [])
            if all_threads and all_threads[0].get("heading","").lower().startswith("top 10"):
                threads = all_threads[1:]
            else:
                threads = all_threads
            threads = threads[:self.MAX_NEWS_ITEMS]

            if not threads:
                logger.error("❌ No valid article threads found in content")
                return False
            
            # Load original articles (for links)
            articles = []
            articles_path = content_path.parent / "scraped_articles.json"
            if articles_path.exists():
                with open(articles_path) as f: 
                    articles = json.load(f)
                logger.info(f"✅ Loaded {len(articles)} original articles")
            else:
                logger.warning("⚠️ No scraped_articles.json found")

            # Index post
            tweets = [Tweet(text=self.format_index_tweet(threads))]

            # Detail posts (guarantee 1/10..10/10)
            for i, item in enumerate(threads, start=1):
                article = articles[i-1] if i-1 < len(articles) else {}
                tweet = self.format_news_tweet(item, article, i, self.MAX_NEWS_ITEMS)
                if tweet.text:
                    tweets.append(tweet)

            # Closing
            today = datetime.now().strftime("%d-%m-%Y")
            closing = f"✅ That's a wrap for {today}! 🚀 Stay tuned for tomorrow's top tech stories."
            tweets.append(Tweet(text=closing))

            # Write to file
            file_date = datetime.now().strftime("%d--%m-%Y")  # `DD--MM-YYYY`
            md_file = Path(f"news-{file_date}.md")

            with open(md_file, "w", encoding="utf-8") as f:
                for i, tweet in enumerate(tweets):
                    f.write(tweet.text.strip() + "\n\n")
                    if i < len(tweets)-1:
                        f.write("---\n\n")

            logger.info(f"🎉 News exported to {md_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Run error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    poster = MarkdownPoster()
    content_path = Path("output/content.json")
    success = poster.run(content_path)
    logger.info("✅ Markdown creation completed!" if success else "❌ Markdown creation failed")

if __name__ == "__main__":
    main()