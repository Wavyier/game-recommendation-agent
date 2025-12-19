# 🎮 Game Recommendation Agent

A game recommendation engine powered by Metacritic, built with the **Strands Agents SDK** and **Amazon Bedrock**.

> Built for the talk: _"What are Agents, How Do They Work and How Can We Create an Agent?"_

## What is This?

This project demonstrates how to build an AI agent using AWS's open-source **Strands Agents SDK**. The agent uses Metacritic data to provide personalized game recommendations based on scores, platforms, and user preferences.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Game Recommendation Agent                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   Prompt    │───▶│ Strands SDK  │───▶│ Amazon Bedrock│  │
│  │  (User Q)   │    │ Agent Loop   │    │ (Claude)      │  │
│  └─────────────┘    └──────┬───────┘    └───────────────┘  │
│                            │                                │
│                            ▼                                │
│                    ┌───────────────┐                        │
│                    │    Tools      │                        │
│                    ├───────────────┤                        │
│                    │ • search_games│                        │
│                    │ • get_details │                        │
│                    │ • top_games   │                        │
│                    │ • new_releases│                        │
│                    │ • game_awards │                        │
│                    │ • goty_history│                        │
│                    └───────┬───────┘                        │
│                            │                                │
│                            ▼                                │
│                    ┌───────────────┐                        │
│                    │  Metacritic / │                        │
│                    │  Game Awards  │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts Demonstrated

1. **Model-Driven Agents**: The LLM (Claude via Bedrock) decides when and how to use tools
2. **Tool Integration**: Custom Python functions decorated with `@tool` become agent capabilities
3. **Agentic Loop**: The SDK handles the reasoning → tool use → response cycle automatically
4. **Streaming**: Real-time response output using callback handlers or async iterators
5. **Session Management**: Conversation persistence across interactions using FileSessionManager
6. **Agent State**: Key-value storage for user preferences and context

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials (for Bedrock access)
aws configure
```

## Usage

### Interactive Mode

```bash
python agent.py
```

### Demo Mode (for presentations)

```bash
python demo.py
```

## Example Interactions

```
You: What are the best RPGs on PC?
GameGuide: 🎮 Here are the top-rated RPGs on PC...  (streams in real-time)

You: Tell me about Elden Ring
GameGuide: 🟢 Elden Ring - Metascore: 96/100...

You: I love action RPGs
GameGuide: Got it! I'll remember that preference...

You: What should I play next?
GameGuide: Based on your love of action RPGs, try...  (uses remembered preference)
```

## Tools Available

| Tool                           | Description                                              |
| ------------------------------ | -------------------------------------------------------- |
| `search_games`                 | Search Metacritic for games by name                      |
| `get_game_details`             | Get detailed info about a specific game                  |
| `get_top_games_by_platform`    | List highest-rated games per platform                    |
| `get_recent_releases`          | Find new releases with good scores                       |
| `get_game_awards`              | Get The Game Awards winners by year/category (2019-2025) |
| `get_game_of_the_year_history` | Complete GOTY winners history                            |

## AWS Services Used

- **Amazon Bedrock**: Hosts Claude model for agent reasoning
- **Strands Agents SDK**: Open-source framework for building agents

## Strands Features Used

| Feature              | Description                                   |
| -------------------- | --------------------------------------------- |
| `@tool` decorator    | Turn Python functions into agent capabilities |
| `BedrockModel`       | Connect to Claude via Amazon Bedrock          |
| `FileSessionManager` | Persist conversations to local filesystem     |
| `callback_handler`   | Stream responses in real-time                 |
| `stream_async()`     | Async iterator for streaming events           |
| `agent.state`        | Key-value storage for preferences             |
| `agent.messages`     | Access conversation history                   |

## Deploying to Production

For production deployment, use **Amazon Bedrock AgentCore**:

### Quick Deploy with Starter Toolkit

```bash
# Install the AgentCore starter toolkit
pip install bedrock-agentcore-starter-toolkit

# Test locally first
agentcore dev

# In another terminal, test the local agent
agentcore invoke --dev '{"prompt": "What won GOTY 2025?"}'

# Deploy to AgentCore Runtime
agentcore launch

# Test the deployed agent
agentcore invoke '{"prompt": "What are the best RPGs on PC?"}'
```

### Invoke Programmatically

```python
import json
import uuid
import boto3

agent_arn = "YOUR_AGENT_ARN"  # From agentcore launch output
client = boto3.client('bedrock-agentcore')

response = client.invoke_agent_runtime(
    agentRuntimeArn=agent_arn,
    runtimeSessionId=str(uuid.uuid4()),
    payload=json.dumps({"prompt": "Recommend me a game"}).encode(),
    qualifier="DEFAULT"
)

for chunk in response.get("response", []):
    print(chunk.decode('utf-8'))
```

### AgentCore Features

| Service       | What it does                                      |
| ------------- | ------------------------------------------------- |
| Runtime       | Serverless hosting, session isolation in microVMs |
| Memory        | Short-term and long-term memory with strategies   |
| Gateway       | Convert APIs to MCP-compatible tools              |
| Identity      | Auth with existing IdPs (Cognito, Okta, etc.)     |
| Observability | Tracing, debugging, and monitoring                |

## License

MIT
