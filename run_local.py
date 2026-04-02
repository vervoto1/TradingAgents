from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "vllm"
config["deep_think_llm"] = "QuantTrio/Qwen3.5-27B-AWQ"
config["deep_think_url"] = "http://localhost:8001/v1"
config["quick_think_llm"] = "QuantTrio/Qwen3.5-35B-A3B-AWQ"
config["quick_think_url"] = "http://localhost:8002/v1"
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

ta = TradingAgentsGraph(debug=True, config=config)

_, decision = ta.propagate("NVDA", "2025-01-15")
print(decision)
