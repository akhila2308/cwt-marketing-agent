"""
agents/research_agent.py
Agent 1 – Product & Competitor Research

Steps:
1. Google search for CWT product facts + reviews
2. Google search for competitors
3. Crawl top competitor landing pages
4. LLM extracts structured product intelligence
"""

import json
from rich.console import Console
from tools.apify_tools import google_search, scrape_website
from tools.openrouter_client import chat
from tools.storage import load_memory

console = Console()

TARGET_URL = "https://www.crowdwisdomtrading.com/"

COMPETITOR_SEARCH_QUERIES = [
    "AI trading signals newsletter aggregator",
    "crowdsourced trading predictions platform",
    "trading insights aggregator AI 2024 2025",
    "best trading signal services comparison",
    "fintwit sentiment aggregator tool",
]

CWT_SEARCH_QUERIES = [
    "CrowdWisdomTrading review",
    "site:crowdwisdomtrading.com",
    "CrowdWisdomTrading competitors alternative",
]


def run() -> dict:
    """
    Returns a dict with:
      - cwt_facts: list of strings about the product
      - competitors: list of {name, url, description, pricing}
      - raw_pages: list of scraped page summaries
    """
    console.rule("[bold cyan]Agent 1 – Research")

    # ── Load memory for context ──────────────────────────────────────────────
    memory = load_memory()
    prior_competitors = memory.get("competitor_intel", {})

    # ── Step 1: Search about CWT ─────────────────────────────────────────────
    cwt_results = google_search(CWT_SEARCH_QUERIES, results_per_query=8)

    # ── Step 2: Search for competitors ──────────────────────────────────────
    comp_results = google_search(COMPETITOR_SEARCH_QUERIES, results_per_query=10)

    # ── Step 3: Crawl CWT website ────────────────────────────────────────────
    cwt_pages = scrape_website(TARGET_URL, max_pages=6)

    # ── Step 4: LLM extracts structured intelligence ─────────────────────────
    search_text = _format_search_results(cwt_results + comp_results)
    page_text = _format_pages(cwt_pages)

    system_prompt = (
        "You are a sharp product marketing researcher. "
        "Given raw search results and scraped web pages, extract structured intelligence. "
        "Respond ONLY with valid JSON — no markdown fences, no preamble."
    )

    user_prompt = f"""
Analyze the following data about CrowdWisdomTrading and its market.

SEARCH RESULTS:
{search_text}

SCRAPED PAGES:
{page_text}

PRIOR COMPETITOR INTEL (from previous runs, may be stale):
{json.dumps(prior_competitors, indent=2)}

Return a JSON object with this exact structure:
{{
  "cwt_facts": [
    // 8-12 factual bullets about CrowdWisdomTrading's product, value prop, pricing, features
  ],
  "competitors": [
    {{
      "name": "...",
      "url": "...",
      "description": "one-sentence description",
      "pricing": "free / paid / unknown",
      "key_differentiator": "..."
    }}
    // 5-8 competitors
  ],
  "market_observations": [
    // 3-5 observations about the prediction/trading intelligence market
  ]
}}
"""

    console.log("[bold]LLM[/bold] Extracting structured research...")
    raw = chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Graceful fallback: try to extract JSON block
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"cwt_facts": [], "competitors": [], "market_observations": []}

    result["raw_search_count"] = len(cwt_results) + len(comp_results)
    result["raw_pages_scraped"] = len(cwt_pages)
    console.log(f"[green]✓[/green] Research complete: {len(result.get('competitors', []))} competitors found")
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_search_results(results: list[dict]) -> str:
    lines = []
    for r in results[:40]:  # cap to avoid token blowout
        lines.append(f"- [{r['title']}]({r['url']})\n  {r['description']}")
    return "\n".join(lines)


def _format_pages(pages: list[dict]) -> str:
    parts = []
    for p in pages[:5]:
        parts.append(f"### {p['title']} ({p['url']})\n{p['text'][:800]}")
    return "\n\n".join(parts)
