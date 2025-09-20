from PIL import Image, ImageDraw, ImageFont
import os, json, re
from datetime import datetime
from zoneinfo import ZoneInfo

# ---------------- Fonts / Helpers ---------------- #

def load_font(size: int):
    font_path = "Iceland-Regular.ttf"
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    print("⚠️ Iceland-Regular.ttf not found, fallback default font")
    return ImageFont.load_default()

def clean(text: str) -> str:
    """Remove emojis/unicode → ASCII only."""
    return re.sub(r"[^\x00-\x7F]+", "", str(text)).strip()

def remove_links(text: str) -> str:
    """Remove http/https links from a given text."""
    return re.sub(r"http\S+|www\.\S+", "", str(text))

def strip_numbering(text: str) -> str:
    """Remove undesired n/10 prefixes from summaries."""
    return re.sub(r"^\s*\d+/\d+:\s*", "", clean(text))

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        if draw.textlength(test, font=font) <= max_width:
            line.append(word)
        else:
            if line: 
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return lines

def draw_centered(draw, text, font, width, y, fill="white"):
    """Draw text centered horizontally with a shadow."""
    text = clean(remove_links(text))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) // 2
    # shadow for contrast
    draw.text((x + 3, y + 3), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill=fill)
    return th

# ---------------- Generators ---------------- #

def generate_index(date_str, headlines, save_path):
    img = Image.open("image.jpg").convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # 🔥 Big easy-to-read fonts for index page
    title_font = load_font(64)
    list_font  = load_font(44)

    title = f"Top 10 Tech/AI News Of The Day - {date_str}:"
    items = [f"{i+1}. {remove_links(clean(h))}" for i, h in enumerate(headlines)]

    bbox = draw.textbbox((0, 0), title, font=title_font)
    th = bbox[3] - bbox[1]
    total_h = th + 60 + sum(
        [draw.textbbox((0,0), txt, font=list_font)[3] - draw.textbbox((0,0), txt, font=list_font)[1] + 18 for txt in items]
    )
    y = (H - total_h) // 2

    draw_centered(draw, title, title_font, W, y)
    y += th + 60
    for txt in items:
        lh = draw_centered(draw, txt, list_font, W, y)
        y += lh + 18

    img.save(save_path)
    print("✅ index.jpg saved")

def generate_card(idx, headline, summary, source, save_path):
    img = Image.open("image.jpg").convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # 🔥 Big, clear fonts for card page
    head_font = load_font(50)   # headline, very bold
    sum_font  = load_font(48)   # summary, chunky readable
    src_font  = load_font(36)   # source label

    # Headline → numbering prefix
    headline = f"{idx}/10: {remove_links(clean(headline))}"
    summary  = strip_numbering(remove_links(summary or "No summary available"))
    source   = remove_links(clean(source or ""))

    lines = wrap_text(draw, summary, sum_font, W - 120)

    bbox = draw.textbbox((0, 0), headline, font=head_font)
    hh = bbox[3] - bbox[1]
    sum_h = sum([draw.textbbox((0,0), l, font=sum_font)[3] - draw.textbbox((0,0), l, font=sum_font)[1] for l in lines])
    block_h = hh + 40 + sum_h + len(lines) * 16
    y = (H - block_h) // 2

    draw_centered(draw, headline, head_font, W, y)
    y += hh + 40
    for l in lines:
        lh = draw_centered(draw, l, sum_font, W, y)
        y += lh + 16

    if source:
        st = f"source: {source}"
        bb = draw.textbbox((0, 0), st, font=src_font)
        sh = bb[3] - bb[1]
        draw.text((30+3, H - sh - 70 + 3), st, font=src_font, fill="black")
        draw.text((30,   H - sh - 70), st, font=src_font, fill="white")

    img.save(save_path)
    print(f"✅ news_{idx}.jpg saved")

# ---------------- Main ---------------- #

def main():
    with open("output/content.json", "r", encoding="utf-8") as f:
        content = json.load(f)
    with open("output/scraped_articles.json", "r", encoding="utf-8") as f:
        arts = json.load(f)

    threads = content.get("instagram", {}).get("threads", [])
    articles = threads[1:11]  # skip index thread
    sources = [a.get("source", "") for a in arts]

    today = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d-%m-%Y")
    folder = f"instagram-images-{today}"
    os.makedirs(folder, exist_ok=True)

    print(f"Loaded {len(articles)} articles, {len(sources)} sources")

    # index.jpg
    headlines = [a.get("heading", f"Article {i+1}") for i, a in enumerate(articles)]
    generate_index(today, headlines, os.path.join(folder, "index.jpg"))

    # news_1..news_10
    n = min(len(articles), 10)
    for i in range(n):
        a = articles[i]
        src = sources[i] if i < len(sources) else ""
        generate_card(
            i+1,
            a.get("heading", f"Article {i+1}"),
            a.get("summary", "No summary available"),
            src,
            os.path.join(folder, f"news{i+1}.jpg")
        )

    print(f"🎉 All {n+1} images saved in {folder} (BIG clear fonts, no links!)")

if __name__ == "__main__":
    main()