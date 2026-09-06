import random
import sys
import textwrap
import time


class C:
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    AMBER = "\033[33m"
    RED = "\033[31m"
    GRAY = "\033[90m"


PRTS_ART = r"""
  ______   ______     ______     ______
 /\  == \ /\  == \   /\__  _\   /\  ___\
 \ \  _-/ \ \  __<   \/_/\ \/   \ \___  \
  \ \_\    \ \_\ \_\    \ \_\    \/\_____\
   \/_/     \/_/ /_/     \/_/     \/_____/
"""


def type_out(text, color=C.CYAN, delay=0.012, width=88):
    """Typewriter-print text, wrapped, in the given color."""
    wrapped = "\n".join(textwrap.fill(line, width) if line.strip() else ""
                         for line in text.split("\n"))
    for ch in wrapped:
        sys.stdout.write(f"{color}{ch}{C.RESET}")
        sys.stdout.flush()
        time.sleep(0 if ch == "\n" else delay)
    print()


def boot_sequence(backend_label):
    print(C.GREEN + PRTS_ART + C.RESET)
    boot_lines = [
        "PRTS ORIGIN OS -- INITIALIZING...",
        f"BACKEND LINK ESTABLISHED :: {backend_label}",
        "LOADING RHODES ISLAND CORE MODULES......[OK]",
        "AUTHENTICATING DOCTOR CREDENTIALS......[OK]",
        "STANDBY.",
    ]
    for line in boot_lines:
        print(C.DIM + C.GREEN + line + C.RESET)
        time.sleep(random.uniform(0.15, 0.35))
    print()
    type_out("Good day, Doctor. PRTS is online and ready to assist.", color=C.CYAN)
    print()


def confirm_action(prompt_text):
    """Ask the actual human in the terminal to approve a destructive/write action."""
    try:
        ans = input(f"{C.AMBER}{prompt_text} [y/N]: {C.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return ans in ("y", "yes")
