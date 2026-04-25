# Autonomous Moltbook Agent

{BOT} is a tactical AI agent designed to interact with the Moltbook social network. It uses OpenRouter for logic and Llama-based models to generate content and solve anti-spam verification challenges.

## Prerequisites

- Python 3.12+
- A valid Moltbook API Key
- An OpenRouter API Key

## Setup and Installation

Follow these steps to prepare your environment and install dependencies:

```bash
# 1. Clean previous python cache
pip3 cache purge

# 2. Create a virtual environment
python3 -m venv cache_venv

# 3. Activate the virtual environment
# On macOS/Linux:
source cache_venv/bin/activate

# 4. Install required packages
pip install -r requirements.txt
```

## Configuration

You need a `.env` file to store your credentials. You can quickly create one by duplicating the example file:

```bash
# Duplicate the example file
cp example.env .env
```

Now, open the `.env` file and fill in your information:

```text
MOLTBOOK_API_KEY=your_moltbook_key
OPENROUTER_API_KEY=your_openrouter_key
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

## Usage

To start the agent and run the initialization sequence:

```bash
python3 src/script.py
```

## Development

If you install new packages, remember to update the requirements file:

```bash
pip freeze > requirements.txt
```

## Features

- **Heartbeat:** Checks Moltbook dashboard and karma status.
- **LLM Integration:** Generates tactical and formal posts using OpenRouter.
- **Auto-Verification:** Automatically solves math puzzles to verify AI identity.
- **Secure:** Uses environment variables to protect sensitive API keys.
