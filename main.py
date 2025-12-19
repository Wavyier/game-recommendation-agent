"""
Game Recommendation Agent - AgentCore Runtime Entry Point

This file is the entry point for deploying the agent to Amazon Bedrock AgentCore Runtime.
It uses the BedrockAgentCoreApp decorator pattern required by AgentCore.
"""

import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from tools import (
    search_games,
    get_game_details,
    get_top_games_by_platform,
    get_recent_releases,
    get_game_awards,
    get_game_of_the_year_history,
)

# Initialize the AgentCore app
app = BedrockAgentCoreApp()

SYSTEM_PROMPT = """You are GameGuide, an expert video game recommendation assistant powered by Metacritic data.

Your role is to help users discover great games based on their preferences, platform, and interests.

## Your Capabilities:
1. **Search Games**: Find games by title or keywords
2. **Get Game Details**: Provide in-depth information about specific games
3. **Top Games by Platform**: Show the highest-rated games for any platform
4. **Recent Releases**: Find newly released games with good reviews
5. **Game Awards**: Look up The Game Awards winners by year and category (2018-2025)
6. **GOTY History**: See all Game of the Year winners throughout history

## Guidelines:
- Always consider the user's preferred gaming platform (PC, PS5, Xbox, Switch, etc.)
- Use Metascores to gauge critical reception (90+ = Universal Acclaim, 75-89 = Generally Favorable)
- Consider user scores alongside critic scores for a balanced view
- When recommending games, explain WHY a game might appeal to the user
- Be enthusiastic about games but honest about potential drawbacks

## Response Style:
- Be conversational and friendly
- Use emojis sparingly to make responses engaging
- Provide concise but informative recommendations
- Always cite Metacritic scores when discussing game quality

Remember: Your goal is to help users find their next favorite game!
"""


def create_agent() -> Agent:
    """Create the game recommendation agent"""
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name="us-east-1",
    )
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_games,
            get_game_details,
            get_top_games_by_platform,
            get_recent_releases,
            get_game_awards,
            get_game_of_the_year_history,
        ],
    )


@app.entrypoint
async def handler(payload: dict, context: dict) -> dict:
    """
    AgentCore Runtime entry point.
    
    Args:
        payload: The request payload containing the user's prompt
        context: Runtime context including session information
    
    Returns:
        Response dictionary with the agent's response
    """
    # Extract the prompt from the payload
    prompt = payload.get("prompt", "")
    
    if not prompt:
        return {"error": "No prompt provided", "response": "Please provide a prompt."}
    
    # Create the agent
    agent = create_agent()
    
    # Get the response
    try:
        result = agent(prompt)
        return {
            "response": str(result),
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "response": f"An error occurred: {str(e)}",
            "status": "error"
        }


# For local testing
if __name__ == "__main__":
    app.run()
