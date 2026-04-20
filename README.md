# CWT Product Marketing Agent

An agentic pipeline that does competitive intelligence, pain-point discovery, and
Reddit outreach for [CrowdWisdomTrading](https://www.crowdwisdomtrading.com/).

## Architecture

```
main.py
├── agents/
│   ├── research_agent.py      # Agent 1 – product & competitor research (Apify + OpenRouter)
│   ├── report_agent.py        # Agent 2 – structured competitor report
│   ├── reddit_agent.py        # Agent 3 – pain-point finder + 3-5 human replies
│   └── learning_loop.py       # Agent 4 – closed learning loop (Hermes reflection)
├── tools/
│   ├── apify_tools.py         # Apify Actor wrappers (Google Search, Reddit scraper)
│   ├── openrouter_client.py   # OpenRouter LLM client
│   └── storage.py             # JSON persistence for the learning loop
├── output/                    # Auto-generated reports and reply drafts
├── logs/                      # Structured run logs
└── samples/                   # Pre-generated sample I/O (included in repo)
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys
python main.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter key (free tier works) |
| `APIFY_TOKEN` | Apify token (free tier works) |
| `REDDIT_CLIENT_ID` | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit OAuth app secret |
| `REDDIT_USERNAME` | Reddit account username |
| `REDDIT_PASSWORD` | Reddit account password |
| `REDDIT_USER_AGENT` | e.g. `cwt-marketing-bot/0.1` |

## Agents

### Agent 1 – Research Agent
- Uses Apify's **Google Search Scraper** to find CrowdWisdomTrading pages, press mentions, and competitor products.
- Uses Apify's **Website Content Crawler** to scrape competitor landing pages.
- Passes raw data to the LLM to extract structured product facts.

### Agent 2 – Competitor Report Agent
- Takes Agent 1's structured facts.
- Generates a Markdown report covering: product overview, competitors, feature gaps, pricing comparison, positioning opportunities.
- Saves to `output/competitor_report.md`.

### Agent 3 – Reddit Pain-Point + Reply Agent
- Searches Reddit (via Apify Reddit Scraper) for posts expressing pain points CWT solves:
  - information overload for traders
  - too much time spent watching YouTube finance videos
  - inability to know which trader signals to trust
- Scores posts by recency, upvotes, and pain-point relevance.
- Drafts 3-5 distinct, non-spammy replies — each tailored to the original post's tone (helpful commenter, not advertiser).
- Anti-spam rules enforced in the prompt: no direct product links in first reply, value-first framing, natural language variation.

### Agent 4 – Closed Learning Loop
- After each run, the LLM reflects on which replies got engagement (or would likely get engagement).
- Updates a `memory.json` with preferred reply styles, subreddit-specific tone notes, and competitor intel freshness.
- Next run loads this memory and improves automatically — this is the Hermes reflection pattern.

## Sample Output

See `samples/` for:
- `competitor_report.md` – full example report
- `reddit_replies.json` – 5 sample replies with rationale
- `run_log.json` – structured log of a complete run
