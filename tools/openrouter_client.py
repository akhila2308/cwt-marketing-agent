"""
tools/openrouter_client.py
LLM client with automatic model fallback.
Tries multiple free models in sequence — if one is rate-limited or unavailable,
it automatically falls back to the next one.
"""

import os
import time
from openai import OpenAI
from rich.console import Console

console = Console()

# Free models tried in order — first available wins
FREE_MODEL_FALLBACK = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "microsoft/phi-4-reasoning-plus:free",
    "google/gemma-3-27b-it:free",
    "mistralai/devstral-small:free",
    "openrouter/auto",  # last resort: OpenRouter picks for us
]

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENROUTER_API_KEY is not set.")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    return _client


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: dict | None = None,
) -> str:
    """
    Send a chat completion request. If the specified model fails,
    automatically falls back through FREE_MODEL_FALLBACK list.
    """
    client = get_client()

    # Build list of models to try
    env_model = os.getenv("LLM_MODEL")
    models_to_try = []
    if model:
        models_to_try.append(model)
    elif env_model and env_model not in FREE_MODEL_FALLBACK:
        models_to_try.append(env_model)
    models_to_try.extend(FREE_MODEL_FALLBACK)

    # Deduplicate while preserving order
    seen = set()
    unique_models = []
    for m in models_to_try:
        if m not in seen:
            seen.add(m)
            unique_models.append(m)

    last_error = None
    for attempt_model in unique_models:
        try:
            console.log(f"[dim]LLM attempting:[/dim] {attempt_model}")

            kwargs = dict(
                model=attempt_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response_format:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            console.log(f"[green]✓ LLM[/green] {attempt_model} → {len(content)} chars")
            return content

        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["404", "429", "503", "rate", "quota", "not found"]):
                console.log(f"[yellow]⚠ {attempt_model} unavailable ({err_str[:80]}), trying next...[/yellow]")
                last_error = e
                time.sleep(2)  # brief pause before next attempt
                continue
            else:
                raise  # non-rate-limit error — don't retry

    raise RuntimeError(f"All models exhausted. Last error: {last_error}")