# Plan: Econ Paper Review Agent — API Pilot

**Date:** 2026-11-06
**Status:** APPROVED (user request contained full requirements; autonomous cloud session)
**Branch:** `claude/econ-paper-review-agent-ek5art`

## Goal

Build a minimal, runnable research-review agent on the **Claude API** (not Claude Code)
that takes an empirical economics paper's abstract + research-design section and returns
a structured review: research question, data structure, identification strategy, key
assumptions, endogeneity concerns. Funded by $100 API credits expiring 2026-12-01
(credits apply to the API/Agent SDK, NOT Claude Code sessions).

## Scope decisions

- **Pilot = single structured API call** (extraction + critique), not a multi-tool agent.
  Per the "Should I build an agent?" test, this task is fully specifiable in advance →
  single-call tier. The Agent SDK is deliberately deferred to a later phase.
- **New isolated directory** `econ-review-agent/` at repo root. Zero changes to existing
  Claude Code skills/agents.
- **Source prompts** distilled from `.claude/skills/review-paper/SKILL.md` (dimensions
  1–3 + referee objections) and `research-ideation/SKILL.md` (assumption/pitfall framing).

## Deliverables

1. `econ-review-agent/econ_review/` — Python package: Pydantic schema, system prompt,
   reviewer (uses `client.messages.parse` for validated structured output), budget guard
   (per-run + cumulative USD caps, usage ledger), CLI.
2. `examples/` — two synthetic inputs (min-wage DiD; Bartik IV urban) + sample output shape.
3. `tests/` — offline tests (schema, prompts, budget, mocked reviewer) + live smoke test
   gated on `ANTHROPIC_API_KEY` (skipped otherwise).
4. `README.md` — setup, usage, cost model, API-vs-Claude-Code reusability map,
   validation criteria for the Dec 1 deadline.
5. Plan + session log per repo rules.

## Verification

- `pytest` offline suite passes in this container (no API key needed).
- Live API call CANNOT be verified here (no key in this environment) — stated explicitly;
  live smoke test is provided for the user to run locally.

## Honest limitations

- Code written ≠ API verified. The live path is exercised only by `tests/test_live_smoke.py`
  and `python -m econ_review.cli`, which the user must run with their own key.
