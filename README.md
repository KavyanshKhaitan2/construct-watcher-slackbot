# Construct Watcher Slackbot

## Overview

This is a Slack bot built for #construct hack clubbers.

## How do I use it?

Currently, I have two (but extensive) commands.

### /construct-time \[goal in clay\]

<table>
  <tr>
    <td>
This command lets you know how far you are from your goal! It also shows a daily required time you will have to spend CADding. (the goal field is optional, the value you put in it gets stored in the SQLite DB.)
    </td>
    <td>
<img width="791" height="787" alt="image" src="https://github.com/user-attachments/assets/bf5be92e-b8b9-44f7-93af-5b93f6fe26df" />
    </td>
  </tr>
</table>

### /construct-user-info \<slack user mention>

<table>
  <tr>
    <td>
  Just mention the user you want to find the info of.
  This bot will do the rest for you. (just make sure that that user is doing construct.)
      <br><br>
  If you dont know whom to mention, you can use @kavyansh.tech, @Shadow, @Arca, etc.
    </td>
    <td>
      <img width="776" height="515" alt="image" src="https://github.com/user-attachments/assets/8bb657e5-913f-4748-9402-7584fd052a1b" />
    </td>
  </tr>
</table>

### Note!

Incase this doesnt work and throws a DB error, please DM me (@kavyansh.). I need to run a script that updates the KV pairs for slack user ID and construct user ID.

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

### 3. Add your construct.hackclub.com cookies

1. Go to construct.hackclub.com
2. Open Network tab in the Devtools
3. Clear logs
4. Reload Page
5. Open the initial page load
6. Search for the cookie header in there and paste them into ./construct_cookie (dont add any extra stuff, no newlines, no nothing!)

### 3. Start servers

```zsh
# For prod:
uv run app.py

# For dev:
uv run slack run
```

Voila! and just add the bot to your channel lol.
