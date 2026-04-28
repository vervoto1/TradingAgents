"""High-level client for external system integration."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

from .schema import AnalysisResult, _state_to_result


class TradingAgentsClient:
    """Wrapper around TradingAgentsGraph for programmatic use.

    Provides structured output, batch analysis, and a feedback loop
    for learning from past decisions via the persistent decision log.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.config = config or DEFAULT_CONFIG.copy()
        self._graph: Optional[TradingAgentsGraph] = None

    def _ensure_graph(self, analysts: Optional[List[str]] = None, depth: int = 1):
        """Lazily create or reconfigure the graph."""
        selected = analysts or ["market", "social", "news", "fundamentals"]
        config = self.config.copy()
        config["max_debate_rounds"] = depth
        config["max_risk_discuss_rounds"] = depth

        self._graph = TradingAgentsGraph(
            selected_analysts=selected,
            debug=False,
            config=config,
        )

    def analyze(
        self,
        ticker: str,
        date: str,
        analysts: Optional[List[str]] = None,
        depth: int = 1,
    ) -> AnalysisResult:
        """Run a full analysis and return a structured result."""
        self._ensure_graph(analysts, depth)

        start = time.time()
        state, decision = self._graph.propagate(ticker.strip().upper(), date)
        elapsed = time.time() - start

        return _state_to_result(
            state=state,
            decision=decision,
            config=self.config,
            elapsed=elapsed,
        )

    def analyze_batch(self, requests: List[Dict[str, Any]]) -> List[AnalysisResult]:
        """Run sequential analysis for multiple tickers.

        Each request dict: {"ticker": str, "date": str, "analysts": list[str], "depth": int}
        Only ticker and date are required.
        """
        results = []
        for req in requests:
            result = self.analyze(
                ticker=req["ticker"],
                date=req["date"],
                analysts=req.get("analysts"),
                depth=req.get("depth", 1),
            )
            results.append(result)
        return results

    def reflect_on_outcome(self, ticker: str, trade_date: str, raw_return: float, alpha_return: float, holding_days: int = 5) -> None:
        """Reflect on a past decision and update the decision log.

        Uses the graph's memory log to find the pending entry, generates
        a reflection, and updates the log with outcome data.
        """
        if self._graph is None:
            self._ensure_graph()
        self._graph.memory_log.update_with_outcome(
            ticker=ticker,
            trade_date=trade_date,
            raw_return=raw_return,
            alpha_return=alpha_return,
            holding_days=holding_days,
            reflection=self._graph.reflector.reflect_on_final_decision(
                final_decision="",
                raw_return=raw_return,
                alpha_return=alpha_return,
            ),
        )
