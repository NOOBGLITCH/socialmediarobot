
# Tech/AI News Automation Bot

<p align="center">
  <img width="800" height="400" src="https://github.com/user-attachments/assets/f477be77-d023-425e-9cab-23b1aef642eb" alt="image" />
</p>


<h2 align="center">
  🔗 <a href="https://deepwiki.com/NOOBGLITCH/socialmediarobot/1-overview">View the DeepWiki Overview</a>
</h2>

# Project Overview

## 🚀 Problem
- News spreads fast; teams struggle to **curate, summarize, format, and publish** across platforms.
- Manual posting is **slow, inconsistent, and resource-heavy**.
- Small teams or creators **can’t scale content efficiently**.

---

## 💡 Solution
An **AI-powered automation pipeline** that:
1. Scrapes **RSS feeds** for top tech/AI news.
2. Generates **summaries & headlines** via **Gemini API**.
3. Auto-posts to **Twitter/X as threads** (1 index + 10 detailed).
4. Fully automated via **GitHub Actions** — **no human intervention**.
5. Supports **custom fonts, branding, and optimized summary length**.

---

## ⚙️ Features
- **Daily automation** at **7 PM IST**.
- **Error handling** and **rate-limit management**.
- **Adaptive content formatting** for high readability and engagement.
- **Modular, scalable architecture** for future platforms.

---

## 📁 Core Structure
```
tech-ai-news-automation/
├─ .github/workflows/pipeline.yml   # GitHub Actions pipeline
├─ src/
│   ├─ rss_scraper.py               # News scraping & filtering
│   ├─ gemini_api.py                # AI content generation
│   └─ twitter.py                   # Auto-posting threads
├─ data/rss.xlsx                     # Feed sources
└─ requirements.txt                  # Dependencies
```

---

## 🛠️ Setup (Private Use Only)
**Private Fork Only** – **do NOT publish public repos**.

### Requirements
- **GitHub Account**: For hosting the repository and running Actions.
- **Python 3.11+**: For local testing.
- **API Keys**:
  - **Gemini API** (Google AI Studio).
  - **Twitter/X OAuth1** (Developer Portal, Free tier).
- **rss.xlsx**: Excel file with columns **"Names"** and **"RSS Links"** (e.g., TechCrunch: `https://techcrunch.com/feed/`).

---

### Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/NOOBGLITCH/socialmediabot
   cd socialmediabot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure `rss.xlsx`**:
   Add RSS feeds to `data/rss.xlsx`:
   ```
   Names        | RSS Links
   TechCrunch   | https://techcrunch.com/feed/
   Ars Technica | https://arstechnica.com/feed/
   ```

4. **Test Locally**:
   - Set environment variables:
     ```bash
     export GEMINI_API_KEY="your-key"
     # Add other Twitter/X secrets
     ```
   - Run scripts:
     ```bash
     python src/rss_scraper.py
     python src/twitter.py
     ```
   - Check your **Twitter/X posts**.

---

## 📈 Future Roadmap
- **Full Automation & Zero Human Interaction**:
  Pipeline runs **completely hands-free** with GitHub Actions.
- **Custom Fonts & Branding**:
  Consistent visual style and identity across all posts.
- **Summary Length & Optimization**:
  Adaptive AI-generated summaries tailored for engagement and readability.

---

## 🎯 Impact
- Teams **save hours daily**, focusing on high-value work.
- Content is **always timely, branded, and engaging**.
- Demonstrates **Agentic AI** in real-world publishing workflows.

---

### ⚠️ Strict Warning
- **Private use only** – **do not fork publicly**.
- **API keys must never be committed to GitHub**.
- **Misuse may lead to API bans**.
- **Social Media Spamming Restrictions**:
  - Do **not** use this bot for spamming, unsolicited promotions, or violating Twitter/X’s [Automation Rules](https://help.twitter.com/en/rules-and-policies/twitter-automation).
  - Ensure all posted content complies with platform guidelines.
  - **Restrict accounts** to authorized users only. Unauthorized or automated abuse may result in **account suspension or legal action**.


---

## 🤝 Contributing
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/new-feature
   ```
5. Open a **Pull Request**.
6. **Feel free to contribute!** Your ideas and improvements are welcome.

---

### 📧 Contact
For **issues, suggestions, or feedback**, please:
- Open an **issue** in the repository.
- Contact **NOOBGLITCH** directly.
---
