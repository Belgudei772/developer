#!/usr/bin/env python3
"""
Developer - AI Coding Assistant
A terminal chat interface with chat mode and plan mode.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from platformdirs import user_config_dir
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

try:
    from tools import list_files, read_file, run_command, write_file
except ImportError:
    from src.tools import list_files, read_file, run_command, write_file

try:
    from plan_mode import (
        PlanState,
        approve_steps,
        create_plan_from_json,
        get_runnable_steps,
        mark_step_result,
        render_plan,
        reset_plan,
        validate_plan,
    )
except ImportError:
    from src.plan_mode import (
        PlanState,
        approve_steps,
        create_plan_from_json,
        get_runnable_steps,
        mark_step_result,
        render_plan,
        reset_plan,
        validate_plan,
    )

try:
    from prompts import PLAN_JSON_SCHEMA_HINT, SYSTEM_CHAT_PROMPT, SYSTEM_PLAN_PROMPT
except ImportError:
    from src.prompts import (
        PLAN_JSON_SCHEMA_HINT,
        SYSTEM_CHAT_PROMPT,
        SYSTEM_PLAN_PROMPT,
    )

CONFIG_DIR = Path(user_config_dir("developer"))
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history"

AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
]
DEFAULT_MODEL = "gemini-2.5-flash"

console = Console()


@dataclass
class RuntimeState:
    config: dict[str, Any]
    client: Any
    chat: Any
    plan_chat: Any
    current_model: str = DEFAULT_MODEL
    current_mode: str = "chat"
    plan_state: PlanState = field(default_factory=reset_plan)


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_api_key(config: dict[str, Any]) -> str | None:
    return config.get("api_key")


def print_header(model: str, mode: str) -> None:
    console.print()
    console.print("[bold cyan]DEVELOPER[/bold cyan] [dim]- AI Coding Assistant[/dim]")
    console.print(f"[dim]Model: {model} | Mode: {mode}[/dim]")
    console.print()


def print_help() -> None:
    console.print("[bold]Commands:[/bold]")
    console.print("  [cyan]/quit[/cyan] or [cyan]/q[/cyan]   Exit")
    console.print("  [cyan]/model[/cyan]          Switch model")
    console.print("  [cyan]/key[/cyan]            Update API key")
    console.print("  [cyan]/clear[/cyan]          Clear screen")
    console.print("  [cyan]/mode plan|chat[/cyan] Switch between plan and chat modes")
    console.print("  [cyan]/plan[/cyan]           Show active plan")
    console.print("  [cyan]/approve <id|all>[/cyan] Approve plan step(s)")
    console.print("  [cyan]/pick[/cyan]           Open simple approval menu")
    console.print("  [cyan]/run[/cyan]            Run approved steps")
    console.print("  [cyan]/resetplan[/cyan]      Clear current plan")
    console.print("  [cyan]/help[/cyan]           Show this help")
    console.print()


def render_streamed_markdown(text: str) -> None:
    if not text:
        return

    displayed_text = ""
    with Live(
        Markdown(displayed_text),
        console=console,
        refresh_per_second=60,
        transient=False,
    ) as live:
        for i, char in enumerate(text):
            displayed_text += char
            if i % 3 == 0 or i == len(text) - 1:
                live.update(Markdown(displayed_text))


def normalize_tool_args(
    tool_name: str, tool_args: dict[str, Any] | None
) -> dict[str, Any]:
    args = dict(tool_args or {})

    if tool_name == "list_files":
        if "directory" not in args and "path" in args:
            args["directory"] = args.pop("path")
        args.setdefault("directory", ".")
    elif tool_name == "read_file":
        if "file_path" not in args and "path" in args:
            args["file_path"] = args.pop("path")
    elif tool_name == "write_file":
        if "file_path" not in args and "path" in args:
            args["file_path"] = args.pop("path")

    return args


def execute_tool(
    tool_name: str,
    tool_args: dict[str, Any],
    available_tools: dict[str, Any],
) -> tuple[bool, str]:
    normalized_args = normalize_tool_args(tool_name, tool_args)
    args_str = json.dumps(normalized_args, indent=2, default=str)
    console.print(f"[dim]→ {tool_name}({args_str})[/dim]")

    if tool_name in ("write_file", "run_command"):
        console.print("[yellow]Allow this action? (y/n)[/yellow]", end=" ")
        answer = input().strip().lower()
        if answer != "y":
            return False, "User denied this action."

    tool_fn = available_tools.get(tool_name)
    if tool_fn is None:
        return False, f"Error: Unknown tool '{tool_name}'"

    try:
        result = tool_fn(**normalized_args)
    except Exception as e:
        result = f"Error: {e}"

    result_display = result[:500] + "..." if len(result) > 500 else result
    console.print(f"[dim]← {result_display}[/dim]")
    return not str(result).startswith("Error"), result


def create_chat_session(client: genai.Client, model: str):
    return client.chats.create(
        model=model,
        config={
            "system_instruction": SYSTEM_CHAT_PROMPT,
            "tools": [read_file, write_file, run_command, list_files],
        },
    )


def create_plan_session(client: genai.Client, model: str):
    return client.chats.create(
        model=model,
        config={"system_instruction": SYSTEM_PLAN_PROMPT},
    )


def build_client_and_sessions(api_key: str, model: str) -> tuple[Any, Any, Any]:
    client = genai.Client(api_key=api_key)
    return (
        client,
        create_chat_session(client, model),
        create_plan_session(client, model),
    )


def switch_model(config: dict[str, Any], current_model: str) -> str:
    console.print("[bold]Available models:[/bold]")
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        marker = " [cyan]← current[/cyan]" if model == current_model else ""
        console.print(f"  {i}. {model}{marker}")

    try:
        choice = console.input("\nPick a number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(AVAILABLE_MODELS):
            new_model = AVAILABLE_MODELS[int(choice) - 1]
            config["model"] = new_model
            save_config(config)
            console.print(f"[green]Switched to {new_model}[/green]\n")
            return new_model
        console.print("[red]Invalid choice[/red]\n")
    except (KeyboardInterrupt, EOFError):
        console.print("[dim]Cancelled[/dim]\n")

    return current_model


def recommended_approval_target(plan_state: PlanState) -> str:
    if not plan_state.steps:
        return "all"

    safe_tools = {"read_file", "list_files"}
    if all(step.tool in safe_tools for step in plan_state.steps):
        return "all"

    return plan_state.steps[0].id


def pick_plan_approval(plan_state: PlanState) -> str | None:
    if not plan_state.active or not plan_state.steps:
        console.print("[yellow]No active plan to pick from.[/yellow]")
        return None

    recommended = recommended_approval_target(plan_state)
    recommended_label = "all" if recommended == "all" else recommended
    console.print("[bold]Approval menu[/bold]")
    console.print(f"  1) Approve recommended ({recommended_label})")
    console.print("  2) Approve all")
    console.print("  3) Type a specific step id")
    console.print("  4) Skip for now")
    choice = console.input("Choose [1-4]: ").strip()

    if choice == "1":
        return recommended
    if choice == "2":
        return "all"
    if choice == "3":
        typed = console.input("Approve which step id (or 'all')? ").strip()
        return typed or None
    return None


def handle_chat_turn(
    state: RuntimeState, user_input: str, available_tools: dict[str, Any]
) -> None:
    response = state.chat.send_message(user_input)
    text = response.text
    func_calls = response.function_calls or []

    while func_calls:
        func_call = func_calls[0]
        _, result = execute_tool(func_call.name, func_call.args, available_tools)
        part = types.Part(
            function_response=types.FunctionResponse(
                name=func_call.name,
                response={"result": result},
            )
        )
        response = state.chat.send_message(part)
        text = response.text
        func_calls = response.function_calls or []

    render_streamed_markdown(text)
    console.print()


def handle_plan_generation(
    state: RuntimeState,
    user_input: str,
    available_tools: dict[str, Any],
) -> None:
    planner_input = f"{PLAN_JSON_SCHEMA_HINT}\n\nUser request:\n{user_input}"
    response = state.plan_chat.send_message(planner_input)
    text = response.text or ""
    state.plan_state = create_plan_from_json(text)
    validate_plan(state.plan_state, set(available_tools.keys()))

    console.print("[green]Plan created. Review and approve steps.[/green]")
    console.print(render_plan(state.plan_state))

    picked = pick_plan_approval(state.plan_state)
    if not picked:
        console.print("[dim]No steps approved. Use /pick or /approve ...[/dim]")
        return

    approved = approve_steps(state.plan_state, picked)
    console.print(f"[green]Approved:[/green] {', '.join(approved)}")
    console.print("[dim]Run /run to execute approved step(s).[/dim]")


def run_approved_steps(state: RuntimeState, available_tools: dict[str, Any]) -> None:
    runnable_steps = get_runnable_steps(state.plan_state)
    if not runnable_steps:
        console.print("[yellow]No approved pending steps to run.[/yellow]")
        return

    for step in runnable_steps:
        step.status = "running"
        ok, result = execute_tool(step.tool, step.args, available_tools)
        mark_step_result(state.plan_state, step.id, ok, result)
        if not ok:
            console.print(f"[red]Step {step.id} failed. Stopping run.[/red]")
            break

    console.print(render_plan(state.plan_state))


def handle_command(
    state: RuntimeState,
    user_input: str,
    available_tools: dict[str, Any],
) -> tuple[bool, bool]:
    """Returns (handled, should_exit)."""
    if not user_input.startswith("/"):
        return False, False

    command, _, arg = user_input.partition(" ")
    arg = arg.strip()

    if command in {"/quit", "/q"}:
        console.print("[dim]Goodbye![/dim]")
        return True, True

    if command == "/help":
        print_help()
        return True, False

    if command == "/clear":
        console.clear()
        print_header(state.current_model, state.current_mode)
        return True, False

    if command == "/key":
        new_key = console.input("Enter new API key: ").strip()
        state.config["api_key"] = new_key
        save_config(state.config)
        state.client, state.chat, state.plan_chat = build_client_and_sessions(
            new_key, state.current_model
        )
        console.print("[green]API key updated.[/green]\n")
        return True, False

    if command == "/model":
        new_model = switch_model(state.config, state.current_model)
        if new_model != state.current_model:
            state.current_model = new_model
            state.chat = create_chat_session(state.client, state.current_model)
            state.plan_chat = create_plan_session(state.client, state.current_model)
            print_header(state.current_model, state.current_mode)
        return True, False

    if command == "/mode":
        if arg not in {"plan", "chat"}:
            console.print("[red]Usage: /mode plan|chat[/red]")
            return True, False
        state.current_mode = arg
        console.print(f"[green]Switched to {arg} mode.[/green]")
        return True, False

    if command == "/plan":
        console.print(render_plan(state.plan_state))
        return True, False

    if command == "/approve":
        if not arg:
            console.print("[red]Usage: /approve <id|all>[/red]")
            return True, False
        approved = approve_steps(state.plan_state, arg)
        console.print(f"[green]Approved:[/green] {', '.join(approved)}")
        return True, False

    if command == "/pick":
        picked = pick_plan_approval(state.plan_state)
        if not picked:
            console.print("[dim]No changes made.[/dim]")
            return True, False
        approved = approve_steps(state.plan_state, picked)
        console.print(f"[green]Approved:[/green] {', '.join(approved)}")
        return True, False

    if command == "/resetplan":
        state.plan_state = reset_plan()
        console.print("[green]Plan cleared.[/green]")
        return True, False

    if command == "/run":
        run_approved_steps(state, available_tools)
        return True, False

    console.print(f"[red]Unknown command: {command}[/red]")
    return True, False


def main() -> None:
    config = load_config()
    api_key = get_api_key(config)
    current_model = config.get("model", DEFAULT_MODEL)
    if current_model not in AVAILABLE_MODELS:
        current_model = DEFAULT_MODEL

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    session = PromptSession(
        history=FileHistory(str(HISTORY_FILE)),
        multiline=False,
    )

    print_header(current_model, "chat")

    if not api_key:
        console.print(
            "[yellow]Welcome! Please enter your Google Gemini API key.[/yellow]"
        )
        console.print("Get one at: https://aistudio.google.com/apikey\n")
        api_key = console.input("API key: ").strip()
        config["api_key"] = api_key
        save_config(config)
        console.print("[green]Saved![/green]\n")

    try:
        client, chat, plan_chat = build_client_and_sessions(api_key, current_model)
    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        console.print("Run with /key to update your API key")
        return

    state = RuntimeState(
        config=config,
        client=client,
        chat=chat,
        plan_chat=plan_chat,
        current_model=current_model,
    )

    available_tools = {
        "read_file": read_file,
        "write_file": write_file,
        "run_command": run_command,
        "list_files": list_files,
    }

    print_help()

    while True:
        try:
            user_input = session.prompt(
                "> ",
                style=Style.from_dict({"prompt": "cyan bold"}),
            ).strip()
            if not user_input:
                continue

            try:
                handled, should_exit = handle_command(
                    state, user_input, available_tools
                )
                if should_exit:
                    break
                if handled:
                    continue

                if state.current_mode == "plan":
                    handle_plan_generation(state, user_input, available_tools)
                else:
                    handle_chat_turn(state, user_input, available_tools)
            except Exception as e:
                error_str = str(e)
                if "API_KEY_INVALID" in error_str:
                    console.print("[red]Invalid API key. Use /key to update.[/red]\n")
                else:
                    console.print(f"[red]Error: {e}[/red]\n")

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break


if __name__ == "__main__":
    main()
