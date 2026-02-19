# Construct Watcher Slackbot

## Overview

This is a Slack bot built for #construct hack clubbers.

## Running locally

### 1. Setup environment variables
Go to `.env` and put these in:
```zsh
DEBUG=<true|false>
# Replace with your tokens
SLACK_BOT_TOKEN=<your-bot-token>
SLACK_APP_TOKEN=<your-app-level-token>

DEFAULT_CHANNEL=<slack-channel-id>
```

### 2. Setup your local project

```zsh
# Clone this project onto your machine
git clone https://github.com/slack-samples/bolt-python-getting-started-app.git

# Change into this project
cd bolt-python-getting-started-app/

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the dependencies
pipx install uv # just install uv. skip the hassle.
```

### 3. Start servers

```zsh
# For prod:
uv run app.py

# For dev:
uv run slack run
```

Voila! and just add the bot to your channel lol.