# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingAgents is a multi-agent LLM financial trading framework built on LangGraph. It orchestrates specialized AI agents (analysts, researchers, risk debaters, traders) through a structured debate workflow to produce trading decisions (Buy/Overweight/Hold/Underweight/Sell).

## Commands

```bash
# Install
pip install .

# Run CLI
tradingagents
# or: python -m cli.main

# Docker
docker compose build
docker compose run --rm tradingagents run NVDA 2025-01-15

# Run all tests
python -m pytest tests/

# Run a single test file
python -m pytest tests/test_model_validation.py

# Run a single test
python -m pytest tests/test_model_validation.py::TestModelValidation::test_known_models_are_valid

# Run the standalone data test script (not pytest — plain script)
python test.py
```

## Architecture

### Agent Pipeline

The core workflow is a LangGraph state machine (`tradingagents/graph/`) that executes this pipeline:

```
Analysts (parallel-capable) → Bull/Bear Debate → Research Manager → Trader → Risk Debate → Portfolio Manager → Decision
```

1. **Analysts** (`agents/analysts/`) — up to 4 types selected at runtime: market (technical indicators), social (sentiment), news, fundamentals. Each produces a report stored in agent state.
2. **Researchers** (`agents/researchers/`) — Bull and Bear agents debate in rounds, each drawing on BM25-based memory of past similar situations.
3. **Research Manager** (`agents/managers/`) — Judges the debate, synthesizes an investment plan.
4. **Trader** (`agents/trader/`) — Creates a trading proposal from the plan.
5. **Risk Debaters** (`agents/risk_mgmt/`) — Three perspectives (aggressive, conservative, neutral) debate the proposal.
6. **Portfolio Manager** (`agents/managers/`) — Renders final decision: Buy/Overweight/Hold/Underweight/Sell.

### Key Subsystems

- **Graph orchestration** (`graph/setup.py`, `graph/conditional_logic.py`) — Builds the LangGraph, routes edges based on debate round counts and selected analysts.
- **LLM client factory** (`llm_clients/factory.py`) — Multi-provider support (OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama, vLLM). Uses a dual-model strategy: `deep_think_llm` for reasoning-heavy tasks, `quick_think_llm` for lighter ones.
- **Data layer** (`dataflows/interface.py`) — Vendor-agnostic tool routing. Supports yfinance (default) and Alpha Vantage with per-category or per-tool vendor overrides and automatic fallback.
- **Memory** (`agents/utils/memory.py`) — BM25 lexical similarity for retrieving past trading situations. Separate memory instances per agent role. Fed via `ta.reflect_and_remember()`.
- **Configuration** (`default_config.py`) — Central config dict controlling LLM provider/models, debate rounds, data vendors, output language. Passed into `TradingAgentsGraph` constructor.

### CLI (`cli/`)

Interactive Typer + Rich application. Handles ticker selection, date picking, provider/model selection, analyst team configuration, and a real-time multi-panel dashboard showing agent progress and reports.

### Programmatic Usage

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    config={"llm_provider": "openai", "deep_think_llm": "gpt-5.4", "quick_think_llm": "gpt-5.4-mini"}
)
result, decision = ta.propagate("NVDA", "2025-01-15")
```

### State Shape

Agent state (`AgentState` TypedDict in `agents/utils/`) carries: `company_of_interest`, `trade_date`, analyst reports (`market_report`, `sentiment_report`, `news_report`, `fundamentals_report`), `investment_debate_state`, `risk_debate_state`, `trader_investment_plan`, and `final_trade_decision`.

## Environment

- Requires API keys for the chosen LLM provider (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`)
- Optional: `ALPHA_VANTAGE_API_KEY` for Alpha Vantage data vendor
- Optional: `DEEP_THINK_URL` and `QUICK_THINK_URL` to override vLLM endpoint URLs (defaults: `http://localhost:8001/v1` and `http://localhost:8002/v1`)
- Python >=3.10
- Docker (optional, for containerized execution via `docker compose`)
