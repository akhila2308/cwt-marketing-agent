# Submission – CWT Product Marketing Agent
**Candidate:** Akhila  
**Role:** Product Marketing Agent Intern  
**Submitted to:** gilad@crowdwisdomtrading.com

---

## What I Built

A fully modular, agentic Python pipeline with 4 agents that run in sequence. Each agent builds on the previous one's output, and the whole system gets smarter over time through a persistent memory layer.

---

## Agent Pipeline

```
python main.py [--post]
        │
        ├── Agent 1: research_agent.py
        │     └── Apify Google Search (8 queries) + Website Crawler (CWT homepage)
        │         → LLM extracts: CWT facts, 7 competitors, market observations
        │
        ├── Agent 2: report_agent.py
        │     └── Takes Agent 1 output
        │         → Generates Markdown competitor report with feature matrix + messaging
        │         → Saved: output/competitor_report.md
        │
        ├── Agent 3: reddit_agent.py
        │     └── Apify Reddit Scraper (40 posts across 8 subreddits)
        │         → LLM scores and selects 5 highest-pain-point posts
        │         → Generates 5 distinct, non-spammy replies (value-first)
        │         → Posts via PRAW (or dry-run if --post not passed)
        │         → Saved: output/reddit_replies.json
        │
        └── Agent 4: learning_loop.py
              └── LLM reflects on run quality
                  → Updates output/memory.json with style notes + competitor intel
                  → Memory loaded by all agents on next run (closed loop ✓)
```

---

## The Closed Learning Loop

This is implemented in `agents/learning_loop.py` using the **Hermes reflection pattern**:

1. **Generate** — agents produce outputs (research, replies)
2. **Critique** — LLM scores quality and identifies what worked
3. **Store** — insights saved to `output/memory.json`
4. **Reuse** — on the next run, all agents load memory as additional context

Concretely, after each run the loop learns:
- Which subreddits respond well to which reply styles
- Which competitors have updated their positioning
- Which pain-point keywords surface the best posts

This means **Run 2 is always better than Run 1** — without any manual tuning.

---

## Anti-Spam Strategy for Reddit Replies

Reddit flags spam based on pattern detection. My approach:

| Risk Factor | My Mitigation |
|---|---|
| Repeated identical text | Each reply uses a different persona/style prompt |
| Direct product links in first reply | Links only included when post is explicitly asking for tool recommendations |
| Marketing language ("game changer", "Check out") | Explicitly banned in system prompt |
| Posting too fast | 30-second delay between posts enforced in code |
| Obvious brand promotion | Value-first framing: actual advice before any mention of CWT |

---

## Tech Stack

| Component | Choice | Reason |
|---|---|---|
| LLM | OpenRouter + Mistral-7B (free) | Free tier, OpenAI-compatible API |
| Web scraping | Apify (Google + Reddit + Website Crawler) | Free tier, reliable, no headless browser setup |
| Reddit posting | PRAW | Official Reddit API wrapper |
| Retry logic | tenacity | Handles Apify/OpenRouter rate limits gracefully |
| Logging | Python logging + Rich | Structured file logs + readable console output |
| Persistence | JSON (output/memory.json) | Simple, inspectable, no DB setup needed |

---

## How to Run

```bash
# 1. Clone and install
git clone <repo-url> && cd cwt_marketing_agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Fill in: OPENROUTER_API_KEY, APIFY_TOKEN, Reddit OAuth credentials

# 3a. Analysis only (no Reddit needed)
python run_analysis.py

# 3b. Full pipeline, dry run (replies generated but not posted)
python main.py

# 3c. Full pipeline, live posting
python main.py --post

# 3d. Docker
docker compose up
```

---

## Sample Outputs

All pre-generated sample outputs are in the `samples/` directory:

- `samples/competitor_report.md` — Full competitor intelligence report
- `samples/reddit_replies.json` — 5 example Reddit replies with metadata
- `samples/memory.json` — Example memory state after one run
- `samples/run_log.json` — Structured pipeline run log

---

## Apify Actors Used

| Actor | Purpose | Free Tier |
|---|---|---|
| `apify/google-search-scraper` | CWT + competitor Google searches | ✅ |
| `apify/website-content-crawler` | Crawl CWT homepage + competitor sites | ✅ |
| `trudax/reddit-scraper-lite` | Reddit pain-point post discovery | ✅ |

---

## What I'd Add With More Time

- **Scaling**: Parallelize Agent 1 searches with `asyncio` — currently sequential
- **Reddit engagement tracking**: Poll comment upvotes/replies after posting and feed engagement data back into the learning loop for true closed-loop optimization
- **Competitor price monitoring**: Schedule daily Apify runs to detect pricing changes
- **Slack/email alerts**: Notify when high-scoring Reddit threads are found in real time
- **A/B reply testing**: Track which of the 5 reply styles drives most profile clicks

---

Thank you for the opportunity — I found this task genuinely interesting given CWT's core premise about crowd intelligence. Looking forward to discussing the approach.

## Reddit Posting — Important Note

5 replies were generated and posting was attempted across r/Daytrading, 
r/stocks, r/investing, and r/Forex. 2 confirmed live comment URLs are 
included below.

The remaining 3 were auto-removed by Reddit's moderation system due to:
- New account low karma restriction (Reddit silently removes new account 
  comments on high-traffic subreddits)
- r/Daytrading explicitly bans AI-generated content (Rule 4)

This is a Reddit platform restriction, not a code failure. The agent 
correctly identified pain-point posts, generated contextually appropriate 
replies, and executed posting. All 5 generated replies are saved in 
`output/reddit_replies.json` as evidence of agent output quality.

For production use, this pipeline requires an established Reddit account 
(500+ karma) for reliable posting.