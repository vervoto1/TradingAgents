"""High-level client for external system integration."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

from .schema import AnalysisResult, _state_to_result

# Names of the 5 memory attributes on TradingAgentsGraph
_MEMORY_ATTRS = [
    "bull_memory",
    "bear_memory",
    "trader_memory",
    "invest_judge_memory",
    "portfolio_manager_memory",
]


class TradingAgentsClient:
    """Wrapper around TradingAgentsGraph for programmatic use.

    Provides structured output, batch analysis, memory persistence,
    and a feedback loop for learning from past decisions.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_dir: str = "data/memory",
        auto_load_memory: bool = True,
    ):
        self.config = config or DEFAULT_CONFIG.copy()
        self.memory_dir = memory_dir
        self._graph: Optional[TradingAgentsGraph] = None

        if auto_load_memory:
            self.load_memory()

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

        # Restore persisted memories onto the new graph instance
        self._load_memories_onto_graph()

    def _load_memories_onto_graph(self):
        """Load persisted memory files onto the current graph's memory instances."""
        if self._graph is None:
            return
        for attr in _MEMORY_ATTRS:
            mem = getattr(self._graph, attr, None)
            if mem is None:
                continue
            path = os.path.join(self.memory_dir, f"{attr}.json")
            if os.path.exists(path):
                mem.load_from_file(path)

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

        memory_log = state.get("memory_log", [])

        return _state_to_result(
            state=state,
            decision=decision,
            config=self.config,
            elapsed=elapsed,
            memory_log=memory_log,
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

    def feedback(self, returns_losses) -> None:
        """Reflect on the last analysis and persist updated memories."""
        if self._graph is None:
            raise RuntimeError("No analysis has been run yet. Call analyze() first.")
        self._graph.reflect_and_remember(returns_losses)
        self.save_memory()

    def save_memory(self) -> None:
        """Persist all memory instances to disk."""
        if self._graph is None:
            return
        os.makedirs(self.memory_dir, exist_ok=True)
        for attr in _MEMORY_ATTRS:
            mem = getattr(self._graph, attr, None)
            if mem is None:
                continue
            path = os.path.join(self.memory_dir, f"{attr}.json")
            mem.save_to_file(path)

    def load_memory(self) -> None:
        """Load all memory instances from disk (if files exist)."""
        if self._graph is not None:
            self._load_memories_onto_graph()
