import os, json, time, logging, requests, re, tweepy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Explicitly load .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("twitter_poster")

@dataclass
class TwitterConfig:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: Optional[str] = None
    dry_run: bool = False

    @classmethod
    def from_env(cls):
        req = {
            "TWITTER_CONSUMER_KEY": "consumer_key",
            "TWITTER_CONSUMER_SECRET": "consumer_secret",
            "TWITTER_ACCESS_TOKEN": "access_token",
            "TWITTER_ACCESS_TOKEN_SECRET": "access_token_secret",
        }
        
        missing = [k for k in req if not os.getenv(k)]
        if missing:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")
        
        config = cls(
            **{v: os.getenv(k) for k, v in req.items()},
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
            dry_run=os.getenv("TWITTER_DRY_RUN", "false").lower() == "true"
        )
        return config

@dataclass
class Tweet:
    text: str
    reply_to_id: Optional[str] = None
    media_ids: Optional[List[str]] = None
    image_url: Optional[str] = None
    article_link: Optional[str] = None

class TwitterPoster:
    MAX_TWEET_LENGTH = 280
    TWITTER_LINK_LENGTH = 23
    MAX_NEWS_ITEMS = 10
    
    def __init__(self, config: TwitterConfig):
        self.config = config
        try:
            # V2 client
            self.client = tweepy.Client(
                consumer_key=config.consumer_key,
                consumer_secret=config.consumer_secret,
                access_token=config.access_token,
                access_token_secret=config.access_token_secret,
                bearer_token=config.bearer_token,
                wait_on_rate_limit=False
            )
            # V1.1 API
            auth = tweepy.OAuth1UserHandler(
                config.consumer_key, config.consumer_secret,
                config.access_token, config.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=False)
            
            # Verify authentication
            me = self.client.get_me()
            if me and me.data:
                logger.info(f"✅ Authenticated as @{me.data.username}")
            else:
                logger.error("❌ Authentication failed - no user data returned")
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            raise

    # -------------------- Image upload --------------------
    def download_upload_image(self, url: str) -> Optional[str]:
        if not url: return None
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if resp.status_code == 200 and 'image' in resp.headers.get('content-type', ''):
                temp_path = Path(f"/tmp/img_{int(time.time()*1000)}.jpg")
                temp_path.write_bytes(resp.content)
                media = self.api_v1.media_upload(str(temp_path))
                temp_path.unlink(missing_ok=True)
                logger.info(f"✅ Image uploaded: {media.media_id}")
                return str(media.media_id)
        except Exception as e:
            logger.error(f"❌ Image error: {e}")
        return None

    # -------------------- Tweet Posting --------------------
    def post_tweet(self, tweet: Tweet, retry: int = 3) -> Optional[str]:
        if not tweet.text.strip():
            return None
        if self.config.dry_run:
            logger.info(f"✅ Dry run: would post {tweet.text[:45]}...")
            return f"dry_{int(time.time())}"
        if tweet.image_url:
            media_id = self.download_upload_image(tweet.image_url)
            if media_id:
                tweet.media_ids = [media_id]

        for attempt in range(retry):
            try:
                # Try v2
                resp = self.client.create_tweet(
                    text=tweet.text,
                    in_reply_to_tweet_id=tweet.reply_to_id,
                    media_ids=tweet.media_ids
                )
                if resp.data:
                    logger.info(f"✅ Posted via v2: {tweet.text[:45]}...")
                    return resp.data['id']
            except tweepy.Forbidden as e:
                logger.warning("⚠️ v2 create_tweet forbidden, falling back to v1.1")
                try:
                    if tweet.media_ids:
                        status = self.api_v1.update_status(
                            status=tweet.text,
                            in_reply_to_status_id=tweet.reply_to_id,
                            media_ids=tweet.media_ids
                        )
                    else:
                        status = self.api_v1.update_status(
                            status=tweet.text,
                            in_reply_to_status_id=tweet.reply_to_id
                        )
                    logger.info(f"✅ Posted via v1.1: {tweet.text[:45]}...")
                    return status.id_str
                except tweepy.Forbidden as e1:
                    logger.error(f"❌ v1.1 post failed: {e1}")
                    return None
                except Exception as e1:
                    logger.error(f"❌ v1.1 post failed: {e1}")
            except tweepy.TooManyRequests:
                logger.warning("⏰ Rate limited, skipping...")
                return None
            except Exception as e:
                logger.error(f"❌ Tweet error (attempt {attempt+1}): {e}")
                if attempt < retry - 1:
                    time.sleep(5 * (attempt + 1))
        return None

    # -------------------- Format Threads --------------------
    def format_index_tweet(self, threads: List[Dict]) -> str:
        header = f"🚀 Top {min(len(threads), self.MAX_NEWS_ITEMS)} Tech/AI News - {datetime.now():%Y-%m-%d}:\n\n"
        items = []
        for i, item in enumerate(threads[:self.MAX_NEWS_ITEMS]):
            heading = item.get('heading', '').strip()
            if heading and len(header + '\n'.join(items) + f"{i+1}. {heading}\n") < self.MAX_TWEET_LENGTH - 20:
                items.append(f"{i+1}. {heading}")
        return header + '\n'.join(items) if items else header.strip()

    def format_news_tweet(self, item: Dict, article: Dict, idx: int, total: int) -> Tweet:
        heading = item.get('heading', '').strip()
        summary = item.get('summary', '').strip()
        link = (article.get('link') or article.get('url', '')) if article else ''
        image_url = article.get("image") or None
        
        if not heading: return Tweet(text="")
        
        base = f"📰 {idx}/{total}: {heading}"
        space_left = self.MAX_TWEET_LENGTH - len(base) - (self.TWITTER_LINK_LENGTH + 4 if link else 0) - 4
        
        text = base
        if summary and space_left > 20:
            text += f"\n\n{summary[:space_left-3]+'...' if len(summary) > space_left else summary}"
        if link: text += f"\n\n🔗 {link}"
        
        return Tweet(text=text, image_url=image_url, article_link=link)

    # -------------------- Runner --------------------
    def run(self, content_path: Path) -> bool:
        try:
            if not content_path.exists():
                logger.error(f"❌ Content file not found: {content_path}")
                return False
                
            with open(content_path) as f: 
                content = json.load(f)
            threads = content.get("twitter", {}).get("threads", [])[:self.MAX_NEWS_ITEMS]
            if not threads: 
                logger.error("❌ No threads found in content")
                return False
            
            articles = []
            articles_path = content_path.parent / "scraped_articles.json"
            if articles_path.exists():
                with open(articles_path) as f: 
                    articles = json.load(f)
                logger.info(f"✅ Loaded {len(articles)} original articles")
            
            tweets = [Tweet(text=self.format_index_tweet(threads))]
            for i, item in enumerate(threads):
                article = articles[i] if i < len(articles) else {}
                tweet = self.format_news_tweet(item, article, i + 1, len(threads))
                if tweet.text: tweets.append(tweet)
            
            logger.info(f"🧵 Starting posts: {len(tweets)} tweets")
            
            posted = 0
            for i, tweet in enumerate(tweets):
                tweet.reply_to_id = None  # Post each as separate tweet
                result = self.post_tweet(tweet)
                if not result:
                    logger.warning(f"⚠️ Failed to post tweet {i + 1}, continuing...")
                else:
                    posted += 1
            
            success = posted == len(tweets)
            logger.info(f"{'🎉 Success' if success else '⚠️ Partial'}: {posted}/{len(tweets)} tweets posted")
            return success
            
        except Exception as e:
            logger.error(f"❌ Run error: {e}")
            import traceback; traceback.print_exc()
            return False

def main():
    try:
        config = TwitterConfig.from_env()
        poster = TwitterPoster(config)
        content_path = Path("output/content.json")
        success = poster.run(content_path)
        logger.info("🎉 Twitter posting completed!" if success else "❌ Twitter posting failed")
    except Exception as e:
        logger.error(f"❌ Main error: {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()