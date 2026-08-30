# PRTS_Terminal

A terminal AI assistant styled after **PRTS**, the Origin OS AI from
*Arknights*. Boot animation, typewriter text, a calm-and-clinical
"Doctor"-addressing persona, three swappable LLM backends, and controlled
local file access.

> Solo project, actively in development — built as a personal exercise in
> prompt engineering, multi-provider LLM integration, and building an
> AI assistant with real (but safely gated) local capabilities.

- **Google Gemini** — free-tier API key
- **Mistral AI** — free-tier API key
- **Ollama** — fully local, no key, no internet needed after the model is pulled

It can also be granted access to a single local folder — list, read,
write, append, and delete files — with every modifying action gated behind
a manual confirmation prompt.

> **Fan project disclaimer:** This is an unofficial, non-commercial fan
> project inspired by *Arknights* (developed by Hypergryph, published by
> Yostar/Gryphline). It is not affiliated with or endorsed by them. All
> Arknights names, characters, and lore referenced here belong to their
> respective owners.

## Status

**Working:**
- Multi-backend chat (Gemini, Mistral, Ollama)
- PRTS boot sequence and persona
- Local folder access: list / read / write / append / delete, with
  confirmation gating on modifying actions
- Automatic grounding against real folder contents (prevents the model
  from inventing files or content it never actually saw)
- Persistent conversation history across sessions

**Known limitations:**
- Markdown from the model (`**bold**`, `* bullets`) prints as raw
  characters instead of rendering — cosmetic, on the roadmap
- Smaller local models (e.g. `llama3`) can be inconsistent about following
  the tool-call protocol for anything the automatic context doesn't
  already cover
- No streaming yet — replies are simulated with a typewriter effect after
  the full response arrives

## Screenshots

_Add a terminal screenshot or two here once you've got a session you like._

## Requirements

- Python 3.10+
- An API key for Gemini and/or Mistral, **or** [Ollama](https://ollama.com) installed locally

## 1. Setup

```bash
git clone https://github.com/adamepaolo/PRTS_Terminal.git
cd PRTS_Terminal

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure a backend

Pick **one or more** — you only need keys for the backends you'll actually use.

### Option A: Gemini
```bash
export GEMINI_API_KEY="your-key-here"
python3 prts_bot.py --backend gemini
```
Get a free key at https://aistudio.google.com/apikey

### Option B: Mistral
```bash
export MISTRAL_API_KEY="your-key-here"
python3 prts_bot.py --backend mistral
```
Get a free key at https://console.mistral.ai/

### Option C: Ollama (fully offline, good for a sandboxed VM)
```bash
# install ollama (see https://ollama.com/download)
curl -fsSL https://ollama.com/install.sh | sh

ollama serve &            # start the local server
ollama pull llama3        # or any model you prefer (mistral, phi3, qwen2...)

python3 prts_bot.py --backend ollama --model llama3
```

You can also copy `.env.example` to `.env` and fill in your keys there
instead of `export`-ing them — the script loads `.env` automatically if
`python-dotenv` is installed.

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
python3 prts_bot.py --backend ollama --folder ~/Documents/rhodes_island_notes
```

With `--folder` set, PRTS can:
- **List** the folder's contents
- **Read** individual files
- **Write** (create or overwrite) a file
- **Append** to a file
- **Delete** a file

It cannot access anything outside that one folder — subfolders, parent
directories, and absolute paths outside it are all blocked, and every check
happens in Python before any file is touched (not just trusted from the
model's output).

**Every write, append, or delete asks for your confirmation in the
terminal first** — PRTS cannot modify or delete anything without you
explicitly typing `y`. This is deliberate: it's the one thing worth not
fully automating.

### Why file reads are reliable even with small local models

Rather than depending entirely on the model correctly asking to read a
file, the script automatically tells PRTS what's actually in the folder,
and includes the real contents of any file whose name is mentioned in your
message, every turn — before it even responds. So if you say "check
sui_entities.txt" or "what does the sui entities file say," it already has
the real content grounded in front of it, regardless of whether it
correctly issues a `TOOL:READ_FILE` command itself. Smaller local models
(like `llama3`) are not always reliable about following an explicit tool
protocol — this closes that gap so it can't fabricate file names or
content instead of using the real ones.

The explicit `TOOL:LIST_FILES` / `TOOL:READ_FILE` / `TOOL:WRITE_FILE` /
`TOOL:APPEND_FILE` / `TOOL:DELETE_FILE` protocol still exists underneath
for anything not already shown to it (e.g. writing a new file, or reading
one whose name wasn't mentioned).

Notes:
- Only top-level files in the folder are listed/matched; it won't recurse
  into subfolders automatically.
- Files are truncated to ~6000 characters when read, and writes are capped
  at ~20000 characters, to keep things sane.

## Persisting conversation history

```bash
python3 prts_bot.py --backend ollama --history-file ~/.prts_history.json
```

With `--history-file` set, the full conversation is saved to that JSON file
after every turn, and automatically reloaded the next time you run PRTS
with the same flag — so it remembers what you talked about last session.
Use the `clear` command mid-chat to wipe both the in-memory and saved
history and start fresh.

## Notes on running this in a VM specifically

- Gemini and Mistral need outbound internet access on 443 to their APIs —
  make sure your VM's network/firewall allows that if you go that route.
- Ollama needs enough RAM for whatever model you pull (a small model like
  `phi3` or a quantized `llama3:8b` is more VM-friendly than larger ones).
- Nothing here touches the filesystem outside its own process — it's just
  terminal I/O and outbound HTTPS requests, so it's low-risk to test in a
  disposable VM.

## Customizing the persona

The system prompt lives in `SYSTEM_PROMPT` near the top of `prts_bot.py` —
edit it directly to adjust PRTS's tone, verbosity, or lore-flavor.

## Roadmap / ideas

- Render markdown (bold, bullets) into proper ANSI formatting instead of
  showing raw `**`/`*`
- Recursive folder browsing
- Real streaming responses instead of a simulated typewriter effect

Contributions and forks welcome — feel free to open an issue or PR.

## License

[Apache License 2.0](LICENSE) — free to use, modify, and distribute, with
attribution and no warranty.
