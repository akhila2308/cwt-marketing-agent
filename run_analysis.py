"""
run_analysis.py
Quick runner for Agents 1 + 2 only (Research + Report).
No Reddit credentials needed — useful for testing and demo.

Usage:
    python run_analysis.py
"""

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from agents import research_agent, report_agent

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]CWT Analysis Mode[/bold cyan]\n"
        "Agents: Research + Competitor Report only\n"
        "No Reddit credentials required.",
        title="🔍 Analysis Pipeline"
    ))

    console.print("\n[bold]Step 1/2:[/bold] Running research agent...")
    research = research_agent.run()

    console.print(f"\n[green]✓[/green] Found {len(research.get('competitors', []))} competitors")
    console.print(f"[green]✓[/green] Extracted {len(research.get('cwt_facts', []))} product facts")

    console.print("\n[bold]Step 2/2:[/bold] Generating competitor report...")
    report_agent.run(research)

    console.print("\n[bold green]Done![/bold green]")
    console.print("  📄 Report saved → output/competitor_report.md")
    console.print("\n[dim]Run 'python main.py' for the full pipeline including Reddit replies.[/dim]")


if __name__ == "__main__":
    main()
