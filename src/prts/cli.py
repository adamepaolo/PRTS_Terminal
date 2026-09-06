#!/usr/bin/env python3
"""
PRTS - Terminal AI Assistant (Arknights-inspired)

Run:
    prts --backend gemini
    prts --backend mistral
    prts --backend ollama --model llama3

Config:
    Copy .env.example to .env and fill in your keys, or export them as
    real environment variables before running:

        export GEMINI_API_KEY="..."
        export MISTRAL_API_KEY="..."

    Ollama needs no key, just `ollama serve` running locally.
"""

import argparse
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()  # silently picks up a .env file in the current directory, if present
except ImportError:
    pass  # dotenv is optional -- real exported env vars work fine without it

from . import history as history_mod
from . import persona, ui
from .backends import BACKENDS, DEFAULT_MODELS
from .tools import FolderTool, ToolRegistry

MAX_TOOL_HOPS = 4  # safety cap on tool-call round-trips per user turn


def build_parser():
    parser = argparse.ArgumentParser(prog="prts", description="PRTS terminal AI chatbot")
    parser.add_argument("--backend", choices=BACKENDS.keys(), default="ollama",
                         help="Which AI backend to use (default: ollama)")
    parser.add_argument("--model", default=None,
                         help="Override the default model name for the chosen backend")
    parser.add_argument("--no-typewriter", action="store_true",
                         help="Disable the typewriter print effect")
    parser.add_argument("--no-boot", action="store_true",
                         help="Skip the boot animation")
    parser.add_argument("--folder", default=None,
                         help="Grant PRTS access to this one local folder: it can list, "
                              "read, write, append, and delete files in it (write/delete "
                              "always ask for your confirmation first)")
    parser.add_argument("--history-file", default=None,
                         help="Persist conversation history to this JSON file across "
                              "sessions (auto-saved after every turn, auto-loaded on "
                              "startup if it already exists)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    model = args.model or DEFAULT_MODELS[args.backend]
    call_backend = BACKENDS[args.backend]

    registry = ToolRegistry()
    folder_label = None
    if args.folder:
        try:
            folder_tool = FolderTool(args.folder)
        except NotADirectoryError as e:
            print(f"{ui.C.RED}[ERROR] {e}{ui.C.RESET}")
            sys.exit(1)
        registry.tools.append(folder_tool)
        folder_label = folder_tool.allowed_dir

    active_system_prompt = persona.SYSTEM_PROMPT + registry.system_prompt_addendum()

    history_file = os.path.expanduser(args.history_file) if args.history_file else None
    history = history_mod.load_history(history_file) if history_file else []

    if not args.no_boot:
        ui.boot_sequence(f"{args.backend.upper()} / {model}")
        if folder_label:
            print(f"{ui.C.DIM}{ui.C.GREEN}LOCAL FOLDER ACCESS :: {folder_label} [GRANTED]{ui.C.RESET}")
        if history_file and history:
            print(f"{ui.C.DIM}{ui.C.GREEN}SESSION RESUMED :: {len(history)} prior "
                  f"message(s) loaded from {history_file}{ui.C.RESET}")
        if folder_label or (history_file and history):
            print()
    else:
        print(f"{ui.C.GREEN}[PRTS online -- backend: {args.backend} / {model}]{ui.C.RESET}")
        if folder_label:
            print(f"{ui.C.GREEN}[folder access granted: {folder_label}]{ui.C.RESET}")
        if history_file and history:
            print(f"{ui.C.GREEN}[session resumed: {len(history)} prior message(s)]{ui.C.RESET}")

    while True:
        try:
            user_input = input(f"{ui.C.BOLD}{ui.C.AMBER}Doctor >{ui.C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            ui.type_out("Connection terminated. Rest well, Doctor.", color=ui.C.GRAY)
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", ":q"):
            ui.type_out("Ending session. PRTS standing by.", color=ui.C.GRAY)
            break
        if user_input.lower() == "clear":
            history.clear()
            if history_file:
                history_mod.save_history(history_file, history)
            print(f"{ui.C.DIM}[conversation history cleared]{ui.C.RESET}")
            continue

        history.append({"role": "user", "content": user_input})
        context = registry.auto_context(user_input)
        if context:
            history.append({"role": "user", "content": context})

        sys.stdout.write(f"{ui.C.CYAN}PRTS   >{ui.C.RESET} ")
        sys.stdout.flush()

        # Tool-call loop: PRTS may respond with a TOOL:... line instead of a
        # real answer. We execute the tool locally, feed the result back in,
        # and ask again -- capped at MAX_TOOL_HOPS to avoid a runaway loop.
        final_reply = None
        turn_failed = False
        for _hop in range(MAX_TOOL_HOPS + 1):
            try:
                reply = call_backend(history, model, active_system_prompt)
            except Exception as e:
                print(f"{ui.C.RED}[ERROR] {e}{ui.C.RESET}")
                history.pop()  # don't poison history with the failed turn
                turn_failed = True
                break

            tool, call = registry.parse(reply)
            if call is None:
                final_reply = reply
                history.append({"role": "assistant", "content": reply})
                break

            history.append({"role": "assistant", "content": reply})

            description = tool.describe_action(call)
            if tool.requires_confirmation(call):
                warn_color = ui.C.RED if call.kind == "DELETE_FILE" else ui.C.AMBER
                print(f"{warn_color}[PRTS wants to {description}]{ui.C.RESET}")
                if ui.confirm_action("Allow this action?"):
                    result_text = tool.execute(call)
                else:
                    result_text = "[The Doctor declined this action.]"
                print(f"{ui.C.DIM}{result_text}{ui.C.RESET}")
            else:
                result_text = tool.execute(call)
                print(f"{ui.C.DIM}[PRTS: {description}]{ui.C.RESET}")

            history.append({
                "role": "user",
                "content": f"TOOL_RESULT:\n{result_text}\n\n"
                           f"Continue and answer the Doctor's original request "
                           f"using this information, or issue another TOOL: call "
                           f"if you still need to.",
            })
        else:
            final_reply = "[PRTS could not resolve the request within the tool-call limit for this turn.]"

        if turn_failed:
            continue

        if history_file:
            history_mod.save_history(history_file, history)

        reply = final_reply

        if args.no_typewriter:
            print(f"{ui.C.CYAN}{reply}{ui.C.RESET}\n")
        else:
            sys.stdout.write("\r" + " " * 20 + "\r")  # clear the line, retype cleanly
            sys.stdout.write(f"{ui.C.CYAN}PRTS   >{ui.C.RESET} ")
            for ch in reply:
                sys.stdout.write(f"{ui.C.CYAN}{ch}{ui.C.RESET}")
                sys.stdout.flush()
                time.sleep(0.010)
            print("\n")


if __name__ == "__main__":
    main()
