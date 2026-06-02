"""
Streamlit Web UI for the Power BI Specialist Agent.
Run with: streamlit run ui.py
"""

import streamlit as st
from agent import PowerBIAgent
from memory import list_sessions, load_session, delete_session
from tools import DeviceLoginRequired, complete_device_login

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
    .main .block-container { padding-top: 1rem; }
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state():
    if "agent" not in st.session_state:
        st.session_state.agent = PowerBIAgent()
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    # Device login state
    if "device_login_pending" not in st.session_state:
        st.session_state.device_login_pending = False
    if "device_login_url" not in st.session_state:
        st.session_state.device_login_url = ""
    if "device_login_code" not in st.session_state:
        st.session_state.device_login_code = ""
    # Store live MSAL objects here — survives Streamlit reruns
    if "msal_app" not in st.session_state:
        st.session_state.msal_app = None
    if "msal_flow" not in st.session_state:
        st.session_state.msal_flow = None
    # Retry the original message after login completes
    if "pending_user_message" not in st.session_state:
        st.session_state.pending_user_message = ""

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
        st.session_state.device_login_pending = False
        st.rerun()

    st.subheader("Past Sessions")

    sessions = list_sessions()
    if not sessions:
        st.caption("No saved sessions yet.")
    else:
        for s in sessions[:20]:
            col1, col2 = st.columns([5, 1])
            with col1:
                label = s["title"][:35] + ("…" if len(s["title"]) > 35 else "")
                if st.button(label, key=f"load_{s['session_id']}", use_container_width=True):
                    saved = load_session(s["session_id"])
                    if saved:
                        st.session_state.display_messages = [
                            {"role": m["role"], "content": m["content"], "tools": []}
                            for m in saved["messages"]
                            if isinstance(m.get("content"), str)
                        ]
                        st.session_state.agent = PowerBIAgent(session_id=s["session_id"])
                        st.session_state.device_login_pending = False
                        st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{s['session_id']}", help="Delete"):
                    delete_session(s["session_id"])
                    st.rerun()

    st.divider()
    st.caption(f"Session: `{st.session_state.agent.session_id}`")

# ---------------------------------------------------------------------------
# Power BI device login banner (shown when login is required)
# ---------------------------------------------------------------------------

if st.session_state.device_login_pending:
    st.warning("**Power BI Login Required**", icon="🔐")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
**Step 1 —** Click this link to log in:

### 👉 [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin)

**Step 2 —** Enter this code when prompted:
"""
        )
        st.code(st.session_state.device_login_code, language=None)
        st.caption("Use your Power BI / Microsoft 365 account to sign in.")

    with col2:
        st.markdown("&nbsp;")  # vertical spacer
        if st.button("✅  I've logged in", type="primary", use_container_width=True):
            with st.spinner("Completing login…"):
                success = complete_device_login(
                    st.session_state.msal_app,
                    st.session_state.msal_flow,
                )
            if success:
                st.session_state.device_login_pending = False
                st.success("Logged in to Power BI!")
                # Re-run the original message now that we have a token
                if st.session_state.pending_user_message:
                    st.session_state._retry_message = st.session_state.pending_user_message
                    st.session_state.pending_user_message = ""
                st.rerun()
            else:
                st.error("Login not completed yet — please finish in the browser first, then click again.")

    st.divider()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.header("Power BI Specialist Agent")

# Render existing messages
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "📊"):
        st.markdown(msg["content"])
        for tool in msg.get("tools", []):
            st.markdown(f'<span class="tool-pill">🔧 {tool}</span>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Handle input — either a fresh message or a retry after device login
# ---------------------------------------------------------------------------

user_input = st.chat_input(
    "Ask about DAX, Power Query, reports, REST API...",
    disabled=st.session_state.device_login_pending,
)

# Pick up a retry message injected after successful device login
if not user_input and st.session_state.get("_retry_message"):
    user_input = st.session_state.pop("_retry_message")

if user_input:
    # Show user message
    st.session_state.display_messages.append({"role": "user", "content": user_input, "tools": []})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # Stream agent response
    with st.chat_message("assistant", avatar="📊"):
        tools_used = []
        response_placeholder = st.empty()
        full_response = ""

        # Wrap execute_tool to capture tool names for display badges
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

            response_placeholder.markdown(full_response)
            for tool in tools_used:
                st.markdown(f'<span class="tool-pill">🔧 {tool}</span>', unsafe_allow_html=True)

            st.session_state.display_messages.append({
                "role": "assistant",
                "content": full_response,
                "tools": tools_used,
            })

        except DeviceLoginRequired as e:
            # Power BI device login needed — show the banner
            st.session_state.device_login_pending = True
            st.session_state.device_login_url = e.verification_url
            st.session_state.device_login_code = e.user_code
            # Store live MSAL objects so complete_device_login() works after rerun
            st.session_state.msal_app = e.msal_app
            st.session_state.msal_flow = e.msal_flow
            st.session_state.pending_user_message = user_input
            # Remove the user message we just added (will be re-sent after login)
            st.session_state.display_messages.pop()
            response_placeholder.empty()
            st.rerun()

        except Exception as e:
            response_placeholder.error(f"Error: {e}")

        finally:
            tools_module.execute_tool = original_execute
