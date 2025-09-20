# Tech/AI News Automation (Twitter/X)

This repository automates the posting of tech and AI news to **Twitter/X** using RSS feeds from an Excel file (`rss.xlsx`). The workflow runs daily at **7 PM IST**, fetching news from the current day (12 AM to 7 PM IST), generating catchy headlines and summaries with the **Gemini API**, and posting 11 threads (1 index with top 10 headlines + 10 news threads).

The pipeline is powered by **GitHub Actions**, ensuring reliable automation.

## Features

  - **RSS Scraping**: Fetches news from RSS feeds listed in `rss.xlsx`.
  - **Content Generation**: Uses Gemini API for SEO-friendly headlines and summaries.
  - **Social Media Posting**:
      - Twitter/X: 11 threads (\~30 tweets, under 50/day limit).
  - **Scheduling**: Runs daily at 7 PM IST (13:30 UTC) via GitHub Actions.
  - **Error Handling**: Logs errors and handles rate limits (e.g., 429 errors).

## File Structure

```
tech-ai-news-automation/
├── .github/
│   └── workflows/
│       └── pipeline.yml            # GitHub Actions pipeline
├── src/
│   ├── rss_scraper.py              # RSS feed scraping and filtering
│   ├── twitter.py                  # Twitter/X thread posting
│   ├── gemini_api.py               # Gemini API for content generation
│   └── utils.py                    # Shared utilities (e.g., date handling)
├── data/
│   └── rss.xlsx                    # RSS feed sources (Names, RSS Links)
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Prerequisites

  - **GitHub Account**: For hosting the repository and running Actions.
  - **Python 3.11+**: For local testing.
  - **API Keys**:
      - Gemini API (Google AI Studio).
      - Twitter/X OAuth1 (Developer Portal, Free tier).
  - **rss.xlsx**: Excel file with columns “Names” and “RSS Links” (e.g., TechCrunch: `https://techcrunch.com/feed/`).

## Setup

1.  **Clone the Repository**:

    ```bash
    git clone https://NOOBGLITCH/socialmediabot
    cd socialmediabot
    ```

2.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure rss.xlsx**:

      - Add RSS feeds to `data/rss.xlsx`:

        ```excel
        Names        | RSS Links
        TechCrunch   | https://techcrunch.com/feed/
        Ars Technica | https://arstechnica.com/feed/
        ```

4.  **Set Up GitHub Actions Secrets**:

      - Go to **Settings \> Secrets and variables \> Actions \> New repository secret**.
      - Add:
          - `GEMINI_API_KEY`: Gemini API key.
          - `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`: Twitter/X credentials.

5.  **Test Locally**:

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

      - Check your Twitter/X posts.

6.  **Deploy Pipeline**:

      - Push changes:

        ```bash
        git add .
        git commit -m "Initial setup"
        git push origin main
        ```

      - The pipeline runs daily at 7 PM IST (13:30 UTC).

      - Trigger manually: **Actions \> Tech AI News Automation \> Run workflow**.

## Usage

  - **Daily Automation**: The pipeline fetches RSS feeds, generates content, and posts to Twitter/X at 7 PM IST.
  - **Output**:
      - **Twitter/X**: 1 index thread (top 10 headlines) + 10 news threads.
  - **Monitoring**: Check Actions logs for errors (e.g., rate limits, API issues).
  - **Rate Limits**:
      - Twitter/X: \~30 tweets (under 50/day).

## Example Output

For May 22, 2025:

  - **Twitter/X**:
      - Index: “Top 10 Tech/AI Headlines - May 22, 2025: 1. AI Startup Raises $100M … \#Tech \#AI”
      - Thread 1: “AI Startup Raises $100M 🚀 $100M to scale robotics. \#AI \#Tech”

## Troubleshooting

  - **API Errors**: Verify API keys and rate limits in Actions logs.
  - **Pipeline Failures**: Check logs for missing secrets or RSS feed errors.
  - **Bans**: Avoid spammy posts; appeal via X Developer Portal if flagged.

## Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/new-feature`).
3.  Commit changes (`git commit -m "Add new feature"`).
4.  Push to the branch (`git push origin feature/new-feature`).
5.  Open a Pull Request.

## License

MIT License. See LICENSE for details.

## Contact

For issues or suggestions, open an issue or contact NOOBGLITCH.

-----

Would you like any further modifications or have more questions about setting this up?
