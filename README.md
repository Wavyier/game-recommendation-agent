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
│                    └───────┬───────┘                        │
│                            │                                │
│                            ▼                                │
│                    ┌───────────────┐                        │
│                    │  Metacritic   │                        │
│                    │   (Web Data)  │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts Demonstrated

1. **Model-Driven Agents**: The LLM (Claude via Bedrock) decides when and how to use tools
2. **Tool Integration**: Custom Python functions decorated with `@tool` become agent capabilities
3. **Agentic Loop**: The SDK handles the reasoning → tool use → response cycle automatically

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
GameGuide: 🎮 Here are the top-rated RPGs on PC...

You: Tell me about Elden Ring
GameGuide: 🟢 Elden Ring - Metascore: 96/100...

You: What new games should I play on PS5?
GameGuide: 🆕 Here are recent PS5 releases with great reviews...
```

## Tools Available

| Tool                        | Description                             |
| --------------------------- | --------------------------------------- |
| `search_games`              | Search Metacritic for games by name     |
| `get_game_details`          | Get detailed info about a specific game |
| `get_top_games_by_platform` | List highest-rated games per platform   |
| `get_recent_releases`       | Find new releases with good scores      |

## AWS Services Used

- **Amazon Bedrock**: Hosts Claude model for agent reasoning
- **Strands Agents SDK**: Open-source framework for building agents

## Deploying to Production

For production deployment, consider using **Amazon Bedrock AgentCore**:

- **Runtime**: Serverless hosting with session isolation
- **Memory**: Persistent context across conversations
- **Gateway**: Convert tools to MCP-compatible endpoints
- **Observability**: Monitor agent performance

## License

MIT
