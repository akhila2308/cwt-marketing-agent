"""
agents/learning_loop.py
Agent 4 – Closed Learning Loop (Hermes Reflection Pattern)

After each pipeline run, this agent:
1. Reviews what happened this run (research findings, replies generated)
2. Reflects on quality and suggests improvements
3. Updates persistent memory.json with actionable notes
4. These notes are loaded by other agents on the NEXT run, creating a feedback loop

This implements the Hermes "reflection" pattern:
  generate → critique → refine → store → reuse
"""

import json
from rich.console import Console
from tools.openrouter_client import chat
from tools.storage import load_memory, save_memory, append_run

console = Console()


def run(research: dict, replies: list[dict]) -> dict:
    """
    research: output from research_agent
    replies: output from reddit_agent

    Returns updated memory dict.
    """
    console.rule("[bold cyan]Agent 4 – Closed Learning Loop")

    memory = load_memory()

    # ── Step 1: Build a run summary ──────────────────────────────────────────
    run_summary = {
        "competitors_found": len(research.get("competitors", [])),
        "posts_targeted": len(replies),
        "replies_posted": sum(1 for r in replies if r.get("posted")),
        "subreddits_targeted": list({r.get("subreddit") for r in replies}),
    }

    # ── Step 2: LLM reflection on this run ──────────────────────────────────
    reflection_prompt = f"""
You are a marketing AI reflecting on a completed outreach run. Analyze quality and extract learnings.

=== THIS RUN ===
Competitors found: {json.dumps(research.get('competitors', []), indent=2)}
Market observations: {json.dumps(research.get('market_observations', []), indent=2)}
Reddit replies generated:
{json.dumps([{{"post_title": r["post_title"], "subreddit": r["subreddit"], "reply": r["reply_text"], "score": r["relevance_score"]}} for r in replies], indent=2)}

=== CURRENT MEMORY (from previous runs) ===
{json.dumps(memory, indent=2)}

Reflect on this run and return a JSON object:
{{
  "reply_style_notes": [
    // 2-3 notes about what reply styles/approaches worked or should be tried next time
    // Example: "r/Daytrading responds better to brief, data-focused replies"
  ],
  "subreddit_notes": {{
    // "subreddit_name": "note about tone/approach that works here"
  }},
  "competitor_intel_updates": {{
    // competitor name → updated fact/note if anything new was learned
  }},
  "next_run_improvements": [
    // 2-3 specific things the pipeline should do differently next run
  ],
  "run_quality_score": 0-10,
  "run_quality_reason": "..."
}}

IMPORTANT: Be specific and actionable. Generic advice like "be more helpful" is not useful.
Return ONLY valid JSON.
"""

    console.log("[bold]LLM[/bold] Reflecting on run quality...")
    raw = chat(
        messages=[{"role": "user", "content": reflection_prompt}],
        temperature=0.4,
        max_tokens=1000,
    )

    try:
        reflection = json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        reflection = json.loads(match.group()) if match else {}

    # ── Step 3: Merge reflection into memory ─────────────────────────────────
    # Append new style notes (keep last 10)
    new_notes = reflection.get("reply_style_notes", [])
    memory["reply_style_notes"] = (memory.get("reply_style_notes", []) + new_notes)[-10:]

    # Merge subreddit notes
    for sub, note in reflection.get("subreddit_notes", {}).items():
        memory.setdefault("subreddit_notes", {})[sub] = note

    # Update competitor intel
    for comp, fact in reflection.get("competitor_intel_updates", {}).items():
        memory.setdefault("competitor_intel", {})[comp] = fact

    # Save updated memory
    save_memory(memory)

    # Append compact run summary to run history
    append_run({
        **run_summary,
        "quality_score": reflection.get("run_quality_score"),
        "improvements_noted": reflection.get("next_run_improvements", []),
    })

    console.log(
        f"[green]✓[/green] Learning loop complete. "
        f"Quality score: {reflection.get('run_quality_score', '?')}/10"
    )
    console.log(f"  [dim]Memory updated → output/memory.json[/dim]")

    return memory
