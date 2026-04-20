"""
tools/apify_tools.py
Wrappers around Apify Actors used by the marketing agents.
All Actors used have free-tier availability.
"""

import os
import time
from apify_client import ApifyClient
from rich.console import Console
from tenacity import retry, stop_after_attempt, wait_exponential

console = Console()


def _get_client() -> ApifyClient:
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise EnvironmentError("APIFY_TOKEN is not set.")
    return ApifyClient(token)


# ─────────────────────────────────────────────
# Google Search Scraper
# Actor: apify/google-search-scraper
# ─────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
def google_search(queries: list[str], results_per_query: int = 10) -> list[dict]:
    """
    Run Google searches via Apify and return flat list of result dicts.
    Each dict has: title, url, description.
    """
    client = _get_client()
    console.log(f"[cyan]Apify[/cyan] Google search: {queries}")

    run_input = {
        "queries": "\n".join(queries),
        "resultsPerPage": results_per_query,
        "maxPagesPerQuery": 1,
    }
    run = client.actor("apify/google-search-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    results = []
    for item in items:
        for organic in item.get("organicResults", []):
            results.append({
                "title": organic.get("title", ""),
                "url": organic.get("url", ""),
                "description": organic.get("description", ""),
            })
    console.log(f"[cyan]Apify[/cyan] Google → {len(results)} results")
    return results


# ─────────────────────────────────────────────
# Website Content Crawler
# Actor: apify/website-content-crawler
# ─────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
def scrape_website(url: str, max_pages: int = 5) -> list[dict]:
    """
    Crawl a website and return a list of {url, title, text} dicts.
    """
    client = _get_client()
    console.log(f"[cyan]Apify[/cyan] Crawling: {url}")

    run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": max_pages,
        "crawlerType": "cheerio",
    }
    run = client.actor("apify/website-content-crawler").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    results = [
        {
            "url": item.get("url", ""),
            "title": item.get("metadata", {}).get("title", ""),
            "text": (item.get("text") or "")[:3000],  # truncate to keep tokens sane
        }
        for item in items
        if item.get("text")
    ]
    console.log(f"[cyan]Apify[/cyan] Crawl → {len(results)} pages")
    return results


# ─────────────────────────────────────────────
# Reddit Scraper
# Actor: trudax/reddit-scraper-lite  (free tier)
# ─────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
def search_reddit(
    keywords: list[str],
    subreddits: list[str] | None = None,
    max_posts: int = 30,
    sort: str = "relevance",
) -> list[dict]:
    """
    Search Reddit for posts matching keywords.
    Returns list of {id, title, selftext, subreddit, url, score, num_comments, created_utc}.
    """
    client = _get_client()
    query = " OR ".join(f'"{kw}"' for kw in keywords)
    # Add subreddit filter inline if provided
    if subreddits:
        sub_filter = " ".join(f"subreddit:{s}" for s in subreddits[:4])
        query = f"{query} ({sub_filter})"
    console.log(f"[cyan]Apify[/cyan] Reddit search: {query}")

    # trudax/reddit-scraper-lite expects "searches" as array of strings
    run_input = {
        "searches": [query],
        "maxItems": max_posts,
        "proxy": {"useApifyProxy": True},
        "sort": sort,
    }

    run = client.actor("trudax/reddit-scraper-lite").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

    results = []
    for item in items:
        if item.get("dataType") == "post":
            results.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "selftext": (item.get("body") or "")[:1500],
                "subreddit": item.get("communityName", ""),
                "url": item.get("url", ""),
                "score": item.get("numberOfUpvotes", 0),
                "num_comments": item.get("numberOfComments", 0),
                "created_utc": item.get("createdAt", ""),
            })

    console.log(f"[cyan]Apify[/cyan] Reddit → {len(results)} posts")
    return results