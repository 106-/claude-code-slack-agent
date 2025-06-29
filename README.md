# Claude Code Slack Agent

A Slack bot that integrates with Claude Code SDK to provide AI-powered responses to user mentions and direct messages.

## Features

- 🤖 **Smart Responses**: Powered by Claude AI with customizable system prompts
- 💬 **Thread Replies**: Responds in threads to keep conversations organized
- ⚡ **Instant Feedback**: Shows "thinking" message while processing, then updates with final response
- 🔧 **Tool Support**: Can execute commands and use various tools (Bash, WebFetch, WebSearch, etc.)
- 📱 **Multi-Channel**: Supports both channel mentions and direct messages
- 🐳 **Docker Ready**: Containerized deployment with Docker support

## Slack App Setup

### 1. Create Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Enter app name and select workspace

### 2. Configure Permissions
In **"OAuth & Permissions"**, add these Bot Token Scopes:
- `app_mentions:read` - Read mentions
- `chat:write` - Send messages
- `im:read` - Read direct messages
- `im:write` - Send direct messages
- `channels:read` - Read channel info
- `groups:read` - Read private channels
- `mpim:read` - Read group DMs

### 3. Enable Socket Mode
1. Go to **"Socket Mode"** and enable it
2. Create App Token with `connections:write` scope
3. Copy the App Token (starts with `xapp-`)

### 4. Configure Events
In **"Event Subscriptions"**:
1. Enable Events
2. Add these bot events:
   - `app_mention`
   - `message.im`

### 5. Enable Direct Messages
In **"App Home"**:
1. Enable **"Messages Tab"**
2. Allow users to send messages from messages tab

### 6. Install to Workspace
1. Go to **"OAuth & Permissions"**
2. Click **"Install to Workspace"**
3. Copy the Bot Token (starts with `xoxb-`)

## Local Setup

### 1. Configuration
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your tokens:
```yaml
slack:
  bot_token: "xoxb-your-bot-token"
  app_token: "xapp-your-app-token" 
  signing_secret: "your-signing-secret"
```

### 2. Install Dependencies
```bash
poetry install --no-root
```

### 3. Run Bot
```bash
# With default log level (INFO)
make run

# With debug logging
poetry run python main.py --log-level DEBUG
```

## Docker Deployment

### Build and Run
```bash
# Build image
make build

# Run with config mount
make docker-run

# Or use Docker Compose
make docker-compose-up
```

## Usage

### In Slack Channels
```
@your_bot_name こんにちは
```
Bot will reply in a thread with Claude's response.

### Direct Messages
Send a direct message to the bot and it will respond directly.

## Configuration

Key `config.yaml` settings:

```yaml
# Bot personality and behavior
bot:
  system_prompt: "You are a helpful assistant..."
  max_turns: 2
  allowed_tools:
    - Bash(date)
    - WebFetch
    - WebSearch

# Custom messages
messages:
  processing_message: "🤔 考え中なのだ..."
  empty_message: "Please provide a message!"
  general_error: "An error occurred."
```

## Development

```bash
make lint    # Run linting
make format  # Format code
make test    # Run tests
```

## Architecture

Built with:
- **slack-bolt**: Modern Slack app framework
- **claude-code-sdk**: AI integration
- **Socket Mode**: Real-time event handling
- **asyncio**: Async Claude API calls
- **Docker**: Containerized deployment