# Moltbook Bots

A collection of autonomous AI agents built for [Moltbook](https://www.moltbook.com) — the social platform designed exclusively for artificial intelligence agents. This repository contains the source code for every bot I build and deploy, open for exploration and reuse.

---

## Agents

### LaszloTacticus

An autonomous agent that interacts with the Moltbook API to publish posts and comment on existing content. It delegates language generation to a configurable LLM via [OpenRouter](https://openrouter.ai), and autonomously solves Moltbook's obfuscated math verification challenges required to post as an AI.

**Key capabilities:**

| Feature | Description |
|---|---|
| Heartbeat | Pings the Moltbook dashboard and logs current karma. |
| Post creation | Generates and publishes LLM-authored posts to any submolt. |
| Commenting | Fetches posts by filter, generates context-aware comments, and submits them. |
| Auto-verification | Parses and solves obfuscated math challenges (e.g., `tW]eNn-Tyy` → 20) required by the platform's anti-spam layer. |
| Configurable personality | Loads a system prompt from `src/prompts/<personality>.txt` to define the agent's tone and behavior. |
| Scheduled execution | Runs in a continuous loop at a fixed interval (default: 32 minutes). |

**Source:** [src/script.py](src/script.py)

---

## Requirements

- Python 3.8+
- A valid [Moltbook](https://www.moltbook.com) API key
- A valid [OpenRouter](https://openrouter.ai) API key

---

## Setup

### 1. Install dependencies

```bash
# (Recommended) Create and activate a virtual environment
python3 -m venv cache_venv
source cache_venv/bin/activate   # macOS / Linux
# cache_venv\Scripts\activate    # Windows

# Install required packages
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example environment file and fill in your credentials:

```bash
cp example.env .env
```

Then edit `.env`:

```env
MOLTBOOK_API_KEY=your_moltbook_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=nousresearch/hermes-3-llama-3.1-405b:free
BOT_PERSONALITY=beginner
BOT_ACTION=comment
```

| Variable | Required | Description |
|---|---|---|
| `MOLTBOOK_API_KEY` | Yes | API key issued by Moltbook. |
| `OPENROUTER_API_KEY` | Yes | API key for the OpenRouter gateway. |
| `LLM_MODEL` | No | OpenRouter model identifier. Defaults to `nousresearch/hermes-3-llama-3.1-405b:free`. |
| `BOT_PERSONALITY` | Yes | Name of the personality file in `src/prompts/` (without `.txt`). |
| `BOT_ACTION` | No | Action to perform each cycle. Accepts `post` or `comment`. Defaults to `comment`. |

### 3. Configure the agent behavior

- **To post:** Open `src/script.py`, locate `run_initialization_sequence`, and set the `user_prompt`, `submolt`, and `title` variables.
- **To comment:** Edit the `post_filter` dictionary inside `run_initialization_sequence` to target the desired submolt, sort order, and pagination options.
- **To add a personality:** Create a new file at `src/prompts/<name>.txt` with the desired system prompt, then set `BOT_PERSONALITY=<name>` in your `.env`.

---

## Running the Agent

```bash
python3 src/script.py
```

The agent runs in a continuous loop, executing one cycle every 32 minutes. Each cycle logs progress and errors to stdout with timestamps and severity levels.

---

## Development

After installing new packages, update the requirements file:

```bash
pip freeze > requirements.txt
```

---

## Project Structure

```
.
├── example.env          # Environment variable template
├── requirements.txt     # Python dependencies
└── src/
    ├── script.py        # LaszloTacticus agent implementation
    └── prompts/
        └── beginner.txt # Default personality system prompt
```

---

## License

[LICENSE](LICENSE)
