from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class AnalystReport:
    analyst_type: str  # "market", "social", "news", "fundamentals"
    content: str       # Full report text


@dataclass
class MemoryMatch:
    matched_situation: str  # Past situation text
    recommendation: str     # Reflection/lesson from that situation
    similarity_score: float # BM25 normalized 0-1
    memory_source: str      # "bull_memory", "bear_memory", etc.


@dataclass
class InvestmentDebate:
    bull_history: str
    bear_history: str
    full_transcript: str
    judge_decision: str
    rounds: int
    bull_memories_used: list[MemoryMatch] = field(default_factory=list)
    bear_memories_used: list[MemoryMatch] = field(default_factory=list)


@dataclass
class RiskDebate:
    aggressive_history: str
    conservative_history: str
    neutral_history: str
    full_transcript: str
    judge_decision: str
    rounds: int


@dataclass
class AnalysisMetadata:
    ticker: str
    date: str
    provider: str
    deep_model: str
    quick_model: str
    analysts_used: list[str]
    depth: int
    elapsed_seconds: float
    timestamp: str


@dataclass
class AnalysisResult:
    decision: str
    analyst_reports: list[AnalystReport]
    investment_debate: InvestmentDebate
    risk_debate: RiskDebate
    investment_plan: str
    trader_plan: str
    final_reasoning: str
    memories_used: list[MemoryMatch]
    metadata: AnalysisMetadata
    raw_state: Optional[dict] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_state", None)
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# Report key -> analyst_type label
_REPORT_KEY_MAP = {
    "market_report": "market",
    "sentiment_report": "social",
    "news_report": "news",
    "fundamentals_report": "fundamentals",
}


def _state_to_result(
    state: dict,
    decision: str,
    config: dict,
    elapsed: float,
    memory_log: list | None = None,
) -> AnalysisResult:
    """Map a raw AgentState dict to a structured AnalysisResult."""

    # --- Analyst reports ---
    analyst_reports: list[AnalystReport] = []
    analysts_used: list[str] = []
    for key, analyst_type in _REPORT_KEY_MAP.items():
        content = state.get(key)
        if content:
            analyst_reports.append(AnalystReport(analyst_type=analyst_type, content=content))
            analysts_used.append(analyst_type)

    # --- Memory matches ---
    memory_matches: list[MemoryMatch] = []
    if memory_log:
        for entry in memory_log:
            if isinstance(entry, MemoryMatch):
                memory_matches.append(entry)
            elif isinstance(entry, dict):
                memory_matches.append(
                    MemoryMatch(
                        matched_situation=entry.get("matched_situation", ""),
                        recommendation=entry.get("recommendation", ""),
                        similarity_score=float(entry.get("similarity_score", 0.0)),
                        memory_source=entry.get("memory_source", ""),
                    )
                )

    bull_memories = [m for m in memory_matches if m.memory_source == "bull_memory"]
    bear_memories = [m for m in memory_matches if m.memory_source == "bear_memory"]

    # --- Investment debate ---
    invest_state = state.get("investment_debate_state") or {}
    investment_debate = InvestmentDebate(
        bull_history=invest_state.get("bull_history", ""),
        bear_history=invest_state.get("bear_history", ""),
        full_transcript=invest_state.get("history", ""),
        judge_decision=invest_state.get("judge_decision", ""),
        rounds=invest_state.get("count", 0),
        bull_memories_used=bull_memories,
        bear_memories_used=bear_memories,
    )

    # --- Risk debate ---
    risk_state = state.get("risk_debate_state") or {}
    risk_debate = RiskDebate(
        aggressive_history=risk_state.get("aggressive_history", ""),
        conservative_history=risk_state.get("conservative_history", ""),
        neutral_history=risk_state.get("neutral_history", ""),
        full_transcript=risk_state.get("history", ""),
        judge_decision=risk_state.get("judge_decision", ""),
        rounds=risk_state.get("count", 0),
    )

    # --- Plans and reasoning ---
    investment_plan = state.get("investment_plan", "") or invest_state.get("judge_decision", "")
    trader_plan = state.get("trader_investment_plan", "")
    final_reasoning = state.get("final_trade_decision", "")

    # --- Metadata ---
    ticker = state.get("company_of_interest", "")
    trade_date = state.get("trade_date", "")
    depth = config.get("max_debate_rounds", 1)

    metadata = AnalysisMetadata(
        ticker=ticker,
        date=trade_date,
        provider=config.get("llm_provider", ""),
        deep_model=config.get("deep_think_llm", ""),
        quick_model=config.get("quick_think_llm", ""),
        analysts_used=analysts_used,
        depth=depth,
        elapsed_seconds=elapsed,
        timestamp=datetime.now().isoformat(),
    )

    return AnalysisResult(
        decision=decision,
        analyst_reports=analyst_reports,
        investment_debate=investment_debate,
        risk_debate=risk_debate,
        investment_plan=investment_plan,
        trader_plan=trader_plan,
        final_reasoning=final_reasoning,
        memories_used=memory_matches,
        metadata=metadata,
        raw_state=state,
    )
