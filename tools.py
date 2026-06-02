"""
Custom tools for the Power BI Specialist Agent.
Each function can be called by the agent during a conversation.
"""

import os
import json
import requests
from config import get
from docs_store import search_and_format


# ---------------------------------------------------------------------------
# Power BI REST API — authentication
# ---------------------------------------------------------------------------

# Microsoft's public Power BI client ID (no Azure registration needed)
_PUBLIC_CLIENT_ID = "c0d2a505-13b8-4ae0-aa9e-cddd5eab0b12"
_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

# Cached token — reused across calls until it expires
_token_cache: dict = {}


def _get_token() -> str:
    """
    Get a Power BI access token using one of three methods (auto-detected):

      1. POWERBI_AUTH=password  → username + password (no MFA)
      2. POWERBI_AUTH=device    → browser device-code login (works with MFA)
      3. POWERBI_AUTH=app       → Azure AD app secret (original method)

    Set POWERBI_AUTH in your .env file to choose.
    Defaults to 'device' if nothing is configured.
    """
    import msal

    auth_method = get("POWERBI_AUTH", "device").lower()

    # Return cached token if still valid
    if _token_cache.get("access_token") and _token_cache.get("method") == auth_method:
        return _token_cache["access_token"]

    # ── Method 1: Username + Password ──────────────────────────────────────
    if auth_method == "password":
        username = get("POWERBI_USERNAME")
        password = get("POWERBI_PASSWORD")
        if not username or not password:
            raise ValueError(
                "Set POWERBI_USERNAME and POWERBI_PASSWORD in your .env file "
                "to use password auth. Note: does not work if MFA is enabled."
            )
        app = msal.PublicClientApplication(
            _PUBLIC_CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
        )
        result = app.acquire_token_by_username_password(
            username=username, password=password, scopes=_SCOPES
        )

    # ── Method 2: Device Code (browser login, works with MFA) ──────────────
    elif auth_method == "device":
        app = msal.PublicClientApplication(
            _PUBLIC_CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
        )
        # Try silent first (uses cached token from a previous login)
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(_SCOPES, account=accounts[0])
            if result and "access_token" in result:
                _token_cache.update({"access_token": result["access_token"], "method": auth_method})
                return result["access_token"]

        # Interactive device code flow
        flow = app.initiate_device_flow(scopes=_SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow failed: {flow.get('error_description')}")

        print("\n" + "=" * 60)
        print("Power BI Login Required")
        print("=" * 60)
        print(flow["message"])  # prints the URL + code to the console/UI
        print("=" * 60 + "\n")

        result = app.acquire_token_by_device_flow(flow)  # blocks until user logs in

    # ── Method 3: Azure AD App Secret (original) ────────────────────────────
    elif auth_method == "app":
        tenant_id = get("POWERBI_TENANT_ID")
        client_id = get("POWERBI_CLIENT_ID")
        client_secret = get("POWERBI_CLIENT_SECRET")
        if not all([tenant_id, client_id, client_secret]):
            raise ValueError(
                "Set POWERBI_TENANT_ID, POWERBI_CLIENT_ID, POWERBI_CLIENT_SECRET "
                "in your .env file for app auth."
            )
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        result = app.acquire_token_for_client(scopes=_SCOPES)

    else:
        raise ValueError(f"Unknown POWERBI_AUTH method: '{auth_method}'. Use 'password', 'device', or 'app'.")

    if "access_token" not in result:
        raise RuntimeError(
            f"Authentication failed: {result.get('error_description', result.get('error', 'Unknown error'))}"
        )

    _token_cache.update({"access_token": result["access_token"], "method": auth_method})
    return result["access_token"]


def call_powerbi_api(endpoint: str, method: str = "GET", body: dict = None) -> dict:
    """
    Call the Power BI REST API.

    Args:
        endpoint: e.g. '/v1.0/myorg/groups'
        method:   GET | POST | DELETE | PATCH
        body:     JSON body for POST/PATCH

    Returns:
        JSON response dict or {'status': 'success'} for 202/204
    """
    url = "https://api.powerbi.com" + endpoint
    token = _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.request(method, url, headers=headers, json=body, timeout=30)

    if response.status_code in (202, 204):
        return {"status": "success", "http_status": response.status_code}
    if response.status_code >= 400:
        return {"error": f"HTTP {response.status_code}", "detail": response.text}
    return response.json()


# ---------------------------------------------------------------------------
# DAX validator
# ---------------------------------------------------------------------------

def validate_dax(formula: str) -> dict:
    """
    Basic DAX syntax checker — catches common structural issues.

    Args:
        formula: The DAX expression to validate

    Returns:
        dict with 'valid', 'issues', and 'suggestions'
    """
    issues = []
    suggestions = []
    upper = formula.upper()

    if formula.count("(") != formula.count(")"):
        issues.append(
            f"Unbalanced parentheses: {formula.count('(')} open, "
            f"{formula.count(')')} close"
        )

    if formula.count('"') % 2 != 0:
        issues.append("Unbalanced double quotes")

    if "/" in formula and "DIVIDE" not in upper:
        suggestions.append(
            "Use DIVIDE(numerator, denominator, 0) instead of '/' "
            "to safely handle division by zero"
        )

    if "FILTER(" in upper and "ALL(" not in upper and "ALLSELECTED(" not in upper:
        suggestions.append(
            "Using FILTER() on a large table can be slow — consider direct "
            "column filters inside CALCULATE() instead"
        )

    repeats = sum([upper.count(f) for f in ["SUM(", "CALCULATE(", "SUMX("]])
    if repeats > 3:
        suggestions.append(
            "Multiple repeated expressions detected — use VAR to store "
            "intermediate results for better readability and performance"
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Docs search
# ---------------------------------------------------------------------------

def search_docs(query: str, top_n: int = 3) -> str:
    """
    Search the Power BI knowledge base (DAX functions, M patterns, concepts).

    Args:
        query: What to look up, e.g. 'year to date', 'CALCULATE filter'
        top_n: Number of results (default 3)

    Returns:
        Formatted documentation string
    """
    return search_and_format(query, top_n=top_n)


# ---------------------------------------------------------------------------
# Tool definitions (JSON schema for Claude)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "search_docs",
        "description": (
            "Search the Power BI knowledge base for DAX functions, M Query patterns, "
            "and Power BI concepts. Use this when you need reference information "
            "about a specific function, technique, or concept before answering."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'year to date', 'RANKX', 'context transition'",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of results to return (default 3, max 5)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "validate_dax",
        "description": (
            "Validate a DAX formula for syntax errors and performance issues. "
            "Always run this before presenting a DAX formula to the user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "formula": {
                    "type": "string",
                    "description": "The DAX formula or measure to validate",
                }
            },
            "required": ["formula"],
        },
    },
    {
        "name": "call_powerbi_api",
        "description": (
            "Call the Power BI REST API to list workspaces, datasets, reports, "
            "trigger dataset refreshes, or manage Power BI resources. "
            "Requires POWERBI_* credentials in the .env file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "description": "API path, e.g. '/v1.0/myorg/groups'",
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "DELETE", "PATCH"],
                },
                "body": {
                    "type": "object",
                    "description": "Request body for POST/PATCH (optional)",
                },
            },
            "required": ["endpoint", "method"],
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher — routes tool calls from the agent
# ---------------------------------------------------------------------------

def execute_tool(name: str, tool_input: dict) -> str:
    """Route a tool call to the correct function and return a string result."""
    try:
        if name == "search_docs":
            return search_docs(
                query=tool_input["query"],
                top_n=tool_input.get("top_n", 3),
            )

        elif name == "validate_dax":
            result = validate_dax(tool_input["formula"])
            lines = []
            if result["valid"]:
                lines.append("DAX syntax check passed — no structural issues found.")
            else:
                lines.append("Issues found:")
                for issue in result["issues"]:
                    lines.append(f"  • {issue}")
            if result["suggestions"]:
                lines.append("\nPerformance / best-practice suggestions:")
                for s in result["suggestions"]:
                    lines.append(f"  • {s}")
            return "\n".join(lines)

        elif name == "call_powerbi_api":
            result = call_powerbi_api(
                endpoint=tool_input["endpoint"],
                method=tool_input.get("method", "GET"),
                body=tool_input.get("body"),
            )
            return json.dumps(result, indent=2)

        else:
            return f"Unknown tool: {name}"

    except Exception as exc:
        return f"Tool error ({name}): {exc}"
