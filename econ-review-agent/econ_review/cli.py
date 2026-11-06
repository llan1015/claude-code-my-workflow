"""CLI: review a paper excerpt from a text/markdown file.

    python -m econ_review.cli examples/minimum_wage_did.md
    python -m econ_review.cli examples/bartik_iv_urban.md --out review.json
    python -m econ_review.cli examples/minimum_wage_did.md --dry-run   # no API call

Requires ANTHROPIC_API_KEY in the environment (or an `ant auth login` profile)
except with --dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .budget import (
    BudgetExceededError,
    Caps,
    Ledger,
    estimate_input_tokens,
    precheck,
)
from .prompts import SYSTEM_PROMPT, build_user_message
from .reviewer import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, review_paper


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structured review of an econ paper excerpt.")
    parser.add_argument("paper", type=Path, help="Path to a .md/.txt file: abstract + research design.")
    parser.add_argument("--title", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--out", type=Path, default=None, help="Write review JSON here (default: stdout).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the worst-case cost estimate and exit without calling the API.")
    args = parser.parse_args(argv)

    paper_text = args.paper.read_text()
    ledger = Ledger()

    if args.dry_run:
        try:
            worst = precheck(
                model=args.model,
                est_input_tokens=estimate_input_tokens(
                    SYSTEM_PROMPT + build_user_message(paper_text, title=args.title)
                ),
                max_output_tokens=args.max_tokens,
                ledger=ledger,
                caps=Caps(),
            )
        except BudgetExceededError as e:
            print(f"BLOCKED: {e}", file=sys.stderr)
            return 2
        print(f"Dry run OK. Worst-case cost for this call: ${worst:.3f} "
              f"(model={args.model}, max_tokens={args.max_tokens}).")
        print(f"Pilot spend so far (ledger): ${ledger.total_usd():.2f}")
        return 0

    try:
        result = review_paper(
            paper_text,
            title=args.title,
            model=args.model,
            max_tokens=args.max_tokens,
            ledger=ledger,
        )
    except BudgetExceededError as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        return 2

    payload = result.review.model_dump()
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text)
        print(f"Review written to {args.out}")
    else:
        print(text)

    print(
        f"\n[usage] model={result.model} in={result.input_tokens} out={result.output_tokens} "
        f"cost=${result.cost_usd:.4f} | pilot total=${ledger.total_usd():.2f}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
