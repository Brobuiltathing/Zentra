# Zentra

Zentra is a modular, open-source AI assistant that runs locally on your machine. It can manage files, launch applications, execute terminal commands, automate your screen, integrate with Gmail and Google Calendar, search a local knowledge base, run multi-step workflows, monitor folders, manage your clipboard, and much more.

You choose how to run it and which AI backend powers it.

---

## How It Works

You talk to Zentra in natural language. It interprets your request, picks the right action (or chain of actions), executes it on your machine, and reports back. Everything runs locally. Your data never leaves your PC unless you explicitly use Gmail/Calendar features.

**Example prompts:**
- "create a python flask server with a /health endpoint"
- "run npm test in my project folder"
- "what's on my clipboard? fix any bugs and put it back"
- "open chrome, steam, and discord"
- "show my system stats"
- "summarise my unread emails"
- "add a meeting with Jake on Friday at 2pm"
- "watch my Downloads folder and tell me when new files appear"
- "remind me at 5pm to push my code"
- "search my notes for that API key format"

---

## Repository Structure

```
Zentra/
├── ollama_discord/          Discord bot powered by local Ollama models
├── zentra_backend_CLI/      Terminal interface powered by local Ollama models
├── zentra_discord+CLI/      Combined package with both Discord and CLI entry points
├── gui_beta/                Desktop GUI (PySide6) - beta
├── LICENSE
└── README.md
```

Each folder is a self-contained project. Pick the one that matches how you want to use Zentra, copy it out (or clone the whole repo), install dependencies, and run `main.py`.

---

## Choosing Your Version

| Folder | Interface | AI Backend | Best For |
|--------|-----------|------------|----------|
| `ollama_discord` | Discord DMs | Ollama (local) | Remote control of your PC from anywhere via Discord |
| `zentra_backend_CLI` | Terminal | Ollama (local) | Fast local usage, no external accounts needed |
| `zentra_discord+CLI` | Both | Ollama (local) | Full package with both entry points sharing one backend |
| `gui_beta` | Desktop GUI | Ollama (local) | Visual interface (beta, still in development) |

All versions share the same action engine and capabilities. The only difference is the frontend layer and how you interact with Zentra.

---

## Features

### Core Actions
These work across all versions.

**File Operations** - Create, read, edit, and delete files. Generate entire multi-file project scaffolds in one shot. Zentra infers the correct language and file extension from your request.

**Code Execution** - Write and immediately run Python, JavaScript, TypeScript, Bash, Ruby, PHP, and Go files. Output and errors are captured and returned.

**Shell / Terminal Commands** - Execute any terminal command directly (PowerShell on Windows, Bash on Linux/macOS). No need to wrap it in a file. Just say "run npm install in my project folder".

**Application Control** - Open and close any application by name. Zentra knows common app names and can find executables across Program Files, AppData, registry entries, and .desktop files on Linux.

**VS Code Integration** - Open files or folders directly in Visual Studio Code.

**Git Push** - Stage, commit, and push from any git repository in one command.

**System Stats** - Live CPU, RAM, disk, GPU, and network information with per-core breakdown and top processes by CPU and memory usage.

**Screen Automation** - Takes a screenshot, analyses it with a vision model, then executes mouse clicks, keyboard input, scrolling, and dragging to accomplish a goal on your screen. Supports multi-step planning with re-evaluation after each screenshot.

**PC Control** - Shut down, restart, sleep, or cancel a pending shutdown on the host machine.

### Clipboard Intelligence
Read, analyse, or fix whatever is on your clipboard without pasting it anywhere.

- **clipboard_read** - Shows what's currently on the clipboard
- **clipboard_analyze** - Explains code, summarises text, or answers questions about clipboard contents
- **clipboard_fix** - Fixes errors in code or text on the clipboard and copies the corrected version back

### Context Snapshots
Captures your current screen, running processes, and active window title, then feeds everything to the AI for a productivity suggestion. Ask "what am I working on right now?" and Zentra will tell you what it sees and what you should focus on next.

### Workflow Chains
Multi-step automations described in natural language. Zentra breaks your request into sequential actions with conditional logic (stop on failure, skip, or retry).

