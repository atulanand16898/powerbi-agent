"""
Quick tests to verify the agent and tools work correctly.
Run: python test_agent.py
"""

import sys
from tools import validate_dax, execute_tool


def test_dax_validator():
    print("--- Test: DAX Validator ---")

    # Valid formula
    result = validate_dax("DIVIDE(SUM(Sales[Amount]), COUNTROWS(Sales))")
    assert result["valid"] is True, "Should be valid"
    print("PASS: Valid formula accepted")

    # Unbalanced parentheses
    result = validate_dax("SUM(Sales[Amount]")
    assert result["valid"] is False
    assert any("parentheses" in i for i in result["issues"])
    print("PASS: Unbalanced parentheses detected")

    # Division without DIVIDE
    result = validate_dax("SUM(Sales[Amount]) / SUM(Sales[Qty])")
    assert len(result["suggestions"]) > 0
    print("PASS: DIVIDE() suggestion given for '/' usage")

    print()


def test_tool_dispatch():
    print("--- Test: Tool Dispatch ---")

    result = execute_tool("validate_dax", {
        "formula": "SUMX(Sales, Sales[Qty] * Sales[Price]"  # Missing closing )
    })
    assert "issues" in result.lower() or "parenthes" in result.lower()
    print("PASS: Tool dispatch works")
    print(f"      Result: {result[:80]}...")
    print()


def test_agent_import():
    print("--- Test: Agent Import ---")
    try:
        from agent import PowerBIAgent
        agent = PowerBIAgent()
        print("PASS: PowerBIAgent created successfully")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    print()


if __name__ == "__main__":
    test_dax_validator()
    test_tool_dispatch()
    test_agent_import()
    print("All tests passed!")
