# PRTS_Terminal

[![Tests](https://github.com/adamepaolo/PRTS_Terminal/actions/workflows/tests.yml/badge.svg)](https://github.com/adamepaolo/PRTS_Terminal/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A terminal AI assistant styled after **PRTS**, the Origin OS AI from
*Arknights*. Boot animation, typewriter text, a calm-and-clinical
"Doctor"-addressing persona, three swappable LLM backends, and a
tool-registry architecture that gates local file access behind explicit
human confirmation.

> Solo project, actively in development — built as a personal exercise in
> prompt engineering, multi-provider LLM integration, and building an
> AI assistant with real (but safely gated) local capabilities.

- **Google Gemini** — free-tier API key
- **Mistral AI** — free-tier API key
- **Ollama** — fully local, no key, no internet needed after the model is pulled

> **Fan project disclaimer:** This is an unofficial, non-commercial fan
> project inspired by *Arknights* (developed by Hypergryph, published by
> Yostar/Gryphline). It is not affiliated with or endorsed by them. All
> Arknights names, characters, and lore referenced here belong to their
> respective owners.

## Status

**Working:**
- Multi-backend chat (Gemini, Mistral, Ollama) behind one shared interface
- PRTS boot sequence and persona
- Local folder tool: list / read / write / append / delete, with
  confirmation gating on every modifying action
- Automatic grounding against real folder contents, so the model can't
  invent file names or content it never actually saw — this closes a real
  reliability gap in smaller/local models that don't always follow an
  explicit tool-call protocol correctly
- Persistent conversation history across sessions
- 47 passing unit tests, including dedicated path-traversal attack tests
- CI (GitHub Actions) running the suite on Python 3.10–3.12 on every push

**Known limitations:**
- Markdown from the model (`**bold**`, `* bullets`) prints as raw
  characters instead of rendering — cosmetic, on the roadmap
- Smaller local models (e.g. `llama3`) can still be inconsistent about the
  tool-call protocol for anything the automatic context doesn't already
  cover
- No streaming yet — replies are simulated with a typewriter effect after
  the full response arrives
- Only one tool (folder access) exists today; the architecture is built to
  add more without touching the core chat loop (see Architecture below)

## Screenshots

_N/A_

## Requirements

- Python 3.10+
- An API key for Gemini and/or Mistral, **or** [Ollama](https://ollama.com) installed locally

## 1. Setup

```bash
git clone https://github.com/adamepaolo/PRTS_Terminal.git
cd PRTS_Terminal

python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

This installs PRTS as an editable package (so code changes take effect
immediately) plus the dev dependencies needed to run the test suite.

## 2. Configure a backend

Pick **one or more** — you only need keys for the backends you'll actually use.

### Option A: Gemini
```bash
export GEMINI_API_KEY="your-key-here"
prts --backend gemini
```
Get a free key at https://aistudio.google.com/apikey

### Option B: Mistral
```bash
export MISTRAL_API_KEY="your-key-here"
prts --backend mistral
```
Get a free key at https://console.mistral.ai/

### Option C: Ollama (fully offline)
```bash
# install ollama (see https://ollama.com/download)
curl -fsSL https://ollama.com/install.sh | sh

ollama serve &            # start the local server
ollama pull llama3        # or any model you prefer (mistral, phi3, qwen2...)

prts --backend ollama --model llama3
```

You can also copy `.env.example` to `.env` and fill in your keys there
instead of `export`-ing them.

## 3. Chat

```
Doctor > who are you
PRTS   > I am PRTS, Origin OS of Rhodes Island...
```

Commands during chat:
- `exit`, `quit`, or `:q` — end the session
- `clear` — wipe conversation history (starts a fresh context)

Flags:
- `--backend {gemini,mistral,ollama}` — required choice of AI backend
- `--model NAME` — override the default model for that backend
- `--no-boot` — skip the boot animation (useful for quick iteration)
- `--no-typewriter` — print full replies instantly instead of char-by-char
- `--folder PATH` — grant PRTS access to exactly one local folder
- `--history-file PATH` — persist conversation history across sessions

## Giving PRTS access to a folder

```bash
prts --backend ollama --folder ~/Documents/rhodes_island_notes
```

With `--folder` set, PRTS can list, read, write, append to, and delete
files in that one folder. It cannot access anything outside it — subfolders,
parent directories, and absolute paths outside it are all blocked, and
every check happens in Python before any file is touched, never just
trusted from the model's own output (see `tests/test_path_traversal.py`).

**Every write, append, or delete asks for your confirmation in the
terminal first** — PRTS cannot modify or delete anything without you
explicitly typing `y`.

## Persisting conversation history

```bash
prts --backend ollama --history-file ~/.prts_history.json
```

The full conversation is saved to that JSON file after every turn and
reloaded automatically next time you run PRTS with the same flag. `clear`
mid-chat wipes both the in-memory and saved history.

## Running the tests

```bash
pytest -v
```

47 tests cover folder operations, path-traversal attacks, tool-call
parsing (including tolerance for local-model narration around the actual
command), the auto-grounding context injection, history persistence, and
the tool registry. CI runs this suite automatically on every push across
Python 3.10, 3.11, and 3.12.

## Architecture

```
src/prts/
├── cli.py            # argument parsing + the main chat loop
├── persona.py         # PRTS system prompt
├── ui.py               # terminal colors, boot sequence, typewriter effect
├── history.py         # conversation persistence (JSON)
├── backends/           # one module per LLM provider, same call() interface
│   ├── gemini.py
│   ├── mistral.py
│   └── ollama.py
└── tools/               # capabilities PRTS can use, beyond plain chat
    ├── base.py         # BaseTool interface every tool implements
    ├── registry.py     # aggregates active tools for one session
    └── folder.py       # the folder access tool
```

**Why a tool registry instead of hardcoding folder logic into the chat
loop:** the chat loop only knows about `BaseTool` — it parses a reply by
asking the registry "does any active tool claim this?", asks the matched
tool whether the action needs confirmation, and executes it. Adding a new
capability (web search, a calendar, shell commands) means writing a new
`BaseTool` subclass with `parse()`/`execute()`/`auto_context()` and
registering it in `cli.py` — the loop itself never changes.

**Why a text-based tool protocol (`TOOL:READ_FILE:<name>`) instead of each
provider's native function-calling API:** it works identically across
Gemini, Mistral, and Ollama without three separate schema implementations,
which matters when the whole point is being backend-agnostic.

**Why auto-grounding instead of just trusting the model to call the tool
correctly:** in practice, `llama3` sometimes narrated "I checked the
folder" without ever emitting the actual `TOOL:` command, then invented
plausible-sounding file names and content. Rather than relying purely on
protocol compliance, `FolderTool.auto_context()` proactively injects the
real folder listing and the real content of any file mentioned by name,
every turn — regardless of whether the model uses the protocol at all.
This turned out to be the actual fix; better prompting alone wasn't enough.

**Why confirmation-gating on writes/deletes:** an LLM can be prompted or
confused into proposing a destructive action it wasn't actually asked for.
Making every write/append/delete stop for an explicit `y` in the terminal
means the human is always the final check on anything irreversible.

## Customizing the persona

The system prompt lives in `src/prts/persona.py` — edit it directly to
adjust PRTS's tone, verbosity, or lore-flavor.

## Roadmap / ideas

- Render markdown (bold, bullets) into proper ANSI formatting instead of
  showing raw `**`/`*`
- Recursive folder browsing
- Real streaming responses instead of a simulated typewriter effect
- Additional tools (web search, shell exec) built on the existing registry
- Retrieval over large folders instead of dumping whole files into context

Contributions and forks welcome — feel free to open an issue or PR.

## License

[Apache License 2.0](LICENSE) — free to use, modify, and distribute, with
attribution and no warranty.
