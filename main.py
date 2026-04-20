"""
main.py
CWT Product Marketing Agent Pipeline Orchestrator

Run: python main.py [--post]
  --post  Actually post the Reddit replies (default is dry-run)
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

from agents import research_agent, report_agent, reddit_agent, learning_loop

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"run_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

console = Console()


def main():
    dry_run = "--post" not in sys.argv

    console.print(Panel.fit(
        "[bold cyan]CWT Product Marketing Agent[/bold cyan]\n"
        f"Mode: {'[yellow]DRY RUN[/yellow] (replies not posted)' if dry_run else '[green]LIVE[/green] (posting to Reddit)'}\n"
        "Target: https://www.crowdwisdomtrading.com/",
        title="🚀 Starting Pipeline",
    ))

    run_log = {"started_at": datetime.utcnow().isoformat(), "agents": {}}

    # ── Agent 1: Research ─────────────────────────────────────────────────────
    console.print("\n")
    research = research_agent.run()
    run_log["agents"]["research"] = {
        "competitors_found": len(research.get("competitors", [])),
        "cwt_facts": len(research.get("cwt_facts", [])),
    }

    # ── Agent 2: Competitor Report ────────────────────────────────────────────
    console.print("\n")
    report_md = report_agent.run(research)
    run_log["agents"]["report"] = {"saved_to": "output/competitor_report.md"}

    # ── Agent 3: Reddit Pain-Point Finder + Replies ───────────────────────────
    console.print("\n")
    replies = reddit_agent.run(dry_run=dry_run)
    run_log["agents"]["reddit"] = {
        "posts_targeted": len(replies),
        "replies_posted": sum(1 for r in replies if r.get("posted")),
    }

    # ── Agent 4: Closed Learning Loop ────────────────────────────────────────
    console.print("\n")
    memory = learning_loop.run(research=research, replies=replies)
    run_log["agents"]["learning_loop"] = {"memory_items": len(memory.get("runs", []))}

    # ── Final summary ─────────────────────────────────────────────────────────
    run_log["finished_at"] = datetime.utcnow().isoformat()

    log_path = LOG_DIR / f"run_summary_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump(run_log, f, indent=2)

    _print_summary(research, replies, dry_run)
    console.print(f"\n[dim]Full log saved → {log_path}[/dim]")


def _print_summary(research: dict, replies: list[dict], dry_run: bool):
    console.print("\n")
    console.print(Panel.fit("[bold green]Pipeline Complete ✓[/bold green]", title="Summary"))

    # Competitor table
    t = Table(title="Competitors Identified", show_header=True, header_style="bold magenta")
    t.add_column("Name", style="cyan")
    t.add_column("Pricing")
    t.add_column("Key Differentiator")
    for c in research.get("competitors", [])[:6]:
        t.add_row(c.get("name", ""), c.get("pricing", ""), c.get("key_differentiator", ""))
    console.print(t)

    # Replies table
    t2 = Table(title=f"Reddit Replies ({'DRY RUN' if dry_run else 'POSTED'})", show_header=True, header_style="bold yellow")
    t2.add_column("Subreddit", style="cyan")
    t2.add_column("Post Title")
    t2.add_column("Score")
    t2.add_column("Posted?")
    for r in replies:
        t2.add_row(
            f"r/{r.get('subreddit', '')}",
            r.get("post_title", "")[:50] + "...",
            str(r.get("relevance_score", "")),
            "✓" if r.get("posted") else "–",
        )
    console.print(t2)

    console.print("\n[bold]Output files:[/bold]")
    console.print("  📄 output/competitor_report.md")
    console.print("  💬 output/reddit_replies.json")
    console.print("  🧠 output/memory.json")


if __name__ == "__main__":
    main()