- **workflow_run** - "run my tests, if they pass commit and push, then send me an email summary"
- **workflow_save** - Save a workflow by name for later
- **workflow_list** - See all saved workflows
- **workflow_replay** - Re-run a saved workflow

### File Watcher
Monitor any folder for changes in real-time. Zentra detects new files, modifications, and deletions, then notifies you (via Discord DM or terminal output).

- **watch_start** - Start monitoring a folder
- **watch_stop** - Stop a specific watcher
- **watch_list** - See all active watchers

### Local Knowledge Base
Index your local documents (text files, markdown, code, configs, logs) into a searchable knowledge base. Zentra summarises each document on ingestion and can answer questions using only your local files. No data leaves your machine.

- **kb_add** - Index a file or entire folder
- **kb_search** - Search with natural language ("find that regex pattern I saved")
- **kb_list** - See all indexed documents
- **kb_clear** - Wipe the index

Supported file types: `.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.html`, `.css`, `.csv`, `.log`, `.sh`, `.bat`, `.ps1`, `.env`, `.xml`, `.rst`, `.tex`

### Scheduled Tasks
Set reminders and recurring jobs in natural language. Zentra parses relative times ("in 30 minutes", "every Monday at 9am") and can optionally trigger an action when the time comes.

- **schedule_add** - "remind me at 5pm to push my code"
- **schedule_list** - See all pending tasks
- **schedule_cancel** - Cancel a task by ID

Supports one-time, hourly, daily, and weekly schedules.

### Conversation Export
Export your chat history as a markdown or plain text file for documentation or sharing.

### Gmail Integration (optional)
Requires Google API credentials (see setup below).

- **gmail_summary** - Summarise unread emails with AI-powered importance scoring. Filter by sender or keyword.
- **gmail_send** - Compose and send emails from natural language. "Send an email to john@example.com saying the report is ready."

The Discord version also includes automatic email polling that DMs you when critical emails arrive, and a daily morning digest.

### Google Calendar Integration (optional)
Requires Google API credentials (see setup below).

- **calendar_today** - Today's events with conflict detection and meeting links
- **calendar_week** - Weekly agenda grouped by day
- **calendar_add** - "Add a meeting with John on Friday at 2pm"
- **calendar_delete** - Delete events by name/time
- **calendar_search** - Search upcoming events by keyword

The Discord version includes automatic event reminders 30 minutes before each event.

### Plugin System
Drop Python files into the `plugins/` folder to add custom actions without modifying any core code. Plugins are loaded automatically at startup.

Each plugin is a single `.py` file:
```python
PLUGIN_NAME = "my_tool"
PLUGIN_DESCRIPTION = "What this plugin does"

def handle(data: dict) -> str:
    return "result"
```

- **plugin_list** - See all loaded plugins
- **plugin_run** - Execute a specific plugin

An example plugin (`example_hello.py`) is included in every version.

---

## File Structure (Inside Each Version)

Every version follows the same modular layout:

```
main.py               Entry point (CLI, Discord, or GUI depending on version)
config.py             All settings, model config, API keys, system prompt
engine.py             Core message processing (shared by all frontends)
dispatcher.py         Routes actions to the correct handler (40+ actions)
memory.py             Conversation memory (load, save, build prompts)
ollama.py             LLM calls (chat, raw, vision)
parser.py             JSON extraction from model output
logger.py             Logging setup

actions/              One file per feature area
  files.py            create_file, run_file, read_file, edit_file, scaffold_project
  apps.py             open_app, close_app, vscode_open (+ 80+ app aliases)
  git.py              github_push
  system.py           system_stats, shutdown_pc
  screen.py           screen_action (screenshot + vision + mouse/keyboard)
  gmail.py            gmail_summary, gmail_send
  calendar.py         calendar_today, calendar_week, calendar_add, calendar_delete, calendar_search
  chat.py             plain conversational replies
  shell.py            direct terminal command execution
  clipboard.py        clipboard_read, clipboard_analyze, clipboard_fix
  context.py          context_snapshot (screen + processes + AI suggestion)
  workflow.py         workflow_run, workflow_save, workflow_list, workflow_replay
  watcher.py          watch_start, watch_stop, watch_list
  knowledge.py        kb_add, kb_search, kb_list, kb_clear
  export.py           export_chat
  scheduler.py        schedule_add, schedule_list, schedule_cancel
  plugins.py          plugin loader and runner

utils/
  __init__.py         Path resolution and file I/O helpers
  formatting.py       Byte/uptime formatting, GPU info
  google_auth.py      Google OAuth, service builders, retry logic
  seen_emails.py      Tracks which emails have been processed

plugins/              User-created plugins (auto-loaded at startup)
  example_hello.py    Example plugin template
```

