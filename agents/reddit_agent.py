"""
agents/reddit_agent.py
Agent 3 – Reddit Pain-Point Finder + Human-Style Reply Drafter

Steps:
1. Search Reddit for posts expressing pain points CWT solves
2. Score and rank posts by relevance + pain intensity
3. Generate 3-5 value-first, non-spammy replies (diverse tone/style)
4. Post replies via PRAW (with dry_run=True by default for safety)
"""

import json
import os
import time
import praw
from datetime import datetime
from pathlib import Path
from rich.console import Console
from tools.apify_tools import search_reddit
from tools.openrouter_client import chat
from tools.storage import load_memory

console = Console()
OUTPUT_PATH = Path("output/reddit_replies.json")

# Pain-point keywords that map to problems CWT solves
PAIN_KEYWORDS = [
    "too many trading YouTubers",
    "information overload trading",
    "don't know which traders to follow",
    "waste hours watching finance YouTube",
    "can't keep up with market news",
    "too much noise in stock market",
    "which trading signal to trust",
    "contradictory trading advice",
    "spending too much time on research",
]

TARGET_SUBREDDITS = [
    "Daytrading",
    "stocks",
    "investing",
    "StockMarket",
    "algotrading",
    "Forex",
    "Crypto_Currency",
    "personalfinance",
]

ANTI_SPAM_RULES = """
CRITICAL ANTI-SPAM RULES (you MUST follow all of these):
1. DO NOT paste a product URL in the reply unless it feels completely natural and the post is a direct recommendation request.
2. Start by acknowledging the person's specific pain point — show you actually read their post.
3. Be helpful first: give real advice or a tip that stands on its own.
4. Only mention CrowdWisdomTrading as "I use a tool called..." naturally, NOT as an advertisement.
5. Vary tone: some replies are casual/conversational, some are slightly more detailed. Never use the same opener twice.
6. Max 150 words per reply. Sound like a real Reddit user, not a marketer.
7. NEVER use phrases like "Check out", "game changer", "revolutionary", or other marketing speak.
"""


def run(dry_run: bool = True) -> list[dict]:
    """
    dry_run=True: generates replies and saves to file but does NOT post to Reddit.
    dry_run=False: actually posts. Use with caution.

    Returns list of reply dicts.
    """
    console.rule("[bold cyan]Agent 3 – Reddit Pain-Point Finder")

    # ── Load learning memory for improved targeting ──────────────────────────
    memory = load_memory()
    subreddit_notes = memory.get("subreddit_notes", {})
    style_notes = memory.get("reply_style_notes", [])

    # ── Step 1: Scrape Reddit for pain-point posts ───────────────────────────
    posts = search_reddit(
        keywords=PAIN_KEYWORDS[:5],  # top 5 to keep Apify usage lean
        subreddits=TARGET_SUBREDDITS,
        max_posts=40,
        sort="relevance",
    )

    if not posts:
        console.log("[yellow]⚠[/yellow] No Reddit posts found. Check Apify token / keywords.")
        return []

    # ── Step 2: LLM scores and selects best posts ────────────────────────────
    posts_json = json.dumps(posts[:30], indent=2)
    memory_context = f"Subreddit notes: {json.dumps(subreddit_notes)}\nStyle notes: {style_notes}"

    scoring_prompt = f"""
You are a product marketer finding Reddit posts where CrowdWisdomTrading would genuinely help.

CrowdWisdomTrading = AI newsletter that aggregates insights from 1,000+ traders (YouTube, Reddit, X) 
into weekly actionable signals. It saves traders 50+ hours/week. $20/month.

REDDIT POSTS:
{posts_json}

MEMORY FROM PREVIOUS RUNS:
{memory_context}

Select the 5 best posts to reply to. Score on:
- Pain point clarity (does the person clearly suffer from information overload or signal confusion?)
- Recency (newer = better)
- Engagement (upvotes + comments = more visibility)
- Reply opportunity (is the thread still active? would a reply feel natural?)

Return ONLY a JSON array of the selected post IDs with scores:
[{{"id": "...", "url": "...", "title": "...", "pain_summary": "...", "score": 0-10}}]
"""

    console.log("[bold]LLM[/bold] Scoring posts...")
    raw_scores = chat(
        messages=[{"role": "user", "content": scoring_prompt}],
        temperature=0.2,
        max_tokens=800,
    )

    try:
        selected = json.loads(raw_scores)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', raw_scores, re.DOTALL)
        selected = json.loads(match.group()) if match else []

    selected = selected[:5]
    console.log(f"[green]✓[/green] Selected {len(selected)} posts for replies")

    # ── Step 3: Generate diverse, human-style replies ────────────────────────
    post_lookup = {p["id"]: p for p in posts}
    replies = []

    reply_styles = [
        "casual Reddit user who trades part-time",
        "slightly technical, been trading for 5 years",
        "empathetic, shares personal experience",
        "concise and direct, no-nonsense",
        "thoughtful, gives real actionable advice",
    ]

    for i, sel in enumerate(selected):
        post = post_lookup.get(sel.get("id"), sel)
        style = reply_styles[i % len(reply_styles)]

        reply_prompt = f"""
{ANTI_SPAM_RULES}

Write a Reddit reply to this post. You are: {style}.

POST TITLE: {post.get('title', '')}
POST BODY: {post.get('selftext', '')[:600]}
SUBREDDIT: r/{post.get('subreddit', '')}
PAIN POINT: {sel.get('pain_summary', '')}

The reply should feel 100% natural for Reddit. Helpful first, CWT mention only if it flows naturally.
Return ONLY the reply text, nothing else.
"""

        reply_text = chat(
            messages=[{"role": "user", "content": reply_prompt}],
            temperature=0.85,
            max_tokens=300,
        )

        replies.append({
            "post_id": post.get("id", ""),
            "post_url": post.get("url", ""),
            "subreddit": post.get("subreddit", ""),
            "post_title": post.get("title", ""),
            "pain_summary": sel.get("pain_summary", ""),
            "reply_text": reply_text.strip(),
            "style": style,
            "relevance_score": sel.get("score", 0),
            "posted": False,
            "posted_at": None,
        })

    # ── Step 4: Optionally post to Reddit ────────────────────────────────────
    if not dry_run:
        reddit = _get_reddit_client()
        for reply_data in replies:
            try:
                submission = reddit.submission(url=reply_data["post_url"])
                comment = submission.reply(reply_data["reply_text"])
                reply_data["posted"] = True
                reply_data["posted_at"] = datetime.utcnow().isoformat()
                reply_data["comment_url"] = f"https://reddit.com{comment.permalink}"
                console.log(f"[green]✓ Posted[/green] → {reply_data['comment_url']}")
                time.sleep(30)  # Rate limit: Reddit enforces 1 comment per 10min for new accounts
            except Exception as e:
                console.log(f"[red]✗ Failed to post[/red]: {e}")
                reply_data["error"] = str(e)
    else:
        console.log("[yellow]DRY RUN[/yellow] – replies generated but NOT posted. Set dry_run=False to post.")

    # ── Save output ───────────────────────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(replies, f, indent=2)

    console.log(f"[green]✓[/green] {len(replies)} replies saved → {OUTPUT_PATH}")
    return replies


def _get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "cwt-marketing-bot/0.1"),
    )
