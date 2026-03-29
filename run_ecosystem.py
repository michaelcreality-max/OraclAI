#!/usr/bin/env python3
"""CLI: run one ecosystem cycle (Alpha → Arena → Reality → Meta)."""

from __future__ import annotations

import argparse
import json
import sys

from quant_ecosystem import QuantEcosystemOrchestrator


def main() -> None:
    p = argparse.ArgumentParser(description="Run quant ecosystem cycle")
    p.add_argument("symbol", nargs="?", default="AAPL", help="Ticker symbol")
    p.add_argument("--period", default="2y", help="yfinance period")
    p.add_argument("--top-models", type=int, default=3, help="Top models per hypothesis")
    p.add_argument("--max-hypotheses", type=int, default=5, help="Cap hypotheses per cycle")
    p.add_argument("--workers", type=int, default=4, help="Thread pool size for arena")
    args = p.parse_args()

    orch = QuantEcosystemOrchestrator(arena_workers=args.workers)
    out = orch.run_cycle(
        args.symbol.upper(),
        period=args.period,
        top_models=args.top_models,
        max_hypotheses=args.max_hypotheses,
    )
    json.dump(out, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
