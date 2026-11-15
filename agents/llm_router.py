"""Resilient 3-tier AI reasoning router: Gemini -> Groq -> Universal Deterministic Fallback."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class SynthesisResult:
    text: str
    provider: str
    model: str
    latency_ms: int
    fallback_used: bool
    notes: str = ""


def resolve_secret(name: str, explicit_value: str | None = None) -> str:
    if explicit_value and explicit_value.strip():
        return explicit_value.strip()
    try:
        import streamlit as st

        if name in st.secrets and str(st.secrets[name]).strip():
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.environ.get(name, "").strip()


def _call_gemini(prompt: str, system_instruction: str, api_key: str) -> tuple[str, str]:
    from google import genai

    client = genai.Client(api_key=api_key)
    for model_name in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-4-hydrogen"):
        try:
            interaction = client.interactions.create(
                model=model_name,
                input=prompt,
                system_instruction=system_instruction,
            )
            text = (interaction.output_text or "").strip()
            if text:
                return text, model_name
        except Exception:
            continue
    raise RuntimeError("All Gemini models failed.")


def _call_groq(prompt: str, system_instruction: str, api_key: str) -> tuple[str, str]:
    from groq import Groq

    client = Groq(api_key=api_key)
    for model_name in ("qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.25,
                max_tokens=550,
            )
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return text, model_name
        except Exception:
            continue
    raise RuntimeError("All Groq models failed or returned empty output.")


def synthesize_with_fallback(
    prompt: str,
    system_instruction: str,
    universal_fallback_fn: Callable[[], str],
    gemini_key: str | None = None,
    groq_key: str | None = None,
) -> SynthesisResult:
    t0 = time.perf_counter()
    errors: list[str] = []

    gkey = resolve_secret("GEMINI_API_KEY", gemini_key)
    if gkey:
        try:
            text, model = _call_gemini(prompt, system_instruction, gkey)
            return SynthesisResult(text, "Google Gemini", model, int((time.perf_counter() - t0) * 1000), False, "Primary LLM tier succeeded.")
        except Exception as exc:
            errors.append(f"Gemini unavailable ({type(exc).__name__})")

    qkey = resolve_secret("GROQ_API_KEY", groq_key)
    if qkey:
        try:
            text, model = _call_groq(prompt, system_instruction, qkey)
            return SynthesisResult(text, "Groq Cloud (Fallback)", model, int((time.perf_counter() - t0) * 1000), True, " | ".join(errors) or "Groq fallback.")
        except Exception as exc:
            errors.append(f"Groq unavailable ({type(exc).__name__})")

    return SynthesisResult(
        universal_fallback_fn(),
        "Universal Keyless Engine",
        "deterministic-scholar-synthesizer-v1",
        int((time.perf_counter() - t0) * 1000),
        True,
        " | ".join(errors) if errors else "Keyless autonomous synthesis active.",
    )
