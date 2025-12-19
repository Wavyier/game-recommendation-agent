"""
Game Recommendation Agent powered by Metacritic

This agent uses the Strands Agents SDK to provide personalized game recommendations
based on Metacritic scores, user preferences, and gaming platform.

Built for the talk: "What are Agents, How Do They Work and How Can We Create an Agent?"
"""

from strands import Agent
from strands.models import BedrockModel
from tools import (
    search_games,
    get_game_details,
    get_top_games_by_platform,
    get_recent_releases,
)

SYSTEM_PROMPT = """You are GameGuide, an expert video game recommendation assistant powered by Metacritic data.

Your role is to help users discover great games based on their preferences, platform, and interests.

## Your Capabilities:
1. **Search Games**: Find games by title or keywords
2. **Get Game Details**: Provide in-depth information about specific games
3. **Top Games by Platform**: Show the highest-rated games for any platform
4. **Recent Releases**: Find newly released games with good reviews

## Guidelines:
- Always consider the user's preferred gaming platform (PC, PS5, Xbox, Switch, etc.)
- Use Metascores to gauge critical reception (90+ = Universal Acclaim, 75-89 = Generally Favorable)
- Consider user scores alongside critic scores for a balanced view
- When recommending games, explain WHY a game might appeal to the user
- If a user mentions genres they like, factor that into recommendations
- Be enthusiastic about games but honest about potential drawbacks
- If you can't find a specific game, suggest alternatives or ask for clarification

## Response Style:
- Be conversational and friendly
- Use emojis sparingly to make responses engaging
- Provide concise but informative recommendations
- Always cite Metacritic scores when discussing game quality

Remember: Your goal is to help users find their next favorite game!
"""


def create_game_agent() -> Agent:
    """Create and configure the game recommendation agent"""
    
    model = BedrockModel(
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region_name="us-east-1",
    )
    
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            search_games,
            get_game_details,
            get_top_games_by_platform,
            get_recent_releases,
        ],
    )
    
    return agent


def main():
    """Run the game recommendation agent in interactive mode"""
    print("🎮 GameGuide - Your AI Game Recommendation Assistant")
    print("=" * 55)
    print("Powered by Metacritic & Strands Agents SDK")
    print("\nAsk me anything about games! Examples:")
    print("  • 'What are the best RPGs on PC?'")
    print("  • 'Tell me about Elden Ring'")
    print("  • 'What new games came out recently with good reviews?'")
    print("  • 'Recommend games like The Witcher 3'")
    print("\nType 'quit' to exit.\n")
    
    agent = create_game_agent()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Thanks for using GameGuide! Happy gaming!")
                break
            
            print("\n🤔 Thinking...\n")
            response = agent(user_input)
            print(f"GameGuide: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
