"""
agents/report_agent.py
Agent 2 – Competitor Report Generator

Takes structured research data from Agent 1 and produces a full Markdown
competitor intelligence report saved to output/competitor_report.md.
"""

import json
from datetime import date
from pathlib import Path
from rich.console import Console
from tools.openrouter_client import chat

console = Console()
OUTPUT_PATH = Path("output/competitor_report.md")


def run(research: dict) -> str:
    """
    research: output dict from research_agent.run()
    Returns the Markdown report as a string (also saved to file).
    """
    console.rule("[bold cyan]Agent 2 – Competitor Report")

    system_prompt = (
        "You are a senior product marketing strategist. "
        "Write a clear, professional competitor intelligence report in Markdown. "
        "Be specific and actionable. No fluff."
    )

    user_prompt = f"""
Write a competitor intelligence report for CrowdWisdomTrading based on this research.

RESEARCH DATA:
{json.dumps(research, indent=2)}

The report must include these sections:
1. **Executive Summary** (3-4 sentences — what is CWT, who it's for, key advantage)
2. **Product Overview** (features, pricing, target audience, channels)
3. **Competitor Landscape** (table + narrative for each key competitor)
4. **Feature Comparison Matrix** (markdown table: CWT vs top 4 competitors)
5. **Pricing Comparison** (what does the market charge?)
6. **CWT's Positioning Opportunities** (3-5 actionable gaps CWT can exploit)
7. **Recommended Messaging** (3 headline + subheadline pairs for ads/landing pages)

Today's date: {date.today().isoformat()}

Use clean Markdown. No JSON in output.
"""

    report_md = chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=3000,
    )

    # Save report
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(f"# CrowdWisdomTrading – Competitor Intelligence Report\n\n")
        f.write(f"*Generated: {date.today().isoformat()}*\n\n---\n\n")
        f.write(report_md)

    console.log(f"[green]✓[/green] Report saved → {OUTPUT_PATH}")
    return report_md
