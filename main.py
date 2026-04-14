import uuid
from dotenv import load_dotenv
from langgraph.types import Command

from supervisor import supervisor

load_dotenv()


def display_updates(chunk: dict) -> None:
    """Pretty-print streaming updates from the supervisor."""
    for node, data in chunk.items():
        if node == "__interrupt__":
            continue
        if not isinstance(data, dict):
            continue
        messages = data.get("messages", [])
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n🔧 [{node}] {tc['name']}({_fmt_args(tc['args'])})")
            elif hasattr(msg, "content") and msg.content:
                role = getattr(msg, "type", "")
                if role == "tool":
                    tool_name = getattr(msg, "name", "tool")
                    content_preview = str(msg.content)[:300]
                    print(f"   📎 [{tool_name}]: {content_preview}")
                elif role == "ai":
                    print(f"\n🤖 [Agent]: {msg.content}")


def _fmt_args(args: dict) -> str:
    parts = []
    for k, v in args.items():
        v_str = str(v)
        if len(v_str) > 120:
            v_str = v_str[:120] + "..."
        parts.append(f"{k}={repr(v_str)}")
    return ", ".join(parts)


def stream_supervisor(input_data, config: dict) -> dict | None:
    """Stream supervisor and return interrupt payload if any."""
    for chunk in supervisor.stream(input_data, config=config, stream_mode="updates"):
        display_updates(chunk)

    state = supervisor.get_state(config)
    for task in state.tasks:
        if task.interrupts:
            return task.interrupts[0].value

    return None


def handle_hitl(interrupt_data: dict, config: dict) -> dict | None:
    """Show the proposed save_report action and get user decision."""
    filename = interrupt_data.get("filename", "report.md")
    content = interrupt_data.get("content", "")

    preview = content[:600] + ("..." if len(content) > 600 else "")

    print("\n" + "=" * 60)
    print("⏸️  ACTION REQUIRES APPROVAL")
    print("=" * 60)
    print(f"  Tool:  save_report")
    print(f"  File:  {filename}")
    print(f"\n  Content preview:\n")
    for line in preview.splitlines()[:15]:
        print(f"    {line}")
    print("=" * 60)

    while True:
        action = input("\n👉 approve / edit / reject: ").strip().lower()
        if action in ("approve", "edit", "reject"):
            break
        print("   Please enter one of: approve, edit, reject")

    if action == "approve":
        decision = {"type": "approve"}
    elif action == "edit":
        feedback = input("✏️  Your feedback: ").strip()
        decision = {"type": "edit", "feedback": feedback}
    else:
        reason = input("📝  Reason for rejection (Enter to skip): ").strip()
        decision = {"type": "reject", "message": reason or "rejected by user"}

    return stream_supervisor(Command(resume=decision), config)


def run_chat():
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("🤖 Multi-agent research system ready! (type 'exit' to quit)")
    print("   Architecture: Supervisor → Planner → Researcher → Critic → save_report\n")

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("👋 Goodbye!")
            break

        interrupt_data = stream_supervisor(
            {"messages": [("user", user_input)]},
            config,
        )

        while interrupt_data is not None:
            interrupt_data = handle_hitl(interrupt_data, config)


if __name__ == "__main__":
    run_chat()
