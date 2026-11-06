# Econ Review Agent — Claude API Pilot

A minimal, structured review agent for **empirical economics papers**, built on the
**Claude API** (plain `anthropic` SDK — *not* Claude Code). Input: a paper's abstract +
research-design section. Output: a schema-validated JSON review covering the research
question, data structure, identification strategy, key assumptions, and endogeneity
concerns.

**Why it exists:** $100 in API credits (expires **2026-12-01**; usable for the Claude
API / Agent SDK, *not* Claude Code sessions) + a Claude Code workflow repo whose
review skills were only usable interactively. This pilot ports the reviewable core of
`.claude/skills/review-paper/` to a reproducible, scriptable API pipeline.

---

## 1. What ports from the Claude Code repo, and what doesn't

| Repo asset | API/SDK portability | How this pilot uses it |
|---|---|---|
| `review-paper` skill (dims 2-3: identification, econometrics; referee objections) | **Ports directly** — it's a prompt + output contract | Distilled into `econ_review/prompts.py` + the `PaperReview` schema |
| `research-ideation` skill (assumption/pitfall framework) | Ports directly | Folded into assumption/endogeneity fields |
| `interview-me` skill | Needs a conversation loop — fits the **Agent SDK or a multi-turn Messages loop**, not a single call | Deferred (Phase 2 candidate) |
| `lit-review` skill | Needs WebSearch/WebFetch → **server tools on the Messages API** (`web_search`, `web_fetch`) | Deferred (Phase 2 candidate) |
| `.claude/agents/*` (proofreader, slide-auditor, quarto-critic, …) | Claude Code subagents: they depend on the Claude Code harness (Read/Grep/Edit on a repo) | Not portable as-is; equivalent behavior needs the **Claude Agent SDK**, which bundles those tools |
| Hooks, `/commit`, `/deploy`, orchestrator protocol | Claude Code-only (harness features) | Not applicable to the API |
| Quality-gate idea (nothing ships below threshold) | Portable as a *pattern* | Mirrored here as schema validation + substantive asserts in the live smoke test |

**Tier decision:** this task (fixed input → fixed structured output) is a
**single API call with structured outputs**, not an agent. The Agent SDK buys nothing
here and would cost more tokens per run. It becomes the right tool in Phase 2 (reading
PDFs from disk, chasing citations, multi-turn interviewing).

## 2. Layout

```
econ-review-agent/
├── econ_review/
│   ├── schema.py      # PaperReview Pydantic schema (the output contract)
│   ├── prompts.py     # System prompt distilled from review-paper skill
│   ├── reviewer.py    # precheck → messages.parse → validated review
│   ├── budget.py      # USD caps + local usage ledger (gitignored)
│   └── cli.py         # command-line entry point
├── examples/          # two synthetic inputs (DiD, Bartik IV)
├── tests/             # offline suite + gated live smoke test
└── requirements.txt
```

## 3. Quickstart

```bash
cd econ-review-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline checks first — no key, no cost:
pytest -q                                            # live test auto-skips
python -m econ_review.cli examples/minimum_wage_did.md --dry-run

# Live run (set your key in the shell, never in code or chat):
export ANTHROPIC_API_KEY=...        # or `ant auth login`
python -m econ_review.cli examples/minimum_wage_did.md --out review_did.json

# One-call live smoke test with substantive assertions (~$0.05-0.15):
pytest tests/test_live_smoke.py -v
```

Your own paper: paste the abstract + design section into a `.md` file and pass its path.

## 4. Cost model and the $100 budget

Prices (Anthropic API, cached 2026-11-06, per 1M tokens):

| Model | Input | Output | Est. cost / review* | Reviews per $90 |
|---|---|---|---|---|
| `claude-opus-5-5` (default) | $4.00 | $20.00 | **$0.08–0.18** | ~500–1,100 |
| `claude-sonnet-5-5` (`--model`) | $2.00 | $10.00 | $0.04–0.09 | ~1,000–2,200 |
| `claude-haiku-5-5` (`--model`) | $0.10 | $0.50 | $0.002–0.005 | ~20,000+ |

