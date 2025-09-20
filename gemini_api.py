import requests
import os
import json
import json5
import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini_api")

@dataclass
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.5-pro"            # ✅ primary model
    fallback_model: str = "gemini-2.5-flash" # ✅ backup model
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: float = 45.0
    max_output_tokens: int = 2048   # bumped higher
    temperature: float = 0.7
    batch_size: int = 5             # process smaller sets at once
    rate_limit_delay: float = 1.0

class GeminiClient:
    def __init__(self, config: GeminiConfig):
        self.config = config
        self.last_request_time = 0

    # ---------------- rate limiting ----------------
    def _apply_rate_limiting(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    # ---------------- API call ----------------
    def _make_request(self, prompt: str, model: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_output_tokens,
                "stopSequences": ["]"],   # encourage clean JSON end
            },
        }
        headers = {"Content-Type": "application/json"}

        try:
            self._apply_rate_limiting()
            resp = requests.post(url, json=payload, headers=headers, timeout=self.config.timeout)
            resp.raise_for_status()
            data = resp.json()

            candidates = data.get("candidates")
            if not candidates:
                logger.error(f"⚠️ No candidates: {json.dumps(data)[:200]}")
                return None

            for idx, cand in enumerate(candidates):
                content = cand.get("content", {})
                parts = content.get("parts")
                if parts and isinstance(parts, list) and "text" in parts[0]:
                    finish = cand.get("finishReason")
                    if finish != "STOP":
                        logger.warning(f"⚠️ Candidate {idx} finishReason={finish}")
                    return parts[0]["text"]
                else:
                    logger.warning(f"⚠️ Candidate {idx} has no usable 'parts': {json.dumps(content)[:150]}")

            logger.error(f"❌ No candidate contained text")
            debug_file = "gemini_debug.json"
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {resp.status_code}: {resp.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    # ---------------- JSON salvage loader ----------------
    def _safe_loads(self, text: str) -> List[Dict]:
        if not text:
            return []
        txt = text.strip()

        # Strip markdown fences
        if txt.startswith("```"):
            lines = txt.splitlines()
            if lines[0].startswith("```json"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            txt = "\n".join(lines).strip()

        # First try normal parsing
        try:
            return json.loads(txt)
        except Exception:
            pass
        try:
            return json5.loads(txt)
        except Exception:
            # Attempt repair: close dangling stuff
            fixed = txt

            # Close dangling quotes
            if fixed.count('"') % 2 != 0:
                fixed += '"'

            # Ensure valid ending
            fixed = fixed.rstrip(", \n")
            if not fixed.endswith("]"):
                if not fixed.endswith("}"):
                    fixed += "}"
                if not fixed.endswith("]"):
                    fixed += "]"

            try:
                return json5.loads(fixed)
            except Exception as e:
                logger.error(f"❌ Cannot repair JSON: {e}\n{txt[:250]}")
                return []

    # ---------------- Generate ----------------
    def generate(self, articles: List[Dict]) -> List[Dict]:
        if not articles:
            logger.error("⚠️ No input articles")
            return []

        # Compact JSON (less tokens)
        clean_articles = [
            {"title": a.get("title", ""), "summary": a.get("summary", "")}
            for a in articles
        ]
        compact_input = json.dumps(clean_articles, separators=(",", ":"))

        prompt = f"""
Rephrase these news articles.

Return ONLY a JSON array. Each object must have:
- heading (short headline)
- summary (1-2 sentences plain text)

NO links, NO emojis, NO markdown, NO extra text.

Input:
{compact_input}

Output:
[{{"heading":"...","summary":"..."}}, ...]
"""

        for model in [self.config.model, self.config.fallback_model]:
            for attempt in range(self.config.max_retries):
                raw = self._make_request(prompt, model)
                if raw:
                    parsed = self._safe_loads(raw)
                    if parsed:
                        logger.info(f"✅ Gemini returned {len(parsed)} items (model={model} attempt={attempt+1})")
                        return parsed
                    else:
                        logger.warning("⚠️ Invalid JSON — retrying...")

                time.sleep(self.config.retry_delay)

        # If it keeps failing, split into halves
        if len(articles) > 1:
            logger.warning("⚠️ Splitting batch into halves due to repeated failures")
            mid = len(articles) // 2
            return self.generate(articles[:mid]) + self.generate(articles[mid:])

        logger.error("❌ No Gemini results even after splitting")
        return []

# ---------------- Helper ----------------
def generate_content(articles: List[Dict], config: Optional[GeminiConfig] = None) -> List[Dict]:
    if not config:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not set")
            return []
        config = GeminiConfig(api_key=api_key)
    client = GeminiClient(config)
    return client.generate(articles)

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Please set GEMINI_API_KEY in your environment")
    else:
        sample_articles = [
            {"title": f"AI News {i}", "summary": f"Details about AI news {i}."}
            for i in range(10)
        ]
        config = GeminiConfig(api_key=api_key)
        res = generate_content(sample_articles, config)
        print("Results:", json.dumps(res, indent=2))