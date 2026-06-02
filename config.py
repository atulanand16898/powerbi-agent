"""
Unified config loader.
Reads from Streamlit secrets (cloud) or .env file (local) automatically.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # no-op on Streamlit Cloud


def get(key: str, default: str = "") -> str:
    """
    Get a config value from:
    1. Streamlit secrets (when running on Streamlit Cloud)
    2. Environment variables / .env file (local dev)
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return val
    except Exception:
        pass

    # Fall back to environment variable
    return os.getenv(key, default)