\* Assumes ~2–4K input tokens (prompt + excerpt) and ~3–7K output tokens (the JSON
review **plus thinking tokens, which bill as output**). Opus 5.5 runs adaptive
thinking at effort `medium` by default. Verify against the `[usage]` line each run
and the `usage_ledger.json` totals — the ledger, not this table, is ground truth.

**Guardrails built in (both enforced *before* any call):**

- `ECON_REVIEW_MAX_USD_PER_RUN` (default **$0.50**) — worst-case cost cap per call,
  computed from a deliberately conservative input estimate + full `max_tokens`.
- `ECON_REVIEW_BUDGET_USD` (default **$90**) — cumulative cap across the pilot,
  tracked in the local `usage_ledger.json` (leaves $10 headroom under the credit).
- `--dry-run` shows the worst-case estimate without spending anything.
- For bulk runs (>50 papers), switch to the **Message Batches API** — same requests
  at 50% price, results within 24h. Not implemented in the pilot; trivial Phase-2 add.

Also set a spend limit in the Anthropic Console (Settings → Limits) as a backstop
that doesn't depend on this code being correct.

## 5. Validation criteria — is this worth extending? (decide before 2026-12-01)

Run the agent on **5 published papers you know deeply** (e.g., papers you've refereed
or taught: ideally 2 DiD, 1 IV/shift-share, 1 RDD, 1 of your choice), using only
their abstract + design sections. Score each output:

| # | Criterion | Pass bar |
|---|---|---|
| V1 | **Extraction accuracy** — method, unit, data sources correct? | 5/5 papers, zero fabricated facts |
| V2 | **Assumption completeness** — does it list the assumptions *you* would list? | ≥80% overlap with your list; no missing first-order assumption (e.g., misses exclusion restriction on an IV paper = fail) |
| V3 | **Non-generic critique** — would ≥2 referee questions per paper survive in a real report? | Yes on ≥4/5 papers |
| V4 | **Discrimination** — does `identification_credibility` rank a strong design above a weak one? | Correct ordering on a known strong/weak pair |
| V5 | **Cost** — average actual cost per review | ≤ $0.25 on Opus 5.5 |
| V6 | **Reproducibility** — same paper, 2 runs: same method/assumption classification? | Core fields stable (prose may vary) |

**Decision rule:** ≥5 of 6 pass → extend (Phase 2); 3–4 → iterate on the prompt/schema
and re-test; ≤2 → the structured single call isn't adding value over interactive use.
Total validation cost: ~10–15 runs ≈ **$1.50–4** — negligible against $100.

## 6. What has and hasn't been verified

- ✅ Offline test suite (schema, prompts, budget guard, mocked pipeline) passes.
- ✅ `--dry-run` path runs without a key.
- ❌ **No live API call has been made from this environment** (no key present, by
  design). `messages.parse` usage follows the current SDK docs (anthropic 2.x), but
  *written ≠ verified*: your first action should be `pytest tests/test_live_smoke.py -v`
  with your key. If the SDK surface has drifted, that test fails loudly, not silently.

## 7. Phase 2 roadmap (only after validation passes)

1. **PDF input** — pass whole papers as `document` blocks (base64 PDF, ≤600 pages) or
   via the Files API; review full papers, not excerpts.
2. **Batch mode** — Message Batches for conference-program or syllabus-scale screening.
3. **Lit-positioning module** — `web_search` / `web_fetch` server tools to check
   whether the cited identification literature is current.
4. **Interactive referee** — Agent SDK session that interviews you about your own
   draft (port of `interview-me`), with file access to your `.tex`.
5. **Stata/R cross-check** — feed the paper's reported specification + your
   replication code; ask for discrepancies.
