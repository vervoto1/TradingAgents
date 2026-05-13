from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news
)


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Applied to every agent whose output reaches the saved report —
    analysts, researchers, debaters, research manager, trader, and
    portfolio manager — so a non-English run produces a fully localized
    report rather than a mix of languages.
    """
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers."""
    return (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`)."
    )

def get_memories_with_log(memory, situation: str, source_name: str, n_matches: int = 2):
    """Retrieve memories and return both the prompt string and log entries.

    Args:
        memory: FinancialSituationMemory instance
        situation: Current market situation text
        source_name: Memory source identifier (e.g. "bull_memory")
        n_matches: Number of top matches to retrieve

    Returns:
        Tuple of (prompt_string, log_entries) where log_entries is a list of dicts
        ready to append to state["memory_log"].
    """
    past_memories = memory.get_memories(situation, n_matches=n_matches)

    prompt_str = ""
    log_entries = []
    for rec in past_memories:
        prompt_str += rec["recommendation"] + "\n\n"
        log_entries.append({
            "matched_situation": rec["matched_situation"],
            "recommendation": rec["recommendation"],
            "similarity_score": rec["similarity_score"],
            "memory_source": source_name,
        })

    return prompt_str, log_entries


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        
