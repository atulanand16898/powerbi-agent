"""
Streamlit Web UI for the Power BI Specialist Agent.
Run with: streamlit run ui.py
"""

import streamlit as st
from agent import PowerBIAgent
from memory import list_sessions, load_session, delete_session

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Power BI Specialist Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Chat area background */
    .main .block-container { padding-top: 1rem; }

    /* Tool call indicator pill */
    .tool-pill {
        display: inline-block;
        background: #1f3a5f;
        color: #7eb8f7;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-family: monospace;
        margin: 2px 0;
    }

    /* Sidebar session items */
    .session-title {
        font-size: 0.85rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state():
    if "agent" not in st.session_state:
        st.session_state.agent = PowerBIAgent()
    if "display_messages" not in st.session_state:
        # List of {"role": "user"|"assistant", "content": str, "tools": [...]}
        st.session_state.display_messages = []
    if "tool_log" not in st.session_state:
        st.session_state.tool_log = []  # tools used in the current turn

_init_state()

# ---------------------------------------------------------------------------
# Sidebar — session history
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("📊 Power BI Agent")
    st.caption("Powered by Claude claude-opus-4-6")

    st.divider()

    if st.button("➕  New Chat", use_container_width=True, type="primary"):
        st.session_state.agent = PowerBIAgent()
        st.session_state.display_messages = []
        st.session_state.tool_log = []
        st.rerun()

    st.subheader("Past Sessions")

    sessions = list_sessions()
    if not sessions:
        st.caption("No saved sessions yet.")
    else:
        for s in sessions[:20]:  # Show latest 20
            col1, col2 = st.columns([5, 1])
            with col1:
                label = s["title"][:35] + ("…" if len(s["title"]) > 35 else "")
                if st.button(
                    label,
                    key=f"load_{s['session_id']}",
                    use_container_width=True,
                ):
                    saved = load_session(s["session_id"])
                    if saved:
                        # Rebuild display messages from saved plain-text turns
                        st.session_state.display_messages = [
                            {"role": m["role"], "content": m["content"], "tools": []}
                            for m in saved["messages"]
                            if isinstance(m.get("content"), str)
                        ]
                        st.session_state.agent = PowerBIAgent(
                            session_id=s["session_id"]
                        )
                        st.session_state.tool_log = []
                        st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{s['session_id']}", help="Delete"):
                    delete_session(s["session_id"])
                    st.rerun()

    st.divider()
    st.caption(f"Session: `{st.session_state.agent.session_id}`")

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.header("Power BI Specialist Agent")

# --- Render existing messages ---
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "📊"):
        st.markdown(msg["content"])
        # Show tool badges if any were used
        for tool in msg.get("tools", []):
            st.markdown(
                f'<span class="tool-pill">🔧 {tool}</span>',
                unsafe_allow_html=True,
            )

# --- Input ---
user_input = st.chat_input("Ask about DAX, Power Query, reports, REST API...")

if user_input:
    # Show user message immediately
    st.session_state.display_messages.append({
        "role": "user",
        "content": user_input,
        "tools": [],
    })
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # Stream the agent response
    with st.chat_message("assistant", avatar="📊"):
        tools_used = []
        response_placeholder = st.empty()
        full_response = ""

        # Patch execute_tool to capture tool names for display
        import tools as tools_module
        original_execute = tools_module.execute_tool

        def _tracked_execute(name, tool_input):
            tools_used.append(name)
            return original_execute(name, tool_input)

        tools_module.execute_tool = _tracked_execute

        try:
            for chunk in st.session_state.agent.stream_chat(user_input):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
        finally:
            tools_module.execute_tool = original_execute  # restore

        response_placeholder.markdown(full_response)

        # Show tool badges under the response
        for tool in tools_used:
            st.markdown(
                f'<span class="tool-pill">🔧 {tool}</span>',
                unsafe_allow_html=True,
            )

    # Save to display history
    st.session_state.display_messages.append({
        "role": "assistant",
        "content": full_response,
        "tools": tools_used,
    })
