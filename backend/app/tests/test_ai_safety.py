import pytest
from app.providers.ai.tools import AI_TOOLS_SPEC, AIToolExecutor
from app.providers.ai.groq_provider import mask_api_key, sanitize_message, GroqProvider


def test_ai_tools_spec_is_strictly_read_only():
    # Verify AI tools only permit analytical queries and NEVER trading/financial execution
    forbidden_terms = ["buy", "sell", "order", "cancel", "deposit", "withdraw", "execute", "wallet", "pay"]
    
    for tool in AI_TOOLS_SPEC:
        tool_name = tool["function"]["name"].lower()
        desc = tool["function"]["description"].lower()
        for forbidden in forbidden_terms:
            assert forbidden not in tool_name, f"Forbidden financial execution tool found: {tool_name}"


@pytest.mark.asyncio
async def test_ai_tool_executor_blocks_unauthorized_actions():
    res = await AIToolExecutor.execute_tool("place_order", {"symbol": "RELIANCE", "quantity": 10})
    assert "error" in res or "Unknown tool" in str(res)

    res2 = await AIToolExecutor.execute_tool("deposit_funds", {"amount": 50000})
    assert "error" in res2 or "Unknown tool" in str(res2)


def test_groq_credential_masking():
    secret = "gsk_1234567890abcdef1234567890abcdef"
    assert mask_api_key(secret) == "********"
    assert mask_api_key(None) == "[NOT_SET]"

    sanitized = sanitize_message(f"Error calling Groq with key {secret}", secret=secret)
    assert secret not in sanitized
    assert "********" in sanitized


@pytest.mark.asyncio
async def test_ai_tool_executor_reads_verified_data():
    quote_res = await AIToolExecutor.execute_tool("get_live_quote", {"symbol": "RELIANCE"})
    assert quote_res["symbol"] == "RELIANCE"
    assert "price" in quote_res

    fund_res = await AIToolExecutor.execute_tool("get_company_fundamentals", {"symbol": "TCS"})
    assert fund_res["symbol"] == "TCS"
    assert "market_cap" in fund_res or "fundamentals" in fund_res

    opt_res = await AIToolExecutor.execute_tool("get_option_chain", {"symbol": "NIFTY 50"})
    assert opt_res["symbol"] == "NIFTY 50"
    assert "pcr_ratio" in opt_res