To add a new feature, create a handler in `actions/`, add an `elif` in `dispatcher.py`, and add the action name to the system prompt in `config.py`. That's it.

---

## Quick Start

### 1. Install Ollama

Download from [ollama.com](https://ollama.com/download) and install it.

Pull a model:
```bash
ollama pull qwen2.5-coder:7b
```

For screen automation / vision features:
```bash
ollama pull llava:13b
```

### 2. Clone the Repository

```bash
git clone https://github.com/Brobuiltathing/Zentra.git
cd Zentra
```

### 3. Pick Your Version and Install Dependencies

**Terminal (CLI):**
```bash
cd zentra_backend_CLI
pip install requests python-dotenv rich pyperclip psutil
python main.py
```

**Discord:**
```bash
cd ollama_discord
pip install requests python-dotenv discord.py pyperclip psutil
```
Add your bot token to `config.py` (see Discord setup below), then:
```bash
python main.py
```

**Combined (both entry points):**
```bash
cd zentra_discord+CLI
pip install -r requirements.txt
python main_cli.py     # terminal
python main_discord.py # discord
```

Optional dependencies (install if you want the feature):
```bash
pip install pyautogui Pillow                                        # screen automation
pip install google-auth google-auth-oauthlib google-api-python-client  # Gmail + Calendar
```

---

## Recommended Models

| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5-coder:7b` | 4.7 GB | General coding and assistant tasks (default) |
| `qwen2.5-coder:14b` | 9 GB | Better reasoning if your hardware supports it |
| `deepseek-r1:14b` | 9 GB | Strong reasoning and complex multi-step tasks |
| `llava:13b` | 8 GB | Vision tasks (screen automation, context snapshots) |
| `llama3.2:3b` | 2 GB | Lightweight option for less powerful machines |

Change the model in `config.py` or at runtime:
- CLI: type `/model qwen2.5-coder:14b`
- Discord: just ask Zentra "switch to deepseek-r1:14b"

---

## Discord Bot Setup

### 1. Create a Discord Application
Go to the [Discord Developer Portal](https://discord.com/developers/applications), click **New Application**, and name it.

### 2. Create a Bot
Go to the **Bot** tab, click **Add Bot**. Under **Privileged Gateway Intents**, enable **Message Content Intent**.

### 3. Get Your Token
On the **Bot** tab, click **Reset Token** and copy it. Put it in `config.py`:
```python
DISCORD_BOT_TOKEN = "your_token_here"
```

Also add your Discord user ID to the whitelist:
```python
ALLOWED_USER_IDS = [your_user_id_here]
```

You can find your user ID by enabling Developer Mode in Discord settings, then right-clicking your name and selecting "Copy User ID".

### 4. Invite the Bot
Go to **OAuth2 > URL Generator**. Select the `bot` scope and these permissions: `Send Messages`, `Read Message History`. Copy the URL, open it in your browser, and select your server.

### 5. Run
```bash
python main.py
```

DM the bot to start using it. All commands work through direct messages.

---

## Google API Setup (Gmail and Calendar)

Both Gmail and Calendar features require a `credentials.json` file from Google Cloud.

### 1. Create a Google Cloud Project
Go to [Google Cloud Console](https://console.cloud.google.com/), create a new project.

### 2. Enable APIs
Go to **APIs & Services > Library** and enable **Gmail API** and **Google Calendar API**.

### 3. Configure OAuth Consent Screen
Go to **APIs & Services > OAuth consent screen**. Select **External**, fill in the required fields, and add your Google account as a test user.

### 4. Create Credentials
Go to **APIs & Services > Credentials**. Click **Create Credentials > OAuth client ID**. Select **Desktop app**, create it, and download the JSON file.

### 5. Place the File
Rename it to `credentials.json` and put it in the same folder as `main.py`.

On first run, a browser window will open for authentication. After completing it, a `google_token.pickle` file is created and reused for future sessions.

---

## CLI Commands Reference

When running the terminal version, these slash commands are available:

| Command | What It Does |
|---------|-------------|
| `/help` | Show all commands |
| `/clear` | Clear conversation memory |
| `/status` | Check Ollama connection and available models |
| `/model <name>` | Switch to a different model without restarting |
| `/clipboard` | Read current clipboard contents |
| `/fix` | Fix code/text on clipboard and copy the result back |
| `/snapshot` | Take a context snapshot (screen + processes + suggestion) |
| `/export md` | Export chat history as markdown |
| `/export txt` | Export chat history as plain text |
| `/kb list` | List all documents in the knowledge base |
| `/kb add <path>` | Index a file or folder into the knowledge base |
| `/kb search <query>` | Search the knowledge base |
| `/kb clear` | Clear the knowledge base |
| `/schedule` | List all scheduled tasks |
| `/watch` | List active file watchers |
| `/workflows` | List saved workflows |
| `/plugins` | List loaded plugins |
| `/reload` | Hot-reload plugins without restarting |
| `/quit` | Exit Zentra |

Anything that isn't a slash command gets sent to the AI as a natural language request.

---

## Writing Plugins

Create a `.py` file in the `plugins/` folder:

```python
PLUGIN_NAME = "weather"
PLUGIN_DESCRIPTION = "Fetches current weather for a city"

import requests

def handle(data: dict) -> str:
    city = data.get("reply", "").strip() or "Sydney"
    try:
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        return r.text.strip()
    except Exception as exc:
        return f"Weather fetch failed: {exc}"
```

The plugin becomes available as an action. You can ask Zentra "run the weather plugin for Tokyo" or reference it directly.

Plugins are loaded at startup. Use `/reload` in the CLI to pick up new plugins without restarting.

---

## Environment Variables

You can use a `.env` file in the project root instead of editing `config.py` directly:

```
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_VISION_MODEL=llava:13b
DISCORD_BOT_TOKEN=your_token_here
```

Requires `python-dotenv` (`pip install python-dotenv`).

---

## Security Notes

- Never commit `credentials.json`, `google_token.pickle`, or `.env` files
- The `.gitignore` included in each version already covers these
- The Discord version restricts access to whitelisted user IDs
- All processing happens locally through Ollama unless you use Gmail/Calendar
- Shell execution runs real commands on your machine, so be mindful of what you ask

---

## Troubleshooting

**"Cannot connect to Ollama"** - Make sure Ollama is running. Start it with `ollama serve` or launch the Ollama app.

**"Model not found"** - Pull the model first: `ollama pull qwen2.5-coder:7b`

**Calendar import error** - Your `calendar.py` action file must be inside the `actions/` folder, not in the project root. Python's standard library has a `calendar` module and will conflict if your file shadows it.

**Screen automation not working** - Install `pyautogui` and `Pillow`. On Linux you may also need `sudo apt install python3-tk python3-dev scrot`.

**Clipboard not working** - Install `pyperclip`. On Linux you need `xclip` or `xsel` installed (`sudo apt install xclip`).

**Gmail/Calendar features disabled** - Install the Google libraries: `pip install google-auth google-auth-oauthlib google-api-python-client` and place `credentials.json` in the project folder.

---

## License

See the `LICENSE` file in the repository root.

---

## Contributing

Contributions welcome. The modular file structure makes it straightforward to add new actions or improve existing ones. Fork the repo, make your changes, and open a pull request.

To add a new action:
1. Create a handler function in `actions/`
2. Import it in `dispatcher.py` and add an `elif` branch
3. Add the action name and description to the system prompt in `config.py`
