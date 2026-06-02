"""
Power BI Specialist AI Agent
----------------------------
Conversational agent powered by Claude claude-opus-4-6.
Features: tool use, session memory, streaming responses, skill loading.
"""

from typing import Generator
import anthropic

from config import get
from tools import TOOL_DEFINITIONS, execute_tool
from memory import new_session_id, save_session, load_session

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Power BI Specialist AI Agent with mastery of:
- DAX — measures, calculated columns, time intelligence, context transition
- Power Query / M Language — data transformation, ETL, query folding
- Data Modeling — star schema, relationships, RLS, aggregations
- Power BI Visualizations — chart selection, report design, UX
- Power BI Service & REST API — workspaces, datasets, refresh automation

## Your workflow
1. For DAX/M/concept questions → search_docs first to load reference material
2. When writing a DAX formula → validate_dax before showing the user
3. For Power BI API operations → call_powerbi_api (requires credentials)

## Response style
- Be precise and practical — show working code, not pseudocode
- Use DAX code blocks for formulas, M code blocks for Power Query
- Explain WHY a pattern works, not just WHAT it does
- Warn about performance implications proactively
- When a formula has multiple approaches, show the recommended one first
"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class PowerBIAgent:
    """
    Conversational Power BI specialist with tool use, memory, and streaming.
    """

    def __init__(self, session_id: str = None):
        self.client = anthropic.Anthropic(api_key=get("ANTHROPIC_API_KEY"))
        self.model = "claude-opus-4-6"
        self.session_id = session_id or new_session_id()

        if session_id:
            saved = load_session(session_id)
            self.messages = saved["messages"] if saved else []
        else:
            self.messages = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        return "".join(self.stream_chat(user_message))

    def stream_chat(self, user_message: str) -> Generator[str, None, None]:
        """
        Send a message and yield response text chunk by chunk.

        Tool calls are resolved with non-streaming API calls first.
        Only the final text response to the user is streamed.
        This keeps the message history clean and avoids thinking-block issues.
        """
        # Snapshot messages so we can roll back on error
        snapshot = [m for m in self.messages]

        self.messages.append({"role": "user", "content": user_message})

        try:
            # --- Step 1: Resolve all tool calls with non-streaming calls ---
            # Keep looping until Claude stops requesting tools
            while True:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    system=[{
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }],
                    tools=TOOL_DEFINITIONS,
                    messages=self.messages,
                )

                if response.stop_reason != "tool_use":
                    # No more tool calls — break out to stream the final answer
                    break

                # Build plain-dict assistant message (NO thinking blocks)
                assistant_blocks = []
                tool_results = []

                for block in response.content:
                    if block.type == "text":
                        assistant_blocks.append({
                            "type": "text",
                            "text": block.text,
                        })
                    elif block.type == "tool_use":
                        assistant_blocks.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                    # Thinking blocks are intentionally skipped —
                    # they must not appear in history alongside tool_use blocks
                    # or they corrupt the next API call.

                if not assistant_blocks:
                    break

                self.messages.append({
                    "role": "assistant",
                    "content": assistant_blocks,
                })
                self.messages.append({
                    "role": "user",
                    "content": tool_results,
                })

            # --- Step 2: Stream the final answer to the user ---
            final_text = ""

            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=[{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            ) as stream:
                for chunk in stream.text_stream:
                    final_text += chunk
                    yield chunk

            # Append final assistant reply as plain text
            self.messages.append({
                "role": "assistant",
                "content": final_text,
            })
            self._save()

        except Exception:
            # Roll back to the clean snapshot so history stays valid
            self.messages = snapshot
            raise

    def reset(self):
        self.messages = []
        self.session_id = new_session_id()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self):
        save_session(self.session_id, self.messages)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Power BI Specialist Agent  (Claude claude-opus-4-6)")
    print("  Commands: 'reset' | 'quit'")
    print("=" * 60 + "\n")

    agent = PowerBIAgent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent.reset()
            print("Session reset.\n")
            continue

        print("\nAgent: ", end="", flush=True)
        for chunk in agent.stream_chat(user_input):
            print(chunk, end="", flush=True)
        print("\n" + "-" * 60)


if __name__ == "__main__":
    main()
